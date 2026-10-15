#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import wave
from zipfile import ZipFile, ZIP_DEFLATED
import numpy as np
from workflow import load, stem, cache_matches, timestamp

RATE=48000

def command(args, **kwargs):
    return subprocess.run([str(v) for v in args], check=True, **kwargs)

def write_wav(path, pcm):
    path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1 if pcm.ndim==1 else pcm.shape[1]);w.setsampwidth(2);w.setframerate(RATE)
        w.writeframes((np.clip(pcm,-1,1)*32767).round().astype('<i2').tobytes())

def read_pcm(path):
    result=command(['ffmpeg','-v','error','-i',path,'-ac','1','-ar',RATE,'-f','s16le','-'],capture_output=True)
    return np.frombuffer(result.stdout,'<i2').astype(float)/32768

def transcript(project, cfg):
    rows=['# 织界 · '+cfg['topic'],'',f'用途：{cfg["kind"]}；时长：{cfg["duration"]:.2f}秒；版本：{cfg["revision"]}。','',
          'AI 引导，孩子思考，共同实现。','','| 时间 | 镜头 | 逐字稿 |','| --- | --- | --- |']
    for s in cfg['timeline']:
        rows.append(f'| {s["start"]:.2f}–{s["end"]:.2f}秒 | '+ ' / '.join(s['title'])+' | '+(s['narration'] or '无旁白，保留观察空间')+' |')
    (project/'逐字稿.md').write_text('\n'.join(rows)+'\n')

def node_env():
    env=os.environ.copy()
    if 'NODE_PATH' not in env and env.get('CODEX_PRIMARY_RUNTIME_NODE_MODULES'):
        env['NODE_PATH']=env['CODEX_PRIMARY_RUNTIME_NODE_MODULES']
    return env.get('CODEX_PRIMARY_RUNTIME_NODE') or shutil.which('node') or 'node', env

def align(project,cfg):
    pcm=np.zeros(round(RATE*cfg['duration']));report=[];subtitles=[];count=0
    for s in cfg['timeline']:
        if not s['narration']:continue
        assert cache_matches(project,cfg,s),f'Scene {s["id"]}: missing or stale audio; run mimo_tts.py'
        raw=project/f'narration/raw/{s["id"]:02d}.wav';sound=read_pcm(raw);original=len(sound)/RATE
        block=round(RATE*.01)
        envelope=np.array([np.sqrt(np.mean(sound[i:i+block]**2)) for i in range(0,len(sound),block)])
        active=np.flatnonzero(envelope>max(.006,envelope.max()*.035))
        assert len(active),f'Scene {s["id"]}: empty voice'
        left=max(0,active[0]*block-round(RATE*.05));right=min(len(sound),(active[-1]+1)*block+round(RATE*.09))
        sound=sound[left:right];budget=s['end']-s['start'];speed=max(1,len(sound)/RATE/(budget-.06))
        assert speed<=1.2,f'Scene {s["id"]}: shorten narration or extend scene (tempo {speed:.2f})'
        temporary=project/f'out/voice-{s["id"]:02d}-trim.wav';write_wav(temporary,sound)
        output=project/f'narration/aligned/{s["id"]:02d}.wav';output.parent.mkdir(parents=True,exist_ok=True)
        filters=f'atempo={speed:.6f},loudnorm=I=-18:TP=-3:LRA=7,afade=t=in:d=0.018,areverse,afade=t=in:d=0.025,areverse'
        command(['ffmpeg','-v','error','-y','-i',temporary,'-af',filters,'-ar',RATE,'-ac','1',output])
        temporary.unlink();sound=read_pcm(output);length=len(sound)/RATE
        assert length<=budget+.02,f'Scene {s["id"]}: voice exceeds window'
        offset=round(s['start']*RATE);pcm[offset:offset+len(sound)]+=sound
        sentences=re.findall(r'[^。！？]+[。！？]?',s['narration']);weights=[max(1,len(t)) for t in sentences];cursor=s['start']
        for text,weight in zip(sentences,weights):
            stop=cursor+length*weight/sum(weights);count+=1
            subtitles.extend([str(count),f'{timestamp(cursor)} --> {timestamp(stop)}',text,'']);cursor=stop
        item={'id':s['id'],'start':s['start'],'end':round(s['start']+length,4),'window_end':s['end'],
              'original_seconds':round(original,4),'tempo':round(speed,5),'text':s['narration']}
        report.append(item);print(json.dumps(item,ensure_ascii=False),flush=True)
    write_wav(project/'narration.wav',pcm)
    command(['ffmpeg','-v','error','-y','-i',project/'narration.wav','-c:a','libmp3lame','-b:a','192k',project/'narration.mp3'])
    (project/'narration.srt').write_text('\n'.join(subtitles))
    (project/'narration').mkdir(exist_ok=True)
    (project/'narration/alignment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (project/'narration/aligned-config.sha256').write_text(config_hash(cfg)+'\n')

def config_hash(cfg):
    return hashlib.sha256(json.dumps(cfg,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def music(project,cfg):
    n=round(RATE*cfg['duration']);score=np.zeros((n,2));rng=np.random.default_rng(37)
    chords=[[60,64,67],[57,60,64],[53,57,60],[55,59,62]]
    for beat in range(int(np.ceil(cfg['duration']/.625))):
        at=beat*.625;notes=[chords[(beat//8)%4][(beat//2)%3]+12] if beat%2==0 else []
        if beat%4==0:notes+=chords[(beat//8)%4]
        for j,note in enumerate(notes):
            t=np.arange(int(RATE*.85))/RATE;freq=440*2**((note-69)/12)
            sound=(np.sin(2*np.pi*freq*t)+.18*np.sin(2*np.pi*freq*2.01*t))*np.exp(-t*5)*(1-np.exp(-t*180))*.045
            start=round((at+j*.017)*RATE);length=min(len(sound),n-start)
            if length>0:score[start:start+length]+=sound[:length,None]*np.array([.9,1.0])
    for s in cfg['timeline'][1:]:
        length=round(RATE*.5);noise=rng.normal(size=length);sound=(noise-np.convolve(noise,np.ones(10)/10,'same'))*np.sin(np.linspace(0,np.pi,length))**2*.012
        start=round(s['a']*RATE);length=min(length,n-start)
        score[start:start+length]+=sound[:length,None]
    t=np.arange(n)/RATE;score*=np.minimum(1,t/.8)[:,None]*np.clip((cfg['duration']-t)/1.1,0,1)[:,None]
    write_wav(project/'out/music.wav',score)

def probe(path):
    return json.loads(command(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',path],capture_output=True,text=True).stdout)

def packets(path):
    return command(['ffmpeg','-v','error','-i',path,'-map','0:v:0','-c:v','copy','-f','hash','-hash','sha256','-'],capture_output=True,text=True).stdout.strip()

def build(project,cfg,picture=None):
    target=project/(stem(cfg)+'.mp4')
    assert not target.exists(),'Output already exists; increment revision before replacing a rendered release'
    assert (project/'narration/aligned-config.sha256').read_text().strip()==config_hash(cfg),'Run align after changing the episode'
    original=Path(picture).resolve() if picture else None
    picture=original or project/'out/picture.mp4'
    if not original:
        node,env=node_env();renderer=subprocess.Popen([node,'--expose-gc',str(project/'render_episode.cjs'),'--raw'],stdout=subprocess.PIPE,env=env)
        encoder=subprocess.Popen(['ffmpeg','-v','warning','-y','-f','rawvideo','-pixel_format','rgba','-video_size','1080x1920','-framerate','24','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p',str(picture)],stdin=renderer.stdout)
        renderer.stdout.close();code=encoder.wait();render_code=renderer.wait()
        assert code==0 and render_code==0,'Rendering failed'
    info=probe(picture);v=next(s for s in info['streams'] if s['codec_type']=='video')
    assert (v['width'],v['height'],v['r_frame_rate'],v['codec_name'],v['pix_fmt'])==(1080,1920,'24/1','h264','yuv420p'),'Picture format differs from brand profile'
    assert int(v['nb_read_frames'])==round(cfg['duration']*24),'Picture duration differs from timeline'
    music(project,cfg);has_subtitles=(project/'narration.srt').stat().st_size>0
    temporary=project/'out'/(stem(cfg)+'-mux.mp4')
    args=['ffmpeg','-nostdin','-v','warning','-y','-i',picture,'-i',project/'out/music.wav','-i',project/'narration.wav']
    if has_subtitles:args+=['-i',project/'narration.srt']
    volume='.48' if has_subtitles else '.75'
    filters=f'[1:a]loudnorm=I=-15:TP=-2:LRA=7,aresample=48000,volume={volume}[bed];[2:a]asplit=2[voice][control];[bed][control]sidechaincompress=threshold=.025:ratio=5:attack=15:release=380:makeup=1[duck];[duck][voice]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0,alimiter=limit=.95:level=0[mix]'
    args+=['-filter_complex',filters,'-map','0:v:0','-map','[mix]','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000']
    if has_subtitles:args+=['-map','3:s:0','-c:s','mov_text','-metadata:s:s:0','language=zho','-disposition:s:0','0']
    args+=['-metadata:s:a:0','language=zho','-t',str(cfg['duration']),'-movflags','+faststart',temporary]
    command(args)
    completed=probe(temporary)
    track=next(s for s in completed['streams'] if s['codec_type']=='video')
    assert int(track['nb_read_frames'])==round(cfg['duration']*24),'Incomplete encoded output'
    temporary.replace(target)
    if original:assert packets(original)==packets(target),'Video packets changed during voice-only reuse'
    print(str(target))

def check(project,cfg):
    video=project/(stem(cfg)+'.mp4');info=probe(video)
    v=next(s for s in info['streams'] if s['codec_type']=='video')
    assert int(v['nb_read_frames'])==round(cfg['duration']*24)
    assert abs(float(info['format']['duration'])-cfg['duration'])<.06
    assert (v['width'],v['height'],v['r_frame_rate'],v['codec_name'],v['pix_fmt'])==(1080,1920,'24/1','h264','yuv420p')
    voice=read_pcm(project/'narration.wav');assert len(voice)==round(cfg['duration']*RATE)
    assert np.max(np.abs(voice))<.99,'Clipped voice PCM'
    mixed=read_pcm(video);peak=float(np.max(np.abs(mixed)));assert peak<.9999,'Clipped mix PCM'
    for item in json.loads((project/'narration/alignment.json').read_text()):
        assert item['end']<=item['window_end']+.02 and item['tempo']<=1.2
    qa=project/'out/encoded-check';qa.mkdir(exist_ok=True)
    for s in cfg['timeline']:
        point=s['a']+min(2,s['duration']*.65)
        command(['ffmpeg','-v','error','-y','-ss',str(point),'-i',video,'-frames:v','1','-q:v','2',qa/f'scene-{s["id"]:02d}.jpg'])
    command(['ffmpeg','-v','error','-y','-ss',str(min(2,cfg['duration']*.5)),'-i',video,'-frames:v','1','-q:v','2',project/'poster.jpg'])
    report={'episode_id':cfg['episode_id'],'revision':cfg['revision'],'duration':cfg['duration'],'frames':int(v['nb_read_frames']),
            'mixed_pcm_peak':round(peak,5),'automated_checks':'passed','visual_review':'pending','listening_review':'pending',
            'sources':cfg.get('source_notes',[]),'saved_locations':[], 'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest()}
    (project/'release.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))

def package(project,cfg):
    target=project/(stem(cfg)+'-source.zip')
    assert not target.exists(),'Source release already exists; increment revision for a new release'
    report=json.loads((project/'release.json').read_text())
    video=project/(stem(cfg)+'.mp4')
    assert report['revision']==cfg['revision'] and report['video_sha256']==hashlib.sha256(video.read_bytes()).hexdigest(),'Run check for this release'
    files=['episode.json','lesson-input.md','package.json','render_episode.cjs','crayon_contrast.cjs','logo.cjs','logo-design.json',
           'Zhi-Jie-logo.png','Zhi-Jie-logo.svg','逐字稿.md','narration.wav','narration.mp3','narration.srt','poster.jpg','release.json']
    files+=[str(p.relative_to(project)) for folder in ['fonts','tools','narration'] for p in (project/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.tmp.' not in p.name]
    with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=6) as archive:
        for name in files:
            path=project/name;assert path.is_file(),f'Missing source: {name}'
            if path.suffix in {'.py','.json','.md','.txt','.srt','.cjs'}:
                assert not re.search(rb'sk-[A-Za-z0-9]{20,}',path.read_bytes()),f'Remove credential from {name}'
            archive.write(path,stem(cfg)+'/'+name)
    with ZipFile(target) as archive:assert archive.testzip() is None
    print(str(target))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');parser.add_argument('action',choices=['validate','script','stills','align','build','check','package']);parser.add_argument('--picture')
    args=parser.parse_args();project,cfg=load(args.project);(project/'out').mkdir(exist_ok=True);transcript(project,cfg)
    if args.action in {'validate','script'}:print(json.dumps({'episode':cfg['episode_id'],'seconds':cfg['duration'],'scenes':len(cfg['timeline']),'validation':'passed'},ensure_ascii=False))
    elif args.action=='stills':
        node,env=node_env();command([node,project/'render_episode.cjs','--stills'],env=env)
    elif args.action=='align':align(project,cfg)
    elif args.action=='build':build(project,cfg,args.picture)
    elif args.action=='check':check(project,cfg)
    elif args.action=='package':package(project,cfg)

if __name__=='__main__':main()
