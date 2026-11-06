# 就绪门槛失败，不能解释为空媒体成功

252的log show查询超时，start_capture尚未返回，因此runner.records为空，MP4.READY.outputs为空。没有测试或freeze、无正式录制。这里的FINAL.VISUAL.OK仅允许无输出的失败runner有限退出，不表示已检查三段实际MOV，也不授权删除它们。三段短测文件已自然结束；须由独立recover_media.py逐一完整解码、转码、抽帧和实审后才清理对应MOV。原失败/空输出报告保持，不回填为成功。
