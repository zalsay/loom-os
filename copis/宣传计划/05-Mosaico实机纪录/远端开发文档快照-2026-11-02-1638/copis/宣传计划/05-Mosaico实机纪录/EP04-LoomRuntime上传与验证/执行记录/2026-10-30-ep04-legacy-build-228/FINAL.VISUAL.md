# 最终 MP4 视觉复核

主 Agent 实际查看 review-sheets 下 preflight/formal × Otty/Safari/MAC-camera-preview 六张联系表（18 个最终抽帧），另查看 formal/Otty-mp4-1.jpg 原尺寸中帧。

- Otty：原同窗任务可见，100 测试、1 ERROR、2.524 秒及 no configuration 失败结果清楚；密集文字 PARTIAL。错误是官方解析夹具组件名 espressif/x 非法，不是部署或固件运行结果。
- Safari：旧 session202 的停止画面保持；下沿 PARTIAL，不是设备控制台，也不是本轮新 UI 验收。
- 相机：设备、外壳与 USB 线可辨认。黑屏不证明关机、ROM 模式或 Runtime 状态。
- 六个 MP4 已完成编码、完整解码和独立解码；这里只放行本轮对应 MOV 清理，不改原 verification_failed，不重演测试。
- 发布 pending；没有设备 HTTP、串口、重启、刷写或 Runtime 操作。
