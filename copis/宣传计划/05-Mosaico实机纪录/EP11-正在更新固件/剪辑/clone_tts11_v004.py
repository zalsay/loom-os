#!/usr/bin/env python3
import base64, json, os, urllib.request, wave
from pathlib import Path

base = Path('/Volumes/RC500/dev/loom-os/copis/宣传计划')
ep = base / '05-Mosaico实机纪录/EP11-正在更新固件'
voice = base / '05-Mosaico实机纪录/EP08-这次只回了一半/剪辑/音频/voice-sample-original.mp3'
lines = [
    '文件传回来了，设备里为什么还看不见？',
    '我在做新固件，相关触摸检查通过了，但没有真的点过设备。',
    '第一回，等了快十分钟，还没开始编译。',
    '第二回，接着上回保留的一部分资料做，又因为连接问题停了。',
    '还没做成，但进度没丢。你猜，下一次能做成吗？',
    '后续结果，下一期揭晓。',
]
key = os.environ['MIMO_API_KEY']
body = {'model': 'mimo-v2.5-tts-voiceclone', 'messages': [
    {'role': 'user', 'content': '用正常偏快的语速朗读，像跟朋友聊天，语气自然清楚，不要拖长音。括号中的 pauses for a moment 是静音指令，绝对不要念出任何括号或英文，只朗读中文。'},
    {'role': 'assistant', 'content': '(pauses for a moment)'.join(lines)}],
    'audio': {'format': 'wav', 'voice': 'data:audio/mpeg;base64,' + base64.b64encode(voice.read_bytes()).decode()}}
request = urllib.request.Request('https://api.xiaomimimo.com/v1/chat/completions', data=json.dumps(body, ensure_ascii=False).encode(), headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(request, timeout=300) as response:
    result = json.load(response)
audio = base64.b64decode(result['choices'][0]['message']['audio']['data'])
outdir = ep / '剪辑/音频'
for n in range(1, 1000):
    out = outdir / f'take-{n}-narration.wav'
    try:
        with out.open('xb') as f:
            f.write(audio)
        break
    except FileExistsError:
        continue
else:
    raise RuntimeError('没有可用的 take 文件名')
with wave.open(str(out), 'rb') as w:
    print('整篇 take:', out.name, '时长:', round(w.getnframes()/w.getframerate(), 3), '秒')
