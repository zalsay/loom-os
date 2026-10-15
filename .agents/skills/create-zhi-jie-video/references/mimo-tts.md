# MiMo配音

使用前检查官方当前文档：https://mimo.mi.com/docs/zh-CN/quick-start/usage-guide/audio/speech-synthesis-v2.5 。以下配置已用于织界V12，记录于2026-10-10，未来接口变化时更新。

- POST `https://api.xiaomimimo.com/v1/chat/completions`，Bearer认证与JSON请求。
- 模型 `mimo-v2.5-tts`，中文预置音色 `茉莉`，非流式 `wav`。
- 风格指令放 `role: user`，逐字稿放 `role: assistant`；解码 `choices[0].message.audio.data` 的Base64。
- 温暖、清晰、略轻快的普通话女声，像引导孩子探索的年轻导师；AI读作A I，织界读作zhī jiè。每段按窗口自然读完，保持音色一致。
- `scripts/mimo_tts.py` 按文本、模型、音色、风格、时长窗口与接口生成指纹；完全匹配才复用音频。

只从当前进程环境 `MIMO_API_KEY` 取密钥。不硬编码、不写进skill、项目、版本库、日志、ZIP或示例，不复述旧对话密钥。缺少配置时完成其他环节并如实说明配音状态。

制作配音仅提交需要朗读的逐字稿，不附原始课堂文档或额外隐私字段。TTS授权不涵盖云端ASR、克隆、其他语音服务或发布。默认本地时长/峰值检查与人工试听；云端转写由用户明确要求或授权后再做。自动审批拒绝时不要改接口、编码或执行路径绕过。

翻页后约0.6秒开始朗读，片尾留短暂余韵。测实际时长，超出窗口优先精简文案或调镜头，保持音高的变速最多1.2倍，不能截句尾。SRT按句长度分配时间只是近似；实际听检负责口误与语感，不能把数值检查称为听过。
