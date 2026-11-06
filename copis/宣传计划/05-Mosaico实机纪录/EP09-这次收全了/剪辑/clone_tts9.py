#!/usr/bin/env python3
"""EP09 旁白：整篇一次 MiMo voiceclone 合成，沿用系列音色样本（EP06/EP08 同源）。
文本与《选题与分镜稿.md》v1 分镜锁定，数字与 session147 验收记录一致。"""
import base64, json, os, re, sys, urllib.request, wave

BASE = "/Volumes/RC500/dev/loom-os/copis/宣传计划"
EP = f"{BASE}/05-Mosaico实机纪录/EP09-这次收全了"
VOICE = f"{BASE}/05-Mosaico实机纪录/EP08-这次只回了一半/剪辑/音频/voice-sample-original.mp3"

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
    "这次，是真的收全了。"
    "上一集它只回了一半。这一份绑定备份，就等一次人工点击。"
    "设备那头，列表里多了它。"
    "点一下，35 秒保护期，不轮询。7 次读取全部成功——90189 字节，校验值三处一致。"
    "收全的，只是一份绑定 Lua 文件，不是整机；Runtime 还没跑起来。"
    "下一关，把新的 Runtime 完整传上去——传输协议已经通过了本地模拟测试。"
    "下一集，只上传，精确读回。"
)
print("汉字数", len([c for c in TEXT if "一" <= c <= "鿿"]))

instruction = (
    "用正常偏快的语速朗读，像跟朋友面对面聊天，语气自然、利落，"
    "不要念得像播新闻，不要拖长音，不要停顿过长，每个分句都要念到，"
    "整篇约35秒内读完，吐字清楚。"
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
