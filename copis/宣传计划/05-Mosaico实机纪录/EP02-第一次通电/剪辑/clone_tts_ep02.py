# -*- coding: utf-8 -*-
"""EP02 通电篇配音：myvioce 音色整篇一次合成（4.4字/秒档），格式沿用 v7 成功配方"""
import base64, json, os, urllib.request

API_KEY = os.environ["MIMO_API_KEY"]
with open("/tmp/ep1/voice-sample2.mp3", "rb") as f:
    VOICE = "data:audio/mpeg;base64," + base64.b64encode(f.read()).decode()

# 5 段旁白（素材实测分镜：0-8 黑屏+按电源 / 8-20 点亮 / 20-34 触控设置 / 34-52 配对+系统 / 52-60 片尾钩子）
SEGMENTS = [
    "上一集开完箱，今天给它第一次通电。屏幕还黑着，先找到侧边的电源键。",          # P1 33字 @0.6
    "按下去的一瞬间，屏幕亮起来了。第一次点亮成功，亮度很足，画面也清楚。这块二点一六寸的方屏，看着确实舒服。",  # P2 51字 @8.2
    "开机后先做基础设置。触控很跟手，点哪是哪。连网络要用屏幕键盘输密码，一格一格点，速度不快，但输入很稳。",  # P3 51字 @20.2
    "配对请求发出之后，系统就顺利跑起来了。主界面是一排应用图标，快捷面板、设置列表都点了一遍，反应没有卡顿。",  # P4 51字 @34.2
    "下一集，给它装上模块，让它真正动起来。关注织界，看设备的成长记录。",          # P5 33字 @52.2
]
TEXT = "".join(SEGMENTS)
n = sum(1 for c in TEXT if '\u4e00' <= c <= '\u9fff')
print(f"汉字数: {n}, 目标 {n/4.4:.0f}s")

instruction = (
    "用正常语速朗读，像跟朋友面对面聊天，吐字干净利落，"
    f"不要拖沓、不要停顿过长，整篇在约 {round(n/4.4)} 秒内自然读完，语速适中偏快一点，但吐字要清楚。"
    "句号处稍作停顿即可，段落之间不要额外加长停顿。"
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
data = json.loads(urllib.request.urlopen(req, timeout=300).read())
wav = base64.b64decode(data["choices"][0]["message"]["audio"]["data"])
out = "/tmp/ep1/clone/full-ep02.wav"
with open(out, "wb") as f:
    f.write(wav)
print(f"full-ep02.wav: {len(wav)} bytes -> {len(wav)/48000.0:.2f}s")
