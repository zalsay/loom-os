#!/usr/bin/env python3
"""EP12 草稿：既有系列克隆音色，整篇单次合成；密钥仅来自进程环境。"""
import base64, json, os, urllib.request, wave
from pathlib import Path
root = Path(__file__).resolve().parents[2]
ep = Path(__file__).resolve().parent
voice = root / 'EP08-这次只回了一半/剪辑/音频/voice-sample-original.mp3'
clauses = [
    '上期说，新固件做了两次还没成。今天把后来的结果补上：固件在电脑上做出来了。',
    '十月二十七日，制作、检查和打包都跑完了，固件文件也整理好了。',
    '但做出来，不等于设备已经用上。到这次检查时，新固件还没有刷进设备，也没有在设备上运行。',
    '设备能通过网络联系上。装之前，还要核对连接、设备里的情况和需要的备份。',
    '所以这次的答案是：做出来了，还没装进去。接下来先把条件查清楚。',
]
text = ' (pauses for a moment) '.join(clauses)
body = {'model':'mimo-v2.5-tts-voiceclone','messages':[{'role':'user','content':'用清晰的普通话，正常偏快，像跟朋友聊天一样自然朗读，句间自然停顿；只读提供的文字，不增删。'},{'role':'assistant','content':text}],'audio':{'format':'wav','voice':'data:audio/mpeg;base64,'+base64.b64encode(voice.read_bytes()).decode()}}
req=urllib.request.Request('https://api.xiaomimimo.com/v1/chat/completions',data=json.dumps(body,ensure_ascii=False).encode(),headers={'Authorization':'Bearer '+os.environ['MIMO_API_KEY'],'Content-Type':'application/json'},method='POST')
with urllib.request.urlopen(req, timeout=240) as resp: data=json.load(resp)
out=ep/'音频/take-v001-whole.wav'
out.parent.mkdir(parents=True,exist_ok=True)
with out.open('xb') as f: f.write(base64.b64decode(data['choices'][0]['message']['audio']['data']))
(ep/'音频/逐字稿-v001.txt').write_text('\n'.join(clauses)+'\n',encoding='utf-8')
with wave.open(str(out),'rb') as w: print('whole take',out,'duration',round(w.getnframes()/w.getframerate(),2),'rate',w.getframerate())
