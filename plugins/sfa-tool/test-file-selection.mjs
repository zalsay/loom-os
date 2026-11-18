import test from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import { apply, argumentsFor } from './index.js';

const connection = 'D1BB8BA7-82DA-49D0-ABC4-BE546E6DD236';
const paths = ['/tmp/封面 01.png', '/tmp/page 02.png'];

test('select-file forwards each local path as a separate argument without requiring a frame', () => {
  assert.deepEqual(argumentsFor({action:'select-file', paths}, connection),
    ['select-file', '--connection', connection, '--path', paths[0], '--path', paths[1]]);
});

test('select-file rejects relative or missing paths and unrelated frame inputs', () => {
  assert.throws(() => argumentsFor({action:'select-file', paths:['relative.png']}, connection), /absolute/i);
  assert.throws(() => argumentsFor({action:'select-file', paths:[]}, connection), /paths/i);
  assert.throws(() => argumentsFor({action:'select-file', paths, frame:connection}, connection), /frame/i);
  assert.throws(() => argumentsFor({action:'select-file', paths}, undefined), /connection/i);
});

test('an unused empty paths field does not block page observation', () => {
  assert.deepEqual(argumentsFor({action:'observe', paths:[]}, connection), ['observe', '--connection', connection]);
});


test('DSH sends the selection once through the existing runtime and returns the CLI receipt', async () => {
  const runtime = path.join(os.homedir(), 'sfc-file-selection-fixture');
  const history = [
    {type:'tool/call', data:{name:'sfa', callId:'prior', arguments:JSON.stringify({action:'connect', profile_id:connection})}},
    {type:'tool/result', data:{message:{toolCallId:'prior', content:[{type:'text', text:JSON.stringify({runtime, exitCode:0, data:{status:'ok', connection}})}]}}}
  ];
  const receipt = {status:'ok', filesSelected:2, sent:true, effectVerified:false};
  const calls = [];
  let tool;
  apply({
    effect: register => register(),
    tools: {register: definition => { tool = definition; }},
    sandboxPolicy: {resolve: () => ({mode:'danger-full-access'})},
    workingDirectory: {ensure: async () => '/tmp'},
    subprocess: {
      resolveExecutable: async executable => executable,
      spawn: spec => {
        calls.push(spec.argv.slice(1));
        return {done:Promise.resolve({exitCode:0, signal:null}), collected:{stdout:{readFrom:() => ({text:JSON.stringify(receipt)})}}};
      }
    }
  });
  const result = await tool.execute({action:'select-file', paths}, {
    agent:{id:'file-selection-fixture', session:{snapshotEvents:() => history}},
    signal:new AbortController().signal
  });
  assert.deepEqual(calls, [['control', '--runtime', runtime, 'select-file', '--connection', connection, '--path', paths[0], '--path', paths[1]]]);
  assert.deepEqual(result.data, receipt);
});
