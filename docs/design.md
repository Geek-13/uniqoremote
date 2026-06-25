# UniqoRemote 项目总体设计文档

> 版本: 1.0 | 生成日期: 2025-06-25

---

## 1. 项目概述

Python + PySide6 全新远程桌面系统，包含客户端和服务端，
同时集成向日葵/ToDesk 的特色功能及 AI 能力。

### 1.1 定位

| 项 | 决策 |
|----|------|
| 协议 | 全新自研，不兼容 RustDesk |
| 平台 | 仅 Windows (后续扩展) |
| UI | PySide6 + Qt Widgets |
| 许可 | LGPL (PySide6) |

### 1.2 功能清单

**核心功能:**
- 远程桌面 (P2P 直连 + 中继回退)
- 键鼠远程控制
- 剪贴板同步
- 文件传输
- 音频传输

**向日葵/ToDesk 特色:**
- 远程文件管理器
- 远程终端/CMD
- 屏幕墙/多屏切换
- 聊天消息
- 会话录制
- 隐私屏/远程黑屏

**AI 功能 (三期):**
- V1: 屏幕内容 OCR + 问答
- V2: 实时翻译 + 异常检测
- V3: 故障诊断 + 会议纪要

---

## 2. 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| UI | PySide6 + Qt Widgets | LGPL，原生 Windows 外观 |
| 异步 | asyncio + qasync | 桥接 Qt 事件循环 |
| 视频编码 | FFmpeg 子进程 (stdin/stdout pipe) | 替代 PyAV，兼容性好 |
| 屏幕捕获 | WGC (winrt) → DXGI (后续) → GDI (回退) | 三级降级策略 |
| 输入控制 | ctypes + SendInput | 无第三方依赖 |
| 加密 | cryptography (PyCA) | X25519 + ChaCha20-Poly1305 |
| 序列化 | msgpack | 紧凑二进制 |
| AI | LiteLLM + PaddleOCR + ollama | DeepSeek 模型 |
| 测试 | pytest + pytest-asyncio + pytest-qt | 标准三件套 |
| 日志 | structlog | 结构化日志 |
| 配置 | TOML (stdlib tomllib) | Python 3.11+ 内置 |
| 打包 | PyInstaller (开发) → Nuitka + Inno Setup (发布) | 渐进优化 |

### 2.1 明确不用的技术

| 技术 | 原因 |
|------|------|
| protobuf | 需编译 .proto，msgpack 更轻 |
| WebRTC | 引入浏览器栈，自建通道更可控 |
| ZeroMQ/nng | IPC 太重，命名管道足够 |
| PyAV | Windows wheel 兼容性差 |
| PyO3/Rust 扩展 | 保留纯 Python 可维护性优势 |

---

## 3. 架构

### 3.1 分层架构

```
ui ──────▶ session ──────▶ core
 │              │             │
 │              ▼             ▼
 │           pipeline     transport (接口)
 │              │             │
 │              ▼             │
 └────────── agent ◀──────────┘
```

**依赖规则:** 内层不能 import 外层，同层不直接依赖，通过上层协调。

### 3.2 双进程模型

| 进程 | 权限 | 职责 | 入口 |
|------|------|------|------|
| UI 进程 | user | 界面渲染、网络通信、会话管理 | `python -m uniqoremote.ui` |
| Agent 进程 | system | 屏幕捕获、输入注入、音频采集 | `python -m uniqoremote.agent` |

**通信方式:** 命名管道 (Windows Named Pipe)，消息格式与网络层一致 (msgpack)。

**分离理由:**
- 屏幕捕获和输入注入需要 SYSTEM 权限 (UIPI 绕过)
- UI 进程崩溃不影响远程会话
- 安全隔离: UI 进程不持有捕获权限

### 3.3 组合根

`ui/compose.py` 是唯一的依赖组装点，所有具体实现在此注入:

```python
def create_app(config: Config) -> QApplication:
    transport = UdpTransport()
    channel = EncryptedChannel(transport, key_pair)
    router = MessageRouter(channel)
    session_mgr = SessionManager(router)
    decoder = FfmpegDecoder()
    agent_client = IpcClient(config.agent_pipe)
    ai_client = DeepSeekClient(config.ai_api_key) if config.ai_enabled else None
    return MainWindow(session_mgr, decoder, agent_client, ai_client)
```

---

## 4. 项目结构

```
uniqoremote/
├── pyproject.toml
├── AGENTS.md
├── docs/
│   └── design.md
├── src/
│   ├── core/                     # 基础层 — 零业务依赖
│   │   ├── __init__.py
│   │   ├── protocol.py           # 消息类型 + msgpack
│   │   ├── crypto.py             # X25519 + ChaCha20-Poly1305
│   │   ├── channel.py            # 加密通道
│   │   ├── config.py             # TOML 配置
│   │   ├── events.py             # 内部事件 dataclass
│   │   └── logging.py            # structlog
│   │
│   ├── transport/                # 传输层 — 纯 socket
│   │   ├── __init__.py
│   │   ├── base.py               # Transport ABC
│   │   ├── udp.py                # UDP 打洞直连
│   │   └── tcp.py                # TCP 中继回退
│   │
│   ├── pipeline/                 # 采集管道 — 捕获+编码
│   │   ├── __init__.py
│   │   ├── base.py               # Pipeline ABC
│   │   ├── capturer/
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # Capturer ABC
│   │   │   ├── wgc.py            # Windows Graphics Capture
│   │   │   ├── dxgi.py           # DXGI (后续)
│   │   │   └── gdi.py            # GDI 回退
│   │   ├── encoder/
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # Encoder ABC
│   │   │   └── ffmpeg.py         # FFmpeg 子进程编码
│   │   ├── decoder/
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # Decoder ABC
│   │   │   └── ffmpeg.py         # FFmpeg 子进程解码
│   │   └── pipeline.py           # 组装: Capturer → Encoder → Frame
│   │
│   ├── input/                    # 输入控制
│   │   ├── __init__.py
│   │   ├── base.py               # InputController ABC
│   │   ├── keyboard.py           # SendInput 键盘
│   │   ├── mouse.py              # SendInput 鼠标
│   │   └── controller.py         # 统一控制器
│   │
│   ├── session/                  # 会话服务
│   │   ├── __init__.py
│   │   ├── manager.py            # 会话生命周期
│   │   ├── clipboard.py          # 剪贴板同步
│   │   ├── file_transfer.py      # 文件传输
│   │   ├── audio.py              # 音频传输
│   │   ├── chat.py               # 聊天消息
│   │   ├── recording.py          # 会话录制
│   │   └── router.py             # 消息路由分发
│   │
│   ├── agent/                    # 本地代理进程 (系统权限)
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── ipc_server.py         # 命名管道服务端
│   │   └── heartbeat.py          # 心跳监控
│   │
│   ├── ui/                       # UI 进程 (用户权限)
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── app.py                # QApplication 入口
│   │   ├── ipc_client.py         # 命名管道客户端
│   │   ├── compose.py            # 组合根 (依赖注入)
│   │   └── windows/
│   │       ├── __init__.py
│   │       ├── main.py           # 主窗口
│   │       ├── remote.py         # 远程画面
│   │       ├── devices.py        # 设备列表
│   │       ├── settings.py       # 设置
│   │       ├── file_manager.py   # 远程文件管理
│   │       └── terminal.py       # 远程终端
│   │
│   ├── ai/                       # AI 子系统 (可选)
│   │   ├── __init__.py
│   │   ├── client.py             # DeepSeek (LiteLLM)
│   │   ├── ocr.py                # PaddleOCR
│   │   ├── translate.py          # 实时翻译
│   │   ├── assistant.py          # 屏幕问答
│   │   └── monitor.py            # 异常检测
│   │
│   └── server/                   # 云端服务器 (独立部署)
│       ├── __init__.py
│       ├── __main__.py
│       ├── rendezvous/
│       │   ├── __init__.py
│       │   └── manager.py        # ID 分配 + 打洞协调
│       ├── relay/
│       │   ├── __init__.py
│       │   └── relay.py          # 流量中继 + 带宽控制
│       └── admin/
│           ├── __init__.py
│           └── web.py            # Web 管理面板 (FastAPI)
│
├── tests/                        # 镜像 src 结构
│   ├── conftest.py
│   ├── core/
│   ├── transport/
│   ├── pipeline/
│   ├── input/
│   ├── session/
│   ├── agent/
│   ├── ui/
│   └── ai/
│
├── resources/                    # 图标、字体、许可证
└── scripts/                      # 构建/打包脚本
```

---

## 5. 协议设计

### 5.1 帧格式

```
┌──────────┬──────────┬──────────┬───────────┬───────────┬──────────────────┐
│  Magic   │ Version  │   Type   │  Seq Num  │  Length   │    Payload       │
│  4 bytes │  2 bytes │  2 bytes │  4 bytes  │  4 bytes  │   N bytes        │
│  "UNIQ"  │  0x0001  │  see 5.2 │  monotonic│           │   (msgpack)      │
└──────────┴──────────┴──────────┴───────────┴───────────┴──────────────────┘
```

Header 固定 16 字节，Payload 为 msgpack 编码。

### 5.2 消息类型

| Type | 名称 | 方向 | Seq? | 用途 |
|------|------|------|------|------|
| 0x01 | HELLO | C↔S | No | 握手: 设备ID, 公钥, 能力协商 |
| 0x02 | PUNCH | C→S | No | 请求 P2P 打洞 |
| 0x03 | NOTIFY | S→C | No | 服务端通知: 对端上线/公钥 |
| 0x04 | RELAY | C↔S↔C | Yes | 中继模式数据 (含内部子帧) |
| 0x05 | STREAM | C↔C | Yes | P2P 直连数据 |
| 0x06 | CONTROL | C↔C | Yes | 控制指令: 分辨率/编码/隐私屏 |
| 0x07 | CLIPBOARD | C↔C | Yes | 剪贴板内容 |
| 0x08 | FILE | C↔C | Yes | 文件传输块 |
| 0x09 | CHAT | C↔C | Yes | 聊天消息 |
| 0x0A | AUDIO | C↔C | Yes | 音频帧 |
| 0x0B | VIDEO | C↔C | Yes | 视频帧 |
| 0x0C | INPUT | C↔C | Yes | 键鼠事件 |
| 0x0D | ERROR | C↔S↔C | Yes | 错误报告 (code + message) |
| 0x0E | PING | C↔S↔C | No | 心跳请求 |
| 0x0F | PONG | C↔S↔C | No | 心跳响应 |
| 0x10 | BYE | C↔S↔C | No | 断开连接 |

### 5.3 HELLO 消息结构

```python
@dataclass
class HelloPayload:
    device_id: str
    public_key: bytes         # X25519 公钥 32 bytes
    version: str              # "1.0.0"
    capabilities: dict        # {"codec": ["h264","h265"], "max_res": "1920x1080", ...}
    nonce: bytes              # 随机数 24 bytes
```

### 5.4 错误码

| Code | 名称 | 描述 |
|------|------|------|
| 0x01 | INVALID_FRAME | 帧格式错误 |
| 0x02 | VERSION_MISMATCH | 协议版本不兼容 |
| 0x03 | AUTH_FAILED | 密钥交换失败 |
| 0x04 | DEVICE_OFFLINE | 对端不在线 |
| 0x05 | RELAY_FULL | 中继带宽满 |
| 0x06 | PUNCH_FAILED | 打洞失败 |
| 0x07 | TIMEOUT | 操作超时 |
| 0x08 | INTERNAL | 内部错误 |

### 5.5 加密通道

```
Client A                        Server                        Client B
   │                              │                              │
   │── HELLO(id_a, pk_a) ───────▶│◀── HELLO(id_b, pk_b) ────────│
   │◀── NOTIFY(id_b, pk_b) ──────│── NOTIFY(id_a, pk_a) ───────▶│
   │                              │                              │
   │  ════════ P2P 打洞 / 中继建立连接 ════════                   │
   │                              │                              │
   │  shared = X25519(sk_a, pk_b) = X25519(sk_b, pk_a)          │
   │  session_key = BLAKE2b(shared || nonce_a || nonce_b)       │
   │                              │                              │
   │◀══════ STREAM {ChaCha20-Poly1305 AEAD} ═══════════════════▶│
```

- 密钥协商: X25519 ECDH，服务端不持有私钥 (E2EE)
- 对称加密: ChaCha20-Poly1305 AEAD (encrypt-then-MAC)
- 会话密钥派生: BLAKE2b(shared_secret || nonce_a || nonce_b)
- 序列号用于 Anti-Replay 检测 + Nonce 构造

### 5.6 连接流程

```
Client A ──HELLO──▶ Server ◀──HELLO── Client B
Client A ◀─NOTIFY── Server ──NOTIFY─▶ Client B
Client A ──PUNCH──▶ Server ◀──PUNCH── Client B
   │                  │                  │
   ├── UDP ───────────┼────────── UDP ──┤
   │  (hole punching with server hints) │
   │                  │                  │
   ├── STREAM (encrypted) ─────────────▶│
   │◀─ STREAM (encrypted) ──────────────┤
   │                  │                  │
   └──── P2P 直连建立 ──────────────────┘
   
   Fallback:
   Client A ──RELAY──▶ Server ──RELAY──▶ Client B
```

---

## 6. IPC 设计 (Agent ↔ UI)

### 6.1 通信方式

| 项 | 选择 |
|----|------|
| 传输 | Windows Named Pipe (`\\.\pipe\uniqoremote_agent`) |
| 序列化 | msgpack (与网络层统一) |
| 模式 | 请求-响应 (req_id 匹配) + 推送 (帧流) |

### 6.2 IPC 消息类型

| Type | 方向 | 说明 |
|------|------|------|
| START_CAPTURE | UI→Agent | 启动屏幕捕获 (分辨率、编码参数) |
| STOP_CAPTURE | UI→Agent | 停止捕获 |
| FRAME | Agent→UI | 编码后的视频帧 |
| INJECT_INPUT | UI→Agent | 注入键鼠事件 |
| AUDIO_PLAY | Agent→UI | 远端音频数据 |
| HEARTBEAT | 双向 | 心跳 |
| ERROR | Agent→UI | 捕获/编码错误 |

### 6.3 Agent 生命周期

```
UI 进程启动 → 以管理员身份启动 Agent 进程
Agent 创建命名管道 → 等待 UI 连接
UI 连接 → 握手 (版本检查)
UI 发送 START_CAPTURE → Agent 开始捕获
循环: Agent 推送 FRAME → UI 渲染
UI 发送 STOP_CAPTURE → Agent 停止
UI 断开 → Agent 退出
```

---

## 7. Pipeline 设计

### 7.1 数据流

```
GPU Framebuffer
      │
      ▼
┌─────────────┐
│  Capturer    │  WGC / DXGI / GDI → RawFrame (numpy BGRA)
└──────┬──────┘
       │ raw_frame: numpy.ndarray (height, width, 4)
       ▼
┌─────────────┐
│  Encoder     │  FFmpeg subprocess → H.264/H.265 bitstream
└──────┬──────┘
       │ encoded: bytes (NAL units)
       ▼
┌─────────────┐
│  Channel     │  encrypt → send over transport
└──────────────┘

               ── Network ──▶

┌─────────────┐
│  Decoder     │  FFmpeg subprocess → DecodedFrame (numpy BGRA)
└──────┬──────┘
       │ decoded_frame: numpy.ndarray (height, width, 4)
       ▼
┌─────────────┐
│  Renderer    │  QPixmap → QLabel 显示
└─────────────┘
```

### 7.2 Capturer 接口

```python
class Capturer(ABC):
    @abstractmethod
    async def start(self, monitor: int = 0) -> None: ...

    @abstractmethod
    async def capture(self) -> RawFrame: ...  # RawFrame = dataclass(data: np.ndarray, width, height, pts)

    @abstractmethod
    async def stop(self) -> None: ...

    @property
    @abstractmethod
    def supported_resolutions(self) -> list[tuple[int, int]]: ...
```

### 7.3 Encoder 接口

```python
class Encoder(ABC):
    @abstractmethod
    async def start(self, width: int, height: int, fps: int, codec: str) -> None: ...

    @abstractmethod
    async def encode(self, frame: RawFrame) -> list[bytes]: ...  # NAL units

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def request_keyframe(self) -> None: ...
```

### 7.4 Decoder 接口

```python
class Decoder(ABC):
    @abstractmethod
    async def start(self, width: int, height: int, codec: str) -> None: ...

    @abstractmethod
    async def decode(self, data: bytes) -> DecodedFrame: ...  # DecodedFrame = dataclass(data: np.ndarray, width, height, pts)

    @abstractmethod
    async def stop(self) -> None: ...
```

### 7.5 编码参数

| 场景 | 编码 | 码率 | 帧率 |
|------|------|------|------|
| 局域网 | H.264 | 10-20 Mbps | 30-60 |
| 公网 P2P | H.264 | 2-5 Mbps | 15-30 |
| 中继回退 | H.265 | 1-3 Mbps | 10-15 |
| 隐私屏 | H.264 | 0.5 Mbps | 5 | (仅黑屏占位帧)

### 7.6 FFmpeg 命令模板

```python
# 编码器
[
    "ffmpeg",
    "-f", "rawvideo",
    "-pix_fmt", "bgra",
    "-s", f"{width}x{height}",
    "-r", str(fps),
    "-i", "pipe:0",              # stdin 接收 raw frame
    "-c:v", "h264_amf",          # AMD AMF 硬编
    "-b:v", f"{bitrate}k",
    "-g", str(fps * 2),          # GOP = 2秒
    "-preset", "fast",
    "-f", "h264",
    "pipe:1"                      # stdout 输出 NAL
]

# 解码器
[
    "ffmpeg",
    "-f", "h264",
    "-i", "pipe:0",
    "-f", "rawvideo",
    "-pix_fmt", "bgra",
    "pipe:1"
]
```

---

## 8. 会话管理

### 8.1 状态机

```
IDLE ──▶ CONNECTING ──▶ HANDSHAKING ──▶ ACTIVE ──▶ CLOSING ──▶ IDLE
                          │                │
                          └── ERROR ───────┘
```

### 8.2 SessionManager

```python
class SessionManager:
    async def connect(self, device_id: str) -> Session: ...
    async def disconnect(self, session: Session) -> None: ...
    async def send_input(self, session: Session, event: InputEvent) -> None: ...
    async def on_frame(self, session: Session, handler: Callable) -> None: ...
    async def start_recording(self, session: Session, path: str) -> None: ...
    async def stop_recording(self, session: Session) -> None: ...
```

---

## 9. AI 子系统

### 9.1 架构

```
Remote Frame
     │
     ▼
┌──────────┐     ┌──────────────┐
│ OCR      │────▶│ DeepSeek     │
│ PaddleOCR│     │ (LiteLLM)    │
└──────────┘     └──────┬───────┘
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
    ┌─────────┐  ┌──────────┐  ┌──────────┐
    │ 问答    │  │ 翻译     │  │ 纪要     │
    │ Q&A     │  │ Translate│  │ Summary  │
    └─────────┘  └──────────┘  └──────────┘
```

### 9.2 模型配置

```python
AI_CONFIG = {
    "providers": {
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "models": {
                "chat": "deepseek-chat",
                "vision": "deepseek-vl2",       # 视觉模型 (OCR 辅助)
            }
        }
    },
    "local": {
        "ocr": "PaddleOCR",                     # 离线 OCR
        "stt": None,                            # 后续: Whisper
    }
}
```

### 9.3 AI 客户端接口

```python
class AIClient(ABC):
    @abstractmethod
    async def ask(self, prompt: str, image: bytes | None = None) -> str: ...

    @abstractmethod
    async def ocr(self, image: bytes) -> str: ...

    @abstractmethod
    async def translate(self, text: str, target_lang: str) -> str: ...

    @abstractmethod
    async def summarize(self, context: str) -> str: ...
```

---

## 10. 测试策略

### 10.1 测试金字塔

```
         ┌──────┐
         │ E2E  │  5%  - 完整远程会话流程
         ├──────┤
         │ 集成 │  25% - IPC/网络/编码管道
         ├──────┤
         │ 单元 │  70% - 协议/加密/消息路由
         └──────┘
```

### 10.2 各层测试方式

| 层 | 测试工具 | Mock 策略 |
|----|---------|----------|
| core | pytest | 无 mock，纯函数测试 |
| transport | pytest-asyncio | Mock socket，注入丢包/延迟 |
| pipeline | pytest-asyncio | 测试视频文件回放 |
| input | pytest | 验证 SendInput 结构体 |
| session | pytest-asyncio | Mock channel |
| ui | pytest-qt | qtbot 交互测试 |
| agent | pytest-asyncio | Mock IPC client |
| ai | pytest | Mock LiteLLM, 录播-回放模式 |

### 10.3 CI 测试矩阵

```yaml
# .github/workflows/test.yml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
    test-group: [core, transport, pipeline, input, session, ui, ai]
```

### 10.4 关键测试场景

1. 协议编解码正确性 (正常 + 边界 + 损坏数据)
2. 加密通道: 加密后对端能正确解密
3. 序列号单调递增，重放帧被拒绝
4. 打洞模拟: X 次重试后降级中继
5. 编码管道: 丢帧/关键帧请求/动态码率
6. IPC: 断连重连、乱序到达
7. UI: 远程画面渲染、输入事件坐标转换
8. AI: 截屏→OCR→问答 完整链路 (录播模式)

---

## 11. 开发路线图

### Phase 1: 基础框架 (第 1-2 周)

**目标:** 可运行的骨架，协议层 + 传输层 + 测试框架

| 任务 | 产出 | 测试 |
|------|------|------|
| pyproject.toml + 项目骨架 | 可安装的空包 | 导入测试 |
| core/protocol.py | 消息定义 + msgpack 编解码 | 单元测试 |
| core/crypto.py | X25519 + ChaCha20-Poly1305 | 加解密往返测试 |
| core/config.py | TOML 配置加载 | 单元测试 |
| core/events.py | 内部事件类型 | 单元测试 |
| core/logging.py | structlog 配置 | 冒烟测试 |
| transport/base.py + udp.py + tcp.py | socket 封装 | 环回测试 |
| core/channel.py | 加密通道组装 | 端到端测试 |

### Phase 2: Agent 进程 (第 3-4 周)

**目标:** 能捕获屏幕并编码

| 任务 | 产出 | 测试 |
|------|------|------|
| pipeline/capturer/gdi.py | GDI 回退方案 | 截图验证 |
| pipeline/capturer/wgc.py | WGC 捕获 | 截图+帧率测试 |
| pipeline/encoder/ffmpeg.py | FFmpeg 编码 | 视频文件验证 |
| pipeline/pipeline.py | 捕获→编码管道 | 管道吞吐量测试 |
| input/keyboard.py + mouse.py | SendInput 封装 | 结构体验证 |
| agent/__main__.py + ipc_server.py | Agent 可独立运行 | IPC 协议测试 |

### Phase 3: 网络连通 (第 5-6 周)

**目标:** 两台机器能 P2P 通信传输视频

| 任务 | 产出 | 测试 |
|------|------|------|
| server/rendezvous/ | ID 分配 + 公钥交换 | 并发连接测试 |
| transport/udp.py 完善 | NAT 打洞逻辑 | 模拟 NAT 测试 |
| server/relay/ | 中继转发 | 吞吐量+延迟测试 |
| session/manager.py | 完整连接生命周期 | 集成测试 |

### Phase 4: 基础 UI (第 7-8 周)

**目标:** 可视化的远程桌面

| 任务 | 产出 | 测试 |
|------|------|------|
| ui/compose.py | 依赖注入组装 | 集成测试 |
| ui/windows/main.py | 主窗口 (设备列表) | qtbot 测试 |
| ui/windows/remote.py | 远程画面渲染 | qtbot 测试 |
| session/clipboard.py | 剪贴板同步 | 单元测试 |

### Phase 5: 会话增强 (第 9-10 周)

**目标:** 文件传输、聊天、录制

| 任务 | 产出 |
|------|------|
| session/file_transfer.py | 断点续传 |
| session/chat.py | 消息收发 |
| session/recording.py | 录制成 MP4 |
| ui/windows/file_manager.py | 远程文件管理 |
| ui/windows/terminal.py | 远程 CMD |

### Phase 6: AI 集成 (第 11-12 周)

**目标:** OCR 问答、实时翻译

| 任务 | 产出 |
|------|------|
| ai/client.py | DeepSeek 客户端 |
| ai/ocr.py | PaddleOCR 封装 |
| ai/assistant.py | 屏幕问答 |
| ai/translate.py | 实时字幕翻译 |

### Phase 7: 打磨发布 (第 13-14 周)

| 任务 | 产出 |
|------|------|
| 性能优化 | DXGI 捕获、硬件编码 |
| 隐私屏 | viewport 黑屏控制 |
| 屏幕墙 | 多显示器切换 |
| AI 监控 | 异常行为检测 |
| 打包脚本 | PyInstaller → Nuitka + Inno Setup |

---

## 12. 构建与部署

### 12.1 开发环境

```powershell
# 创建虚拟环境
python -m venv .venv
.venv\Scripts\Activate.ps1

# 安装开发依赖
pip install -e ".[dev,test]"

# 运行测试
pytest tests/ -v --cov=src
```

### 12.2 pyproject.toml 依赖声明

```toml
[project]
name = "uniqoremote"
version = "0.1.0"
requires-python = ">=3.11"

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio", "pytest-qt", "pytest-cov", "ruff", "mypy"]
ui = ["PySide6", "qasync"]
ai = ["litellm", "paddleocr"]

[project.scripts]
uniqoremote = "uniqoremote.ui.__main__:main"
uniqoremote-agent = "uniqoremote.agent.__main__:main"
uniqoremote-server = "uniqoremote.server.__main__:main"
```

### 12.3 打包

```powershell
# 开发阶段
pyinstaller --onefile --name uniqoremote src/uniqoremote/ui/__main__.py

# 发布阶段
nuitka --standalone --windows-console-mode=disable src/uniqoremote/ui/__main__.py
# 然后用 Inno Setup 制作安装包
```
