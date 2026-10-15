#!/usr/bin/env python3
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
import wave
from workflow import load, request, fingerprint, cache_matches

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--segments',help='Comma-separated scene numbers')
    args=parser.parse_args()
    project,config=load(args.project)
    selected={int(v) for v in args.segments.split(',')} if args.segments else None
    key=os.environ.get('MIMO_API_KEY','').strip()
    raw=project/'narration/raw'
    raw.mkdir(parents=True,exist_ok=True)
    for scene in config['timeline']:
        if not scene['narration'] or selected and scene['id'] not in selected:
            continue
        cached=cache_matches(project,config,scene)
        if args.dry_run:
            print(json.dumps({'scene':scene['id'],'text':scene['narration'],'window':round(scene['end']-scene['start'],3),'cached':cached},ensure_ascii=False))
            continue
        if cached:
            print(f'Scene {scene["id"]}: valid cached audio',flush=True)
            continue
        if not key:
            raise SystemExit('MIMO_API_KEY is required for new or changed narration.')
        req=urllib.request.Request('https://api.xiaomimimo.com/v1/chat/completions',
            data=json.dumps(request(config,scene),ensure_ascii=False).encode(),
            headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},method='POST')
        print(f'Scene {scene["id"]}: generating narration',flush=True)
        try:
            with urllib.request.urlopen(req,timeout=180) as response:
                result=json.load(response)
        except urllib.error.HTTPError as error:
            detail=error.read(600).decode('utf-8','replace').replace(key,'[REDACTED]')
            raise SystemExit(f'MiMo HTTP {error.code}: {detail}') from None
        encoded=result['choices'][0]['message']['audio']['data']
        if encoded.startswith('data:'):encoded=encoded.split(',',1)[1]
        audio=base64.b64decode(encoded,validate=True)
        temporary=raw/f'{scene["id"]:02d}.tmp.wav'
        temporary.write_bytes(audio)
        with wave.open(str(temporary)) as wav:
            seconds=wav.getnframes()/wav.getframerate()
        temporary.replace(raw/f'{scene["id"]:02d}.wav')
        meta={'fingerprint':fingerprint(config,scene),'audio_sha256':hashlib.sha256(audio).hexdigest(),
              'model':config['voice']['model'],'voice':config['voice']['voice'],'seconds':seconds,
              'text':scene['narration'],'usage':result.get('usage')}
        (raw/f'{scene["id"]:02d}.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        print(f'Scene {scene["id"]}: saved {seconds:.2f}s',flush=True)

if __name__=='__main__':main()
