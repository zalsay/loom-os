#!/usr/bin/env python3
"""EP06 v003 旁白：session80 线（没碰设备，先在电脑上做只读探针）。
MiMo voiceclone 整篇一次合成。音色样本用 EP05 旁白成片（系列连续）。"""
import base64, json, os, re, sys, urllib.request

for line in open("/Volumes/RC500/dev/loom-os/宣传计划/.env"):
    m = re.match(r"\s*MIMO_API_KEY\s*=\s*(\S+)", line)
    if m:
        API_KEY = m.group(1).strip()
        break
else:
    sys.exit("MIMO_API_KEY not found")

with open("/tmp/ep5live/clone/full.wav", "rb") as f:
    VOICE = "data:audio/wav;base64," + base64.b64encode(f.read()).decode()

SEGMENTS = [
    "上一集它卡在交卷，整晚没回话。这次我没急着碰它，先在电脑上写了支探针。",
    "探针很克制，只问能干不能干，不读文件，也不重跑导出。它只查，不动手。三组跑下来，全过。屏幕上最后那句，我盯着看了半天——主机验证通过，设备运行时还没验证。",
    "说白了，电脑这边我拿准了，真机那边还是空白。慢一点不怕，怕的是瞎试。下一集，把探针送进设备。",
]
TEXT = "".join(SEGMENTS)
n = len([c for c in TEXT if "\u4e00" <= c <= "\u9fff"])
print("汉字数", n, "目标秒", round(n / 4.4, 1))

instruction = (
    "用正常语速朗读，像跟朋友面对面聊天，语气自然、带点讲故事的口气，"
    "不要念得像播新闻，不要拖长音，不要漏掉任何一句，每个分句都要念到，"
    f"句间停顿短一点，整篇在约 31 秒内读完，语速适中偏快，吐字清楚。"
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
os.makedirs("/tmp/ep6c/clone", exist_ok=True)
out = "/tmp/ep6c/clone/full.wav"
with open(out, "wb") as f:
    f.write(base64.b64decode(data))
print("saved", out)
