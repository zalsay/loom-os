import os from 'node:os';
import path from 'node:path';
import { mkdtemp } from 'node:fs/promises';

export const name = 'loom-sfa-tool';
export const inject = ['tools', 'subprocess', 'sandboxPolicy', 'workingDirectory'];

const actions = ['profiles', 'authorize', 'launch', 'connect', 'state', 'observe', 'navigate', 'click', 'type', 'press', 'release'];
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const properties = {
  action: {type:'string', enum:actions, description:'Operation to perform.'},
  profile_id: {type:'string', description:'Profile UUID, required for launch and connect.'},
  url: {type:'string', description:'HTTP(S) URL, required for navigate and optional for launch.'},
  frame: {type:'string', description:'Frame UUID from observe, required for click, type and press. The agent decides whether the screenshot is still suitable.'},
  x: {type:'integer', description:'Screenshot pixel x coordinate for click.'},
  y: {type:'integer', description:'Screenshot pixel y coordinate for click.'},
  text: {type:'string', description:'Text for type; only enter content explicitly authorized by the user.'},
  key: {type:'string', description:'Key for press, as supported by sfa.'}
};
export function argumentsFor(a, connection) {
  if (!a || typeof a !== 'object' || Array.isArray(a) || !actions.includes(a.action)) throw new Error('Invalid action');
  const allowed = {profiles:[],authorize:[],launch:['profile_id','url'],connect:['profile_id'],state:[],observe:[],navigate:['url'],click:['frame','x','y'],type:['frame','text'],press:['frame','key'],release:[]}[a.action];
  // Some API clients serialize unused optional fields as empty strings/zero.
  // Tolerate only those inert placeholders; never pass unrelated values to sfa.
  for (const k of Object.keys(a)) {
    if (k === 'action' || allowed.includes(k)) continue;
    const placeholder = Object.hasOwn(properties, k) && (a[k] === '' || (['x','y'].includes(k) && a[k] === 0));
    if (!placeholder) throw new Error(`Unexpected parameter: ${k}`);
  }
  for (const k of allowed) if (a[k] === undefined && !(a.action === 'launch' && k === 'url')) throw new Error(`Missing parameter: ${k}`);
  if (a.action === 'profiles') return ['profile','list'];
  if (a.action === 'authorize') return ['authorize'];
  if (a.action === 'launch') {
    if (!UUID.test(a.profile_id)) throw new Error('Invalid profile UUID');
    const out=['launch',a.profile_id];
    if (a.url !== undefined && a.url !== '') { let u; try { u=new URL(a.url); } catch { throw new Error('Invalid URL'); } if (!['http:','https:'].includes(u.protocol)) throw new Error('URL must use http or https'); out.push('--url',a.url); }
    return out;
  }
  if (a.action === 'connect') { if (!UUID.test(a.profile_id)) throw new Error('Invalid profile UUID'); return ['connect','--profile',a.profile_id]; }
  // A completed release can still need daemon cleanup, without a live connection.
  if (a.action==='release' && !connection) return ['release'];
  if (!connection || !UUID.test(connection)) throw new Error('No connection owned by this session');
  const out = [a.action,'--connection',connection];
  if (a.action === 'navigate') { let u; try { u = new URL(a.url); } catch { throw new Error('Invalid URL'); } if (!['http:','https:'].includes(u.protocol)) throw new Error('URL must use http or https'); out.push('--url',a.url); }
  if (['click','type','press'].includes(a.action)) { if (!UUID.test(a.frame)) throw new Error('Invalid frame UUID'); out.push('--frame',a.frame); }
  if (a.action === 'click') { if (![a.x,a.y].every(n=>Number.isSafeInteger(n)&&n>=0&&n<=65535)) throw new Error('Invalid pixel coordinates'); out.push('--x',String(a.x),'--y',String(a.y),'--count','1'); }
  if (a.action === 'type') { if (typeof a.text !== 'string' || a.text.length > 10000) throw new Error('Invalid text'); out.push('--text-stdin'); }
  if (a.action === 'press') { if (typeof a.key !== 'string' || !/^[A-Za-z0-9+_-]{1,32}$/.test(a.key)) throw new Error('Invalid key'); out.push('--key',a.key); }
  return out;
}

function replyData(result) {
  if (result?.outputTruncated) return null;
  let data = result?.data;
  if (!data) { try { data=JSON.parse(result?.stdout ?? ''); } catch { return null; } }
  return data && typeof data==='object' && !Array.isArray(data) ? data : null;
}
function successful(result) {
  return result?.exitCode===0 && !result.signal && replyData(result)?.status==='ok';
}
function released(result) {
  const receipt=replyData(result)?.controlReleased;
  return successful(result) && ['inputReleased','artifactsCleaned','browserRetained','manualInteractionEnabled'].every(k=>receipt?.[k]===true);
}
function validRuntime(runtime) {
  return typeof runtime==='string' && path.dirname(runtime)===os.homedir() && /^sfc-[A-Za-z0-9_-]+$/.test(path.basename(runtime));
}

// Recover routing from this session's completed tool calls. Historical errors
// are evidence for the agent, not a permanent prohibition on future commands.
export function restoreControl(session, currentCallId) {
  const calls=new Map(); let state=null;
  for (const e of session?.snapshotEvents?.() ?? []) {
    if (e.type==='tool/call' && e.data?.name==='sfa' && e.data.callId!==currentCallId) {
      try { calls.set(e.data.callId,JSON.parse(e.data.arguments)); } catch { /* no routing facts */ }
    }
    if (e.type!=='tool/result') continue;
    const message=e.data?.message, call=calls.get(message?.toolCallId);
    if (!call || message.isError) continue;
    let value; try { value=JSON.parse(message.content.find(b=>b.type==='text')?.text ?? ''); } catch { continue; }
    if (!value || typeof value!=='object' || Array.isArray(value)) continue;
    if (call.action==='connect' && validRuntime(value.runtime)) {
      const data=replyData(value);
      if (successful(value) && UUID.test(data.connection ?? '')) state={runtime:value.runtime,connection:data.connection,profileID:call.profile_id};
      else if (!state) state={runtime:value.runtime,connection:null};
    }
    if (call.action==='release') {
      if (successful(value.stop)) state=null;
      else if (released(value) && validRuntime(value.runtime)) state={runtime:value.runtime,connection:null,released:true,releaseResult:value};
    }
  }
  return state;
}

export function apply(ctx) {
  const sessions = new Map();
  const running = new Set();
  async function invoke(argv, exec, cwd, stdin) {
    const exe = await ctx.subprocess.resolveExecutable(path.join(os.homedir(),'.local/bin/sfa'), undefined, exec.signal);
    const handle = ctx.subprocess.spawn({argv:[exe,...argv], cwd, stdio:{stdin:stdin === undefined ? 'ignore' : {data:stdin},stdout:{maxBytes:1048576},stderr:{maxBytes:65536}},graceMs:2000,signal:exec.signal});
    const outcome = await handle.done;
    const stdout = handle.collected.stdout?.readFrom(0); const stderr = handle.collected.stderr?.readFrom(0);
    return {exitCode:outcome.exitCode,signal:outcome.signal,stdout:stdout?.text ?? '',stderr:stderr?.text ?? '',
      ...(stdout?.lossy || stderr?.lossy ? {outputTruncated:true} : {})};
  }
  async function stopReleased(s,id,exec,cwd) {
    // Release already succeeded. Only the daemon cleanup remains to be sent.
    const {stop: previousStop, stopError: previousStopError, ...releaseResult}=s.releaseResult;
    try {
      const stop=await invoke(['control','--runtime',s.runtime,'daemon','stop'],exec,cwd);
      if (successful(stop)) sessions.delete(id);
      return {...releaseResult,runtime:s.runtime,releaseVerified:true,stop};
    } catch(error) {
      return {...releaseResult,runtime:s.runtime,releaseVerified:true,stopError:String(error?.message ?? error)};
    }
  }
  ctx.effect(() => ctx.tools.register({
    name:'sfa',
    description:'Execute authorized Safarier browser commands once. Connect before state/observe/input; use observe to inspect page effects and choose a suitable frame. Return CLI results without judging page success. An error does not block later explicit commands; never automatically repeat input. Release control when finished; never close the user browser. Only available under danger-full-access session policy.',
    parameters:{type:'object',additionalProperties:false,properties,required:['action']},
    output:{schema:{type:'object',additionalProperties:true},render:(_a,v)=>[{type:'text',text:JSON.stringify(v)}]},
    timeoutMs:120000,
    isConcurrencySafe:()=>false,
    async execute(a,exec) {
      if (!exec.agent?.session) throw new Error('An owning session is required');
      const policy=ctx.sandboxPolicy.resolve({session:exec.agent.session});
      if (policy.mode !== 'danger-full-access') throw new Error('sfa requires danger-full-access; this tool cannot request or bypass permissions');
      const id=String(exec.agent.id);
      if (running.has(id)) throw new Error('Another sfa operation is in progress');
      running.add(id);
      try {
        let s=sessions.get(id);
        if (!s) { s=restoreControl(exec.agent.session,exec.callId); if(s) sessions.set(id,s); }
        // A verified release leaves no browser connection, only daemon cleanup.
        const argv=argumentsFor(a,s?.connection);
        const cwd=await ctx.workingDirectory.ensure(exec.agent,exec.signal);
        if (a.action==='profiles' || a.action==='authorize') return await invoke(argv,exec,cwd);
        if (s?.released && a.action==='release') return await stopReleased(s,id,exec,cwd);
        if (a.action==='launch') {
          return await invoke(argv,exec,cwd);
        }
        if (a.action==='release' && s && !s.connection) {
          const stop=await invoke(['control','--runtime',s.runtime,'daemon','stop'],exec,cwd);
          if (successful(stop)) sessions.delete(id);
          return {...stop,runtime:s.runtime,stop};
        }
        // A historical connection is routing data, not proof that its daemon is alive.
        // Let the backend decide a same-profile explicit reconnect; keep the old
        // route if start/connect fails. Do not abandon another profile's owner.
        if (a.action==='connect' && (s?.released || (s?.connection && s.profileID?.toLowerCase()!==a.profile_id.toLowerCase()))) throw new Error('Release the current connection before connecting again');
        if (a.action!=='connect' && !s?.connection) throw new Error('No connection owned by this session');
        if (!s) { s={runtime:await mkdtemp(path.join(os.homedir(),'sfc-')),connection:null}; sessions.set(id,s); }
        if (a.action==='connect') {
          const start=await invoke(['control','--runtime',s.runtime,'daemon','start'],exec,cwd);
          if (!successful(start)) return {...start,runtime:s.runtime};
        }
        const result=await invoke(['control','--runtime',s.runtime,...argv],exec,cwd,a.action==='type'?a.text:undefined);
        const data=replyData(result), response={...result,...(data?{data}:{}),runtime:s.runtime};
        if (!successful(response)) return response;
        if (a.action==='connect' && UUID.test(data.connection ?? '')) { s.connection=data.connection; s.profileID=a.profile_id; }
        if (a.action==='release') {
          if (!released(response)) return {...response,releaseVerified:false};
          s.released=true; s.connection=null; s.releaseResult=response;
          return await stopReleased(s,id,exec,cwd);
        }
        return response;
      } finally { running.delete(id); }
    }
  }));
}
