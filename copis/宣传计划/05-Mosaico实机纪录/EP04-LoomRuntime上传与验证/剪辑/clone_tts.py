#!/usr/bin/env python3
"""EP04 旁白：MiMo voiceclone 整篇一次合成。"""
import base64, json, os, re, sys, urllib.request

for line in open("/Volumes/RC500/dev/loom-os/宣传计划/.env"):
    m = re.match(r"\s*MIMO_API_KEY\s*=\s*(\S+)", line)
    if m:
        API_KEY = m.group(1).strip()
        break
else:
    sys.exit("MIMO_API_KEY not found")

with open("/tmp/ep1/voice-sample2.mp3", "rb") as f:
    VOICE = "data:audio/mpeg;base64," + base64.b64encode(f.read()).decode()

SEGMENTS = [
    "上集说过，要让板子真正跑起来。这一集，我先把底层框架整个搬进去：六十八个文件，传一个、验一个，全部对上。",
    "人按下重启，设备熄了又亮，里面的东西都还在。",
    "点开新作品，屏幕上一行红字。别慌，报告显示它跑通过一次，答案，四十二。再点一次就报错，更像是它拒绝重复交卷。",
    "六十九项旧文件再核一遍，依然全对。可真正的开机，还差一道触控门槛。下一集，我们去敲门。",
]
TEXT = "".join(SEGMENTS)
n = len([c for c in TEXT if "\u4e00" <= c <= "\u9fff"])
print("汉字数", n, "目标秒", round(n / 4.4, 1))

instruction = (
    "用正常语速朗读，像跟朋友面对面聊天，吐字干净利落，"
    "不要漏掉任何一句，每个分句都要念到，句号处稍作停顿即可，"
    f"节奏紧凑，句间停顿短，不要拖长音，整篇在约 33 秒内读完，吐字要清楚。"
)

body = {
    "model": "mimo-v2.5-tts-voiceclone",
    "messages": [
        {"role": "user", "content": instruction},
        {"role": "assistant", "content": TEXT},
    ],
    "audio": {"format": "wav", "voice": VOICE},
}
req = urllib.request.Request(
    "https://api.xiaomimimo.com/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    method="POST",
)
resp = json.load(urllib.request.urlopen(req, timeout=300))
data = resp["choices"][0]["message"]["audio"]["data"]
os.makedirs("/tmp/ep4live/clone", exist_ok=True)
with open("/tmp/ep4live/clone/full.wav", "wb") as f:
    f.write(base64.b64decode(data))
print("saved /tmp/ep4live/clone/full.wav")
