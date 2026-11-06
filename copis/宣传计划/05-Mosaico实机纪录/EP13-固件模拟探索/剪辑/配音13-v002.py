#!/usr/bin/env python3
"""EP13 一次整篇 MiMo 配音；密钥仅从环境读取。"""
import base64, json, os, urllib.request, wave
from pathlib import Path
p = Path(__file__).resolve().parent
voice = p.parents[1] / 'EP08-这次只回了一半/剪辑/音频/voice-sample-original.mp3'
text = (p / '音频/逐字稿-v002.txt').read_text(encoding='utf-8').strip().replace('\n', '')
out = p / '音频/take-v002-whole.wav'
if out.exists():
    raise SystemExit('输出已存在，停止')
body = {'model':'mimo-v2.5-tts-voiceclone','messages':[
    {'role':'user','content':'用正常语速朗读，像跟朋友面对面聊天，吐字干净利落，不要拖沓，不要停顿过长，整篇在约四十秒内自然读完，只读提供的正文，不要增删内容。'},
    {'role':'assistant','content':text}],
    'audio':{'format':'wav','voice':'data:audio/mpeg;base64,'+base64.b64encode(voice.read_bytes()).decode()}}
req = urllib.request.Request('https://api.xiaomimimo.com/v1/chat/completions', data=json.dumps(body,ensure_ascii=False).encode(), headers={'Authorization':'Bearer '+os.environ['MIMO_API_KEY'],'Content-Type':'application/json'}, method='POST')
with urllib.request.urlopen(req,timeout=240) as resp:
    result=json.load(resp)
with out.open('xb') as f:
    f.write(base64.b64decode(result['choices'][0]['message']['audio']['data']))
with wave.open(str(out),'rb') as w:
    print('整篇 WAV：%.2f 秒，%d Hz' % (w.getnframes()/w.getframerate(),w.getframerate()))
