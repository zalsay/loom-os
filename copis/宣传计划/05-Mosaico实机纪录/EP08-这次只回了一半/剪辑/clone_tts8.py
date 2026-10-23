#!/usr/bin/env python3
"""EP08 旁白：整篇一次 MiMo voiceclone 合成（79 汉字），不拆句、不混 take。
音色样本沿用系列持久化样本（EP06 旁白）。输出 take-1，保留原档。"""
import base64, json, os, re, sys, urllib.request, wave

BASE = "/Volumes/RC500/dev/loom-os/copis/宣传计划"
EP = f"{BASE}/05-Mosaico实机纪录/EP08-这次只回了一半"
VOICE = f"{EP}/剪辑/音频/voice-sample-original.mp3"


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
    "设备回话了——它只说了一半。"
    "等了两分多钟，终端才跳出回执。"
    "七项底层接口可查，但状态停在“部分完成”。"
    "能回话，不等于能跑。"
    "剩余项未知，它在响应，但还没交卷。"
    "算开了头。下一集，把剩下的一半问回来。"
)
print("汉字数", len([c for c in TEXT if "一" <= c <= "鿿"]))

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
data = base64.b64decode(resp["choices"][0]["message"]["audio"]["data"])
adir = f"{EP}/剪辑/音频"
os.makedirs(adir, exist_ok=True)
# 不覆盖既有 take：取下一个未占用编号，排他创建
n = 1
while True:
    out = f"{adir}/take-{n}-narration.wav"
    try:
        fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        break
    except FileExistsError:
        n += 1
with os.fdopen(fd, "wb") as f:
    f.write(data)
with wave.open(out, "rb") as w:
    print("saved", out, "seconds", round(w.getnframes() / w.getframerate(), 3), "rate", w.getframerate(), "ch", w.getnchannels())
