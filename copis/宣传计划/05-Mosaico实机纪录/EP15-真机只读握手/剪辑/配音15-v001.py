#!/usr/bin/env python3
"""EP15 MiMo 一次整篇合成，密钥仅从环境读取，不覆盖已有文件。"""
import base64,json,os,urllib.request,wave
from pathlib import Path
p=Path(__file__).resolve().parent
voice=p.parents[1]/'EP08-这次只回了一半/剪辑/音频/voice-sample-original.mp3'
text=(p/'音频/逐字稿-v001.txt').read_text(encoding='utf-8').strip().replace('\n','')
out=p/'音频/take-v001-whole.wav'
if out.exists(): raise SystemExit('已有输出，不覆盖')
body={'model':'mimo-v2.5-tts-voiceclone','messages':[{'role':'user','content':'用自然流畅、干净亲切的中文讲述，语速略快，短句自然停顿，整篇约三十五秒，只朗读提供的正文，不增删。'},{'role':'assistant','content':text}], 'audio':{'format':'wav','voice':'data:audio/mpeg;base64,'+base64.b64encode(voice.read_bytes()).decode()}}
req=urllib.request.Request('https://api.xiaomimimo.com/v1/chat/completions',data=json.dumps(body,ensure_ascii=False).encode(),headers={'Authorization':'Bearer '+os.environ['MIMO_API_KEY'],'Content-Type':'application/json'},method='POST')
with urllib.request.urlopen(req,timeout=240) as response: result=json.load(response)
with out.open('xb') as f: f.write(base64.b64decode(result['choices'][0]['message']['audio']['data']))
with wave.open(str(out),'rb') as w: print(f'整篇 WAV {w.getnframes()/w.getframerate():.2f}s {w.getframerate()}Hz')
