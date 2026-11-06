#!/usr/bin/env python3
"""EP10 旁白：整篇一次 MiMo voiceclone 合成，沿用系列音色样本（EP06/EP08/EP09 同源）。
文本与《选题与分镜稿.md》v3.1 分镜锁定，数字与 session160 验收记录一致：
77 上传/299 请求/73 清单文件哈希一致 0 不符/launcher 最后传/runtime not_run。"""
import base64, json, os, re, sys, urllib.request, wave

BASE = "/Volumes/RC500/dev/loom-os/copis/宣传计划"
EP = f"{BASE}/05-Mosaico实机纪录/EP10-只上传精确读回"
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

SENTENCES = [
    "77 个文件，逐个读回来了。",
    "每个文件都要读回来；一处没过，这轮就停。",
    "这轮上传，启动器排在最后。",
    "77 个上传，77 个读回。",
    "73 个与清单哈希一致；0 个不符。",
    "设备里，能看见吗？",
]
# operator 规则（2026-10-22）：整篇一次性合成；用 MiMo 原生 (pauses) audio tag 预留句间停顿，供后续按静音边界分段拆入
GAP = "(pauses for a moment)"
TEXT = GAP.join(SENTENCES)
print("汉字数", len([c for c in TEXT if "一" <= c <= "鿿"]))

instruction = (
    "用正常偏快的语速朗读，像跟朋友面对面聊天，语气自然、利落，"
    "不要念得像播新闻，不要拖长音，吐字清楚。"
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
outdir = f"{EP}/剪辑/音频"
n = 1
while True:
    out = f"{outdir}/take-{n}-narration.wav"
    try:
        fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        break
    except FileExistsError:
        n += 1
with os.fdopen(fd, "wb") as f:
    f.write(data)
with wave.open(out, "rb") as w:
    print("single-shot narration:", out, round(w.getnframes() / w.getframerate(), 3), "s")
