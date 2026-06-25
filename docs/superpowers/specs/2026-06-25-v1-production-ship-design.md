# UniqoRemote v1.0 生产发布方案

> 状态: 已确认 | 日期: 2026-06-25 | 周期: ~7 周

---

## 1. 范围

首版目标：**可安装、可运行的 Windows 远程桌面客户端 + 服务端**。

- 局域网直连 IP 远程桌面
- 互联网 P2P 打洞 + 中继回退
- 键鼠远程控制
- 剪贴板同步
- 基础文件传输

### 不在此版

- AI (OCR/翻译/问答) — UI 入口占位
- 音频传输 — 留接口
- 聊天消息 — 留接口
- 会话录制 — 留接口
- 远程终端/CMD — 留接口
- 屏幕墙/多屏
- 隐私屏
- 权限审计
- CI/CD pipeline

---

## 2. 当前代码审计结论

### 2.1 可用模块 (无需大改)

| 模块 | 行数 | 测试 | 状态 |
|------|------|------|------|
| core/protocol.py | 89 | 11 passed | 就绪 |
| core/crypto.py | 62 | 11 passed | 就绪 |
| core/config.py | 83 | 3 passed | 就绪 |
| core/events.py | - | 5 passed | 就绪 |
| core/logging.py | - | 3 passed | 就绪 |
| core/channel.py | 27 | 3 passed | 就绪 |
| transport/udp.py | 63 | 2 passed | 就绪 |
| transport/tcp.py | 40 | 2 passed | 就绪 |
| transport/p2p.py | 86 | 4 passed | 就绪 |
| pipeline/capturer/gdi.py | 88 | ok | 就绪 |
| input/controller.py | - | 3 passed | 就绪 |
| session/router.py | 46 | ok | 就绪 |

### 2.2 需修改模块

| 模块 | 问题 | 严重程度 |
|------|------|----------|
| **ui/compose.py** | `derive_key()` 本地伪造密钥对——加密通道用远端不知道的密钥 | 致命 |
| **pipeline/encoder/ffmpeg.py** | `encode(frame_data: bytes)` 签名与 `Encoder.encode(frame: RawFrame)` 不匹配 | 致命 |
| **agent/__main__.py** | START_CAPTURE/INJECT_INPUT handler 只打日志不执行 | 致命 |
| **server/__main__.py** | 无 UDP/TCP 协议监听器，客户端无法注册 | 致命 |
| **session/manager.py** | 纯状态机无网络能力，不持有 MessageRouter | 高 |
| **ui/windows/main.py** | `_on_connect()` 不做网络连接，仅设变量 | 高 |
| **ui/windows/remote.py** | 空壳，不接收/解码/渲染帧 | 高 |
| **agent/ipc_server.py** | 使用 TCP 而非设计文档指定的命名管道 | 中 |

### 2.3 缺失模块

| 模块 | 说明 |
|------|------|
| server/protocol.py | UDP HELLO/NOTIFY/PUNCH 协议服务 |
| session/handshake.py | ECDH 密钥交换 + 会话密钥派生 |
| agent/pipeline_runner.py | 真实捕获→编码→IPC 推送循环 |
| ui/connect_flow.py | 连接流程编排 (resolve → punch → stream) |
| 打包脚本 | PyInstaller spec + FFmpeg 捆绑 |
| 安装脚本 | Inno Setup .iss |
| config.toml 模板 | 预设配置 + 说明 |

---

## 3. 关键设计修正

### 3.1 会话密钥交换 (修正 compose.py)

**旧代码 (错误):**
```python
def derive_key(key_pair):
    sk_a, pk_a = key_pair
    sk_b, pk_b = generate_key_pair()  # ← 本地生成，远端不知道
    return derive_session_key(sk_a, pk_b, ...)
```

**修正:** 密钥派生移入 SessionManager 握手流程，通过 rendezvous 交换公钥后派生。

```
Client A                    Server                     Client B
   │─ HELLO(pk_a, nonce_a) ─▶│◀─ HELLO(pk_b, nonce_b) ──│
   │◀─ NOTIFY(pk_b, addr_b) ─│── NOTIFY(pk_a, addr_a) ─▶│
   │                          │                          │
   │  session_key = BLAKE2b(  │  session_key = BLAKE2b(  │
   │    X25519(sk_a, pk_b) || │    X25519(sk_b, pk_a) || │
   │    nonce_a || nonce_b    │    nonce_a || nonce_b    │
   │  )                       │  )                       │
```

`compose.py` 不再调用 `derive_key()`。`EncryptedChannel` 在握手完成后才创建。

### 3.2 Encoder 接口对齐

`FfmpegEncoder` 改为实现 `Encoder` ABC 的完整签名：

```python
async def encode(self, frame: RawFrame) -> list[bytes]:
    raw = frame.data.tobytes()
    self._proc.stdin.write(raw)
    self._proc.stdin.flush()
    data = self._proc.stdout.read(65536)
    return [data] if data else []
```

### 3.3 Agent 进程真实实现

`agent/__main__.py` 的 `_handle_client`:

```
START_CAPTURE:
  1. 解析分辨率/编码参数
  2. 创建 Pipeline(GdiCapturer(), FfmpegEncoder())
  3. 启动捕获循环: capture → encode → conn.send("FRAME", data)
  4. 异步推送帧到 UI 进程

STOP_CAPTURE:
  1. pipeline.stop()
  2. 清理资源

INJECT_INPUT:
  1. InputController 执行键鼠注入

HEARTBEAT:
  1. 原样回传时间戳
```

### 3.4 Server 协议监听

新增 `server/protocol.py`:

- **UDP 监听** (端口 21116): 处理 HELLO、PUNCH 请求
- **消息路由**:
  - HELLO → 注册设备 + 公钥 + 地址，若对端在线则回复 NOTIFY
  - PUNCH → 告诉 A「B 在 addr_b 等你」，告诉 B「A 在 addr_a 等你」
  - PING/PONG → 心跳
- **TCP 监听** (端口 21117): RELAY 模式数据中继

`RendezvousManager` 与 `RelayServer` 由 ProtocolServer 组合调用。

### 3.5 Agent IPC 传输选择

| 选项 | 优势 | 劣势 |
|------|------|------|
| 命名管道 | 安全(ACL)、无端口冲突 | 实现复杂、Win32 API |
| TCP loopback | 简单、跨平台 | 端口可能冲突、防火墙可能拦截 |

**决策**: v1.0 沿用 TCP loopback (127.0.0.1:9510)。端口固定，agent 启动时若被占用则递增。v1.1 迁移到命名管道。

### 3.6 Agent 提权

Agent 需 SYSTEM/Admin 权限执行屏幕捕获和输入注入 (UIPI 绕过)。

- `compose.py` 中用 `ShellExecuteW(runas, ...)` 启动 agent 进程
- Agent 启动时检测权限，不足则弹 UAC
- 若用户拒绝提权，GDI 捕获仍可用 (低权限) 但输入注入受限

---

## 4. 模块依赖修正

修正后的 `compose.py`:

```python
def create_app(config_path: Path | None = None) -> tuple[MainWindow, QApplication]:
    config = load_config(config_path or Path("config.toml"))
    app = create_qapp()

    stun = StunClient()
    p2p_transport = P2PTransport()
    relay_transport = TcpTransport()
    session_mgr = SessionManager()  # 不再在此创建 channel
    decoder = FfmpegDecoder()
    agent_client = IpcClient(port=9510)
    ai_client = _create_ai_client(config)

    window = MainWindow(
        config=config,
        session_mgr=session_mgr,
        decoder=decoder,
        agent_client=agent_client,
        ai_client=ai_client,
        stun_client=stun,
        p2p_transport=p2p_transport,
        relay_transport=relay_transport,
    )
    return window, app
```

`MainWindow` 在用户点击「连接」时调用 `SessionManager.connect(device_id, server_addr, stun, transports)` → 内部完成 HELLO→NOTIFY→PUNCH→派生密钥→创建 EncryptedChannel。

---

## 5. 分阶段执行计划

### Phase 1: 基线修复 (第1周)

**目标:** 零 lint/type 错误，全部 135 测试通过。

| Task | 描述 | 文件 |
|------|------|------|
| T1.1 | 修复 mypy 13 错 + ruff 1 错 | 5 files |
| T1.2 | 安装 PySide6 + qasync，跑通 2 个 UI 测试 | pyproject.toml |
| T1.3 | 修复 `FfmpegEncoder.encode()` 签名 | encoder/ffmpeg.py |
| T1.4 | 删除 `compose.py:derive_key()`，`EncryptedChannel` 不在 compose 创建 | ui/compose.py |
| T1.5 | 写入 `config.toml` 模板，含所有字段 + 注释 | resources/config.toml |

**验证:** `pytest tests/ -v` 137 passed, `ruff check` 0, `mypy --strict` 0

### Phase 2: Agent 真实实现 (第1-2周)

**目标:** Agent 进程能真启动捕获→编码→通过 IPC 推送帧。

| Task | 描述 | 文件 |
|------|------|------|
| T2.1 | 实现 `agent/pipeline_runner.py`: 组装 Pipeline + 捕获循环 | 新文件 |
| T2.2 | 重写 `agent/__main__.py:_handle_client` 调用 PipelineRunner | agent/__main__.py |
| T2.3 | `IpcClient` 增加异步上下文管理器 (`async with`) | agent/ipc_server.py |
| T2.4 | 补全测试: 真实 GDI 捕获 + FFmpeg 编码 + IPC 帧传输 | tests/agent/ |
| T2.5 | `compose.py` 用 `runas` 启动 agent 进程 | ui/compose.py |

**验证:** `pytest tests/agent/ -v` 通过，Agent 独立运行可捕获桌面

### Phase 3: Session 联网 (第2-3周)

**目标:** 客户端通过 rendezvous 服务器完成设备发现和 P2P 建立。

| Task | 描述 | 文件 |
|------|------|------|
| T3.1 | 实现 `server/protocol.py`: UDP HELLO/NOTIFY/PUNCH 处理器 | 新文件 |
| T3.2 | `server/__main__.py` 启动 ProtocolServer + RelayServer | server/__main__.py |
| T3.3 | 实现 `session/handshake.py`: ECDH 密钥交换 + session_key 派生 | 新文件 |
| T3.4 | 重写 `SessionManager`: 注入 server_addr/stun/transports，新增 `connect()`/`disconnect()` | session/manager.py |
| T3.5 | `MainWindow._on_connect()` 调用 `session_mgr.connect(device_id)` | ui/windows/main.py |
| T3.6 | Dockerfile + docker-compose.yml 部署 server | 新文件 |
| T3.7 | 补全测试: HELLO→NOTIFY 握手、session 状态流转 | tests/server/, tests/session/ |

**验证:** server 在 Docker 启动，2 个 client 可注册并获知对方在线

### Phase 4: 局域网端到端 (第3-4周)

**目标:** 两台真机局域网内可互相远程桌面。

| Task | 描述 | 文件 |
|------|------|------|
| T4.1 | 实现帧流接收循环: router.on(VIDEO) → decoder → QPixmap 渲染 | ui/windows/remote.py |
| T4.2 | 实现输入事件发送: 鼠标/键盘事件 → msgpack → channel.send(INPUT) | ui/windows/remote.py |
| T4.3 | 实现输入坐标缩放: 远程分辨率 ≠ 本地窗口尺寸时换算 | ui/windows/remote.py |
| T4.4 | Agent 端接收 INPUT 消息 → InputController 执行 | agent/__main__.py |
| T4.5 | P2P 打洞关键帧同步: 双方同时发 punch + 等待对方帧 | transport/p2p.py |
| T4.6 | FFmpeg 不可用时的用户提示 (QMessageBox) | ui/windows/main.py |
| T4.7 | 局域网 E2E 手动测试 + 性能调节 | 无代码 |

**验证:** 2 台真机局域网 30fps H.264 画面流畅，键鼠延迟 < 50ms

### Phase 5: 互联网 E2E (第4-5周)

**目标:** 公网环境下 P2P 打洞成功，relay 回退可用。

| Task | 描述 | 文件 |
|------|------|------|
| T5.1 | 实现 relay 回退: punch 3 次失败 → 切换 TCP relay | transport/p2p.py |
| T5.2 | Relay 模式帧封装 (RELAY 消息类型 + session_id 前缀) | core/protocol.py |
| T5.3 | 动态码率: 根据丢包率调整 FFmpeg 码率 | pipeline/encoder/ffmpeg.py |
| T5.4 | 心跳机制: PING/PONG 5 秒间隔，20 秒超时断连 | session/manager.py |
| T5.5 | 客户端断线重连 (保留 session_id，复用已派生 session_key) | session/manager.py |
| T5.6 | 公网点对点测试 + relay 回退测试 | 无代码 |

**验证:** P2P 成功率 >70%，relay 回退延迟 < 200ms

### Phase 6: 剪贴板 + 文件传输 (第5-6周)

**目标:** 基础剪贴板同步和文件传输可用。

| Task | 描述 | 文件 |
|------|------|------|
| T6.1 | 实现 Windows 剪贴板监听 (Win32 API + Qt) | session/clipboard.py |
| T6.2 | 剪贴板文本同步: 检测变化 → 编码 → CLIPBOARD 消息 | session/clipboard.py |
| T6.3 | `MainWindow._on_sync_clipboard` 真实调用 session API | ui/windows/main.py |
| T6.4 | 文件传输基础: 单文件分块发送 + 接收校验 | session/file_transfer.py |
| T6.5 | `FileManagerDialog` 浏览本地 + 选择发送 | ui/windows/file_manager.py |

**验证:** 文本剪贴板双向同步，小文件 (<10MB) 可传输

### Phase 7: 打包发布 (第6-7周)

**目标:** 一键安装包，干净 Windows 可启动使用。

| Task | 描述 | 文件 |
|------|------|------|
| T7.1 | PyInstaller spec: 含 PySide6 + cryptography + msgpack + numpy | scripts/uniqoremote.spec |
| T7.2 | FFmpeg 捆绑: 拷贝 ffmpeg.exe 到安装目录 bin/ | scripts/bundle.py |
| T7.3 | config.toml 首次启动自动生成 (含持久化 device_id) | core/config.py |
| T7.4 | 日志落盘: `%APPDATA%/UniqoRemote/logs/` 按天轮转 | core/logging.py |
| T7.5 | Inno Setup 安装脚本: 桌面快捷方式 + 卸载入口 | scripts/installer.iss |
| T7.6 | 资源: 应用图标 (ico) + 任务栏图标 | resources/ |
| T7.7 | 启动脚本: 一键打包 PS1 脚本 | scripts/build.ps1 |

**验证:** 安装包在新装 Win10/Win11 上可启动、可注册、可远程

---

## 6. Phase 间 Gate

进入下一 Phase 前必须:

- [ ] 本 Phase 全部测试通过
- [ ] `ruff check` 全项目 0
- [ ] `mypy --strict` 全项目 0
- [ ] `pytest tests/ -v` 全量通过
- [ ] 无已知崩溃场景

---

## 7. 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| NAT 类型对称 (Symmetric) 打洞失败率高 | 中 | 所有此类 NAT 走 relay | 自动检测 NAT 类型，快速降级 |
| FFmpeg 用户未安装 | 高 | 无法编码/解码 | 捆绑 ffmpeg.exe + 首次启动检测 |
| PyInstaller 打包体积过大 (>100MB) | 高 | 下载慢 | Nuitka 后续优化；首版接受 |
| Agent 提权被拒绝 | 中 | 输入注入失效 | GDI 捕获仍可用；用户提示 |
| qasync 与 asyncio 事件循环冲突 | 低 | UI 卡死 | 单元测试已通过；增加 E2E 压力测试 |
| 多显示器坐标偏移 | 中 | 鼠标点击错位 | Phase 4 增加多显示器测试用例 |

---

## 8. 关键接口约定

### Encoder

```python
class Encoder(ABC):
    async def start(self, width: int, height: int, fps: int, codec: str) -> None: ...
    async def encode(self, frame: RawFrame) -> list[EncodedPacket]: ...
    async def request_keyframe(self) -> None: ...
    async def stop(self) -> None: ...
```

### SessionManager (修正后)

```python
class SessionManager:
    def __init__(self) -> None: ...
    async def connect(
        self, remote_device_id: str, server_addr: tuple[str, int],
        stun: StunClient, p2p: P2PTransport, relay: TcpTransport,
    ) -> Session: ...
    async def disconnect(self) -> None: ...
    def on_frame(self, handler: Callable[[bytes], None]) -> None: ...
    async def send_input(self, event: InputEvent) -> None: ...
    async def send_clipboard(self, text: str) -> None: ...
    async def send_file(self, path: Path) -> None: ...
```

### IpcClient (修正后)

```python
class IpcClient:
    async def connect(self) -> None: ...
    async def start_capture(self, width: int, height: int, fps: int, codec: str) -> None: ...
    async def stop_capture(self) -> None: ...
    async def inject_input(self, event: InputEvent) -> None: ...
    async def on_frame(self, handler: Callable[[bytes], None]) -> None: ...
    async def close(self) -> None: ...
```
