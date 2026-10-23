#!/usr/bin/env python3
"""EP05 旁白：MiMo voiceclone 整篇一次合成（悬念钩子三段）。"""
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
    "敲门的结果出来了。六十八项编译全过，六十二个依赖，一个不缺。可它把自己锁在了门里。",
    "门槛亮了：触摸没确认之前，连界面都不许起。别骂它，这是保护，先证明你能摸，再谈开机。",
    "我没重跑，也没碰它，只把报告读完。开锁的钥匙怎么配，下一集见。",
]
TEXT = "".join(SEGMENTS)
n = len([c for c in TEXT if "\u4e00" <= c <= "\u9fff"])
print("汉字数", n, "目标秒", round(n / 4.4, 1))

instruction = (
    "用正常语速朗读，像跟朋友面对面聊天，吐字干净利落，"
    "不要漏掉任何一句，每个分句都要念到，句号处稍作停顿即可，"
    f"节奏紧凑，句间停顿短，不要拖长音，整篇在约 22 秒内读完，吐字要清楚。"
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
os.makedirs("/tmp/ep5live/clone", exist_ok=True)
with open("/tmp/ep5live/clone/full.wav", "wb") as f:
    f.write(base64.b64decode(data))
print("saved /tmp/ep5live/clone/full.wav")
