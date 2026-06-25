# UniqoRemote

Python + PySide6 远程桌面系统，全新自研协议，兼容 Windows。

[![Test](https://github.com/Geek-13/uniqoremote/actions/workflows/test.yml/badge.svg)](https://github.com/Geek-13/uniqoremote/actions/workflows/test.yml)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Tests](https://img.shields.io/badge/tests-143%20passed-brightgreen)

## 架构

```
ui ──────▶ session ──────▶ core
 │              │             │
 │              ▼             ▼
 │           pipeline     transport (UDP/TCP/P2P)
 │              │             │
 │              ▼             │
 └────────── agent ◀──────────┘
```

- **UI 进程** (user): 界面渲染、网络通信、会话管理
- **Agent 进程** (system): 屏幕捕获、输入注入、音频采集
- **Server**: ID 注册、P2P 打洞协调、中继转发
- 进程间通过 TCP 回环 IPC 通信，消息格式与网络层统一 (msgpack)

## 快速开始

```powershell
# 环境要求: Python 3.11+, ffmpeg (可选)
git clone https://github.com/Geek-13/uniqoremote.git
cd uniqoremote
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev,ui]"
```

## 运行

```powershell
# 加密通道演示 (协议 + 加密 + UDP 回环)
python examples/demo.py

# 启动服务端 (Rendezvous + Relay)
python -m uniqoremote.server

# 启动 Agent (屏幕捕获 + 输入注入)
python -m uniqoremote.agent

# 启动 UI (主界面)
python -m uniqoremote.ui
```

## 功能

### 核心功能
- 远程桌面 (P2P 直连 + 中继回退)
- 键鼠远程控制 (SendInput ctypes)
- 剪贴板同步 (Win32 Clipboard API)
- 文件传输 (分块 + 断点续传模型)
- 音频传输 (采集 → 管道 → 播放)

### 向日葵/ToDesk 特色
- 远程文件管理器 (GUI 对话框)
- 远程终端 CMD (subprocess 后端 + GUI)
- 多屏管理 / 屏幕墙
- 聊天消息
- 会话录制
- 隐私屏 / 远程黑屏

### AI 能力 (DeepSeek)
- 屏幕 OCR + 问答
- 实时翻译 (含缓存)
- 智能操作建议
- 异常行为检测

## 项目结构

```
src/uniqoremote/
├── core/                    基础层 — 零业务依赖
│   ├── protocol.py          帧编解码 + msgpack
│   ├── crypto.py            X25519 + ChaCha20-Poly1305
│   ├── channel.py           加密通道
│   ├── config.py            TOML 配置
│   ├── events.py            事件类型 + 枚举
│   └── logging.py           structlog JSON 日志
│
├── transport/               传输层
│   ├── base.py              Transport ABC
│   ├── udp.py               asyncio UDP
│   ├── tcp.py               asyncio TCP (长度前缀)
│   └── p2p.py               STUN + UDP 打洞
│
├── pipeline/                采集管道
│   ├── capturer/
│   │   ├── base.py          Capturer ABC
│   │   └── gdi.py           GDI 屏幕捕获 (BitBlt)
│   ├── encoder/
│   │   ├── base.py          Encoder ABC
│   │   └── ffmpeg.py        FFmpeg H.264/H.265 编解码
│   ├── decoder/
│   │   └── base.py          Decoder ABC
│   └── pipeline.py          捕获→编码→Channel 管道
│
├── input/                   输入控制
│   ├── base.py              InputController ABC
│   └── controller.py        SendInput 键鼠注入
│
├── session/                 会话服务
│   ├── manager.py           会话状态机 (6 状态)
│   ├── router.py            消息路由分发
│   ├── clipboard.py         Win32 剪贴板同步
│   ├── file_transfer.py     文件传输管理器
│   ├── chat.py              聊天消息
│   ├── recording.py         会话录制
│   ├── terminal.py          远程 CMD (同步/异步)
│   ├── monitor.py           多屏枚举
│   ├── privacy.py           隐私屏控制
│   ├── audio.py             音频采集/播放
│   └── audio_pipeline.py    音频管道
│
├── agent/                   代理进程
│   ├── __main__.py          入口
│   └── ipc_server.py        TCP 回环 IPC
│
├── ui/                      UI 进程
│   ├── __main__.py          入口
│   ├── compose.py           依赖注入组装
│   ├── ipc_client.py        IPC 客户端
│   └── windows/
│       ├── main.py          主窗口
│       ├── remote.py        远程画面渲染
│       ├── file_manager.py  文件管理器
│       ├── terminal.py      终端对话框
│       └── settings.py      设置面板
│
├── ai/                      AI 子系统
│   ├── client.py            DeepSeek LiteLLM 客户端
│   ├── assistant.py         问答/摘要/建议
│   └── monitor.py           异常检测
│
└── server/                  云端服务器
    ├── __main__.py          入口
    ├── rendezvous/
    │   └── manager.py       设备注册 + 公钥交换
    └── relay/
        └── relay.py         中继转发
```

## 测试

```powershell
# 全部测试
pytest tests/ -v

# 覆盖率
pytest tests/ -v --cov=src/uniqoremote

# 分模块
pytest tests/core/ -v         # 协议/加密/配置
pytest tests/transport/ -v    # UDP/TCP/P2P
pytest tests/pipeline/ -v     # 采集/编码/解码
pytest tests/session/ -v      # 会话服务
pytest tests/ui/ -v           # UI 组件
pytest tests/ai/ -v           # AI 客户端
pytest tests/server/ -v       # Rendezvous/Relay
```

## 代码质量

```powershell
ruff check src/ tests/           # Lint
ruff format --check src/ tests/  # 格式检查
mypy src/uniqoremote/ --strict   # 类型检查
```

## 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| UI | PySide6 + Qt Widgets | LGPL 许可 |
| 异步 | asyncio + qasync | Qt 事件循环桥接 |
| 加密 | X25519 + ChaCha20-Poly1305 | cryptography (PyCA) |
| 序列化 | msgpack | 紧凑二进制 |
| 屏幕捕获 | GDI (BitBlt) | ctypes |
| 输入控制 | SendInput | ctypes |
| 视频编码 | FFmpeg 子进程 | H.264/H.265 |
| 日志 | structlog | JSON 结构化日志 |
| 配置 | TOML | tomllib (stdlib) |
| AI | DeepSeek + LiteLLM | OpenAI 兼容 API |
| 测试 | pytest + asyncio + qt | 143 个用例 |
| 检查 | ruff + mypy --strict | 零容忍 |
| 打包 | PyInstaller → Nuitka | 渐进优化 |
| CI | GitHub Actions | lint/typecheck/test |

## 协议

16 字节二进制帧头 + msgpack 载荷：

```
┌──────────┬────────┬──────┬─────────┬────────┬─────────┐
│  Magic   │Version │ Type │ Seq Num │ Length │ Payload │
│  4 bytes │ 2 bytes│2bytes│ 4 bytes │ 4 bytes│ N bytes │
│  "UNIQ"  │ 0x0001 │0x01  │monotonic│        │ msgpack │
└──────────┴────────┴──────┴─────────┴────────┴─────────┘
```

**端到端加密**: X25519 ECDH 密钥协商 + ChaCha20-Poly1305 AEAD，服务端不持有私钥。

**消息类型**: HELLO · PUNCH · NOTIFY · RELAY · STREAM · CONTROL · CLIPBOARD · FILE · CHAT · AUDIO · VIDEO · INPUT · ERROR · PING · PONG · BYE

## 配置

编辑 `config.toml` 或使用默认值：

```toml
[identity]
device_id = "auto"         # 自动生成 12 位 ID
device_name = "My PC"

[network]
bind_port = 21116
rendezvous_server = ""     # 留空使用局域网发现

[display]
default_width = 1920
default_height = 1080
max_fps = 30

[ai]
enabled = false            # 设置 true + 配置环境变量启用
model = "deepseek-chat"
```

AI 功能需要设置环境变量：
```powershell
$env:UNIQOREMOTE_AI_API_KEY = "sk-your-deepseek-key"
```

## 打包

```powershell
# PyInstaller
pip install pyinstaller
pyinstaller scripts/pyrdp.spec

# Nuitka (发布版)
pip install nuitka
nuitka --standalone --windows-console-mode=disable src/uniqoremote/ui/__main__.py
```

## 文档

- `docs/design.md` — 完整架构设计文档
- `AGENTS.md` — AI 开发规范
- `docs/superpowers/plans/` — 实施计划

## 许可

PySide6 (LGPL) · 项目代码 MIT
