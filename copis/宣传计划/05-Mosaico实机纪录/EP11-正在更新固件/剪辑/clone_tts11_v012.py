#!/usr/bin/env python3
"""EP11: whole-take replacement; plain punctuation avoids spoken pause tags."""
import base64, json, os, urllib.request, wave
from pathlib import Path

base = Path('/Volumes/RC500/dev/loom-os/copis/宣传计划')
ep = base / '05-Mosaico实机纪录/EP11-正在更新固件'
voice = base / '05-Mosaico实机纪录/EP08-这次只回了一半/剪辑/音频/voice-sample-original.mp3'
text = ('文件传回来了，设备里为什么还看不见？'
        '我在做新固件，相关触摸检查通过了，但没有真的点过设备。'
        '第一次，等了快十分钟，还没开始编译。'
        '第二次，接着上回保留的一部分资料做，又因为连接问题停了。'
        '还没做成，但进度没丢。你猜，下一次能做成吗？'
        '后续结果，下一期揭晓。')
body = {'model': 'mimo-v2.5-tts-voiceclone', 'messages': [
    {'role': 'user', 'content': '用清晰的普通话、正常偏快的语速，像跟朋友聊天一样自然朗读。只读提供的文字，不要增删内容，清楚区分第一次和第二次。'},
    {'role': 'assistant', 'content': text}],
    'audio': {'format': 'wav', 'voice': 'data:audio/mpeg;base64,' + base64.b64encode(voice.read_bytes()).decode()}}
request = urllib.request.Request('https://api.xiaomimimo.com/v1/chat/completions', data=json.dumps(body, ensure_ascii=False).encode(), headers={'Authorization': 'Bearer ' + os.environ['MIMO_API_KEY'], 'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(request, timeout=300) as response:
    result = json.load(response)
out = ep / '剪辑/音频/take-v012-narration.wav'
with out.open('xb') as f:
    f.write(base64.b64decode(result['choices'][0]['message']['audio']['data']))
with wave.open(str(out), 'rb') as w:
    print('整篇 take:', out.name, '时长:', round(w.getnframes()/w.getframerate(), 3), '秒')
