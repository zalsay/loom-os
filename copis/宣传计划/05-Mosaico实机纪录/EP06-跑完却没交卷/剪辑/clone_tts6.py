#!/usr/bin/env python3
"""EP06 旁白：MiMo voiceclone 整篇一次合成（跑完却没交卷 三幕）。音色样本用 EP05 旁白成片。"""
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
    "昨晚那份报告，我翻到很晚。今天一早，我带着新版回来了。",
    "七十三个文件，一个不差。检查按钮按下去，它真的开跑了——跑了一阵，自己停了下来。回执导出，四零四。",
    "说实话，看到这行红字，我反而踏实了。它跑完了全程，只是交卷的时候摔了跤。摔跤不可怕，可怕的是说不清自己怎么摔的。下一集，我先教它把失败讲清楚。",
]
TEXT = "".join(SEGMENTS)
n = len([c for c in TEXT if "\u4e00" <= c <= "\u9fff"])
print("汉字数", n, "目标秒", round(n / 4.4, 1))

instruction = (
    "像跟朋友面对面聊天那样朗读，语气自然放松，带点讲故事的口气，"
    "不要念得像播新闻，不要漏掉任何一句，每个分句都要念到，"
    f"整篇节奏从容一点，大概 31 秒读完，吐字清楚。"
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
os.makedirs("/tmp/ep6live/clone", exist_ok=True)
out = "/tmp/ep6live/clone/full.wav"
with open(out, "wb") as f:
    f.write(base64.b64decode(data))
print("saved", out)
