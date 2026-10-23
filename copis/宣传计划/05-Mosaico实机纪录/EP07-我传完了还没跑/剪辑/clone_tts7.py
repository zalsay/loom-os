#!/usr/bin/env python3
"""EP07 v001 旁白：session96 上传/未运行。
MiMo voiceclone 整篇一次合成；音色样本使用项目内持久化的 EP06 旁白。
输出到 EP07 剪辑/音频，不写 /tmp。"""
import base64, json, os, re, sys, urllib.request, wave

BASE = "/Volumes/RC500/dev/loom-os/copis/宣传计划"
EP = f"{BASE}/05-Mosaico实机纪录/EP07-我传完了还没跑"
VOICE = f"{EP}/剪辑/音频/voice-sample-original.mp3"
OUT = f"{EP}/剪辑/音频/take-1-narration.wav"

for line in open(f"{BASE}/.env"):
    m = re.match(r"\s*MIMO_API_KEY\s*=\s*(\S+)", line)
    if m:
        API_KEY = m.group(1).strip()
        break
else:
    sys.exit("MIMO_API_KEY not found")

with open(VOICE, "rb") as f:
    voice = "data:audio/mpeg;base64," + base64.b64encode(f.read()).decode()

TEXT = (
    "文件传进板子了，它就一定会跑吗？"
    "我先只做了一件事：把文件传进去，再逐个读回核对。"
    "读回对得上。"
    "结果那一格，是我预先留的等待位，设备还没有执行报告。"
    "这一步，我先停在这里，没有让它运行。"
    "上传完成，不等于运行成功。"
)
print("汉字数", len([c for c in TEXT if "一" <= c <= "鿿"]), "目标秒", round(len([c for c in TEXT if "一" <= c <= "鿿"]) / 4.5, 1))

instruction = (
    "用正常偏快的语速朗读，像跟朋友面对面聊天，语气自然、利落，"
    "不要念得像播新闻，不要拖长音，不要停顿过长，每个分句都要念到，"
    "整篇约20秒内读完，吐字清楚。"
)
body = {
    "model": "mimo-v2.5-tts-voiceclone",
    "messages": [
        {"role": "user", "content": instruction},
        {"role": "assistant", "content": TEXT},
    ],
    "audio": {"format": "wav", "voice": voice},
}
req = urllib.request.Request(
    "https://api.xiaomimimo.com/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    method="POST",
)
resp = json.load(urllib.request.urlopen(req, timeout=300))
data = resp["choices"][0]["message"]["audio"]["data"]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "wb") as f:
    f.write(base64.b64decode(data))
with wave.open(OUT, "rb") as w:
    print("saved", OUT, "seconds", round(w.getnframes() / w.getframerate(), 3), "rate", w.getframerate(), "ch", w.getnchannels())
