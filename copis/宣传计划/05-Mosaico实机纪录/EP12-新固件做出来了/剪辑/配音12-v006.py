#!/usr/bin/env python3
"""EP12 整篇重生成：沿用系列音色，正文不含停顿标签；保留旧 take。"""
import base64, json, os, urllib.request, wave
from pathlib import Path
edit = Path(__file__).resolve().parent
root = edit.parents[1]
voice = root / 'EP08-这次只回了一半/剪辑/音频/voice-sample-original.mp3'
text = (edit / '音频/逐字稿-v001.txt').read_text(encoding='utf-8').strip().replace('\n', '')
out = edit / '音频/take-v006-whole.wav'
if out.exists():
    raise SystemExit('输出已存在，停止，避免覆盖')
body = {'model':'mimo-v2.5-tts-voiceclone', 'messages':[
    {'role':'user','content':'用正常语速朗读，像跟朋友面对面聊天，吐字干净利落，不要拖沓、不要停顿过长，整篇在约三十秒内自然读完，语速偏快，紧凑连贯，但吐字要清楚。只读提供的正文，不要增删内容。'},
    {'role':'assistant','content':text}], 'audio':{'format':'wav','voice':'data:audio/mpeg;base64,'+base64.b64encode(voice.read_bytes()).decode()}}
req=urllib.request.Request('https://api.xiaomimimo.com/v1/chat/completions',data=json.dumps(body,ensure_ascii=False).encode(),headers={'Authorization':'Bearer '+os.environ['MIMO_API_KEY'],'Content-Type':'application/json'},method='POST')
with urllib.request.urlopen(req,timeout=240) as resp:
    result=json.load(resp)
with out.open('xb') as f:
    f.write(base64.b64decode(result['choices'][0]['message']['audio']['data']))
with wave.open(str(out),'rb') as w:
    print('已保存整篇 WAV，时长 %.2f 秒，采样率 %d Hz' % (w.getnframes()/w.getframerate(),w.getframerate()))
