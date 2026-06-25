# UniqoRemote — 生产就绪补全计划

> 基于设计文档差距分析，Phase 3-7 精选实现。

## 补全优先级

| 优先级 | 模块 | 理由 |
|--------|------|------|
| P0 | server/rendezvous — ID 注册 | 阻塞所有网络功能 |
| P0 | session/audio.py — 音频传输 | 设计文档指定核心功能 |
| P0 | pipeline/encoder/ffmpeg.py — FFmpeg 编码 | 阻塞视频传输 |
| P1 | pipeline/decoder/ffmpeg.py — FFmpeg 解码 | 阻塞远程画面 |
| P1 | ui/windows/remote.py — 远程画面 | 阻塞可视化 |
| P1 | ai/client.py → DeepSeek 实现 | AI 功能核心 |
| P2 | ui/windows/file_manager.py — 文件管理 UI | 向日葵特色 |
| P2 | ui/windows/terminal.py — 终端 UI | 向日葵特色 |
| P2 | ai/assistant.py + translate.py | AI 增强 |
| P2 | 打包/PyInstaller | 分发就绪 |

## 架构约束

- 所有模块通过 ABC 接口解耦
- FFmpeg 缺失时自动降级为 mock
- AI 模块通过环境变量 PYRDP_AI_API_KEY 配置
- 命名管道 IPC → 保持 TCP 回环 (Windows 兼容)
