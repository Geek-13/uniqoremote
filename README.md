# UniqoRemote

Python + PySide6 远程桌面系统，全新自研协议，兼容 Windows。

## 架构

```
ui ──────▶ session ──────▶ core
 │              │             │
 │              ▼             ▼
 │           pipeline     transport
 │              │             │
 │              ▼             │
 └────────── agent ◀──────────┘
```

双进程模型：UI 进程负责界面与网络，Agent 进程负责屏幕捕获与输入注入，通过 TCP 回环 IPC 通信。

## 快速开始

```powershell
# 环境要求: Python 3.11+, ffmpeg (可选)
git clone https://github.com/Geek-13/uniqoremote.git
cd uniqoremote
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## 运行

```powershell
# 加密通道演示
python examples/demo.py

# 启动 UI
python -m uniqoremote.ui

# 启动 Agent
python -m uniqoremote.agent

# 启动服务端
python -m uniqoremote.server
```

## 测试

```powershell
pytest tests/ -v --cov=src/uniqoremote

# 单独模块
pytest tests/core/ -v
pytest tests/transport/ -v
pytest tests/session/ -v
```

## 代码检查

```powershell
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/ --strict
```

## 项目结构

```
src/uniqoremote/
├── core/             基础层: 协议、加密、配置、事件、日志、通道
├── transport/        传输层: UDP/TCP socket
├── pipeline/         采集管道: 捕获、编码、解码
│   ├── capturer/     GDI 屏幕捕获
│   ├── encoder/      编码器接口
│   └── decoder/      解码器接口
├── input/            输入控制: SendInput 键鼠注入
├── session/          会话服务
│   ├── manager.py    会话状态机
│   ├── router.py     消息路由
│   ├── clipboard.py  剪贴板同步
│   ├── file_transfer.py  文件传输
│   ├── chat.py       聊天消息
│   ├── recording.py  会话录制
│   ├── terminal.py   远程终端
│   ├── monitor.py    多屏管理
│   └── privacy.py    隐私屏控制
├── ai/               AI 子系统
│   ├── client.py     AI 客户端接口
│   └── monitor.py    异常行为检测
├── agent/            代理进程 (系统权限)
│   └── ipc_server.py TCP 回环 IPC
├── ui/               UI 进程 (用户权限)
│   ├── compose.py    依赖注入组装
│   └── windows/      窗口组件
└── server/           云端服务器 (独立部署)
```

## 技术栈

| 用途 | 技术 |
|------|------|
| UI | PySide6 + Qt Widgets |
| 异步 | asyncio + qasync |
| 加密 | X25519 + ChaCha20-Poly1305 (cryptography) |
| 序列化 | msgpack |
| 日志 | structlog |
| 配置 | TOML |
| AI | LiteLLM + PaddleOCR + DeepSeek |
| 测试 | pytest + pytest-asyncio + pytest-qt |
| 检查 | ruff + mypy --strict |
| 最低版本 | Python 3.11 |

## 协议

自定义二进制协议，16 字节帧头：

```
┌────────┬────────┬──────┬─────────┬────────┬─────────┐
│ Magic  │Version │ Type │ Seq Num │ Length │ Payload │
│ 4 bytes│ 2 bytes│2bytes│ 4 bytes │ 4 bytes│ N bytes │
│ "UNIQ" │ 0x0001 │0x01  │monotonic│        │ msgpack │
└────────┴────────┴──────┴─────────┴────────┴─────────┘
```

端到端加密：X25519 ECDH 密钥协商 + ChaCha20-Poly1305 AEAD

## 设计文档

详见 `docs/design.md`
