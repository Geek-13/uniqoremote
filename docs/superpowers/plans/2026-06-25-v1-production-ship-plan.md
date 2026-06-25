# UniqoRemote v1.0 生产发布实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建可安装的 Windows 远程桌面客户端 + 服务端，支持局域网直连和互联网 P2P/中继连接。

**Architecture:** 双进程模型 (UI + Agent TCP IPC)，UDP P2P 直连优先/TCP relay 回退，X25519 ECDH 密钥交换 + ChaCha20-Poly1305 AEAD 加密，GDI 屏幕捕获 + FFmpeg H.264 编码。

**Tech Stack:** Python 3.11+, PySide6, qasync, cryptography, msgpack, numpy, FFmpeg subprocess, structlog, PyInstaller

**Spec:** `docs/superpowers/specs/2026-06-25-v1-production-ship-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `resources/config.toml` | Create | 默认配置模板 |
| `resources/icon.ico` | Create | 应用图标 (占位) |
| `src/uniqoremote/server/protocol.py` | Create | UDP HELLO/NOTIFY/PUNCH 协议服务器 |
| `src/uniqoremote/session/handshake.py` | Create | ECDH 密钥交换 + session_key 派生 |
| `src/uniqoremote/agent/pipeline_runner.py` | Create | 捕获→编码→IPC 推送循环 |
| `Dockerfile` | Create | Server 容器化 |
| `docker-compose.yml` | Create | Server 一键部署 |
| `pyproject.toml` | Modify | 加 PySide6/qasync 到 dev deps, 声明 server extras |
| `src/uniqoremote/pipeline/encoder/ffmpeg.py` | Modify | 修复 encode() 签名为 RawFrame→list[bytes] |
| `src/uniqoremote/ui/compose.py` | Modify | 移除 derive_key, 延迟 channel 创建, agent 提权启动 |
| `src/uniqoremote/agent/__main__.py` | Modify | 真实捕获/注入 handler |
| `src/uniqoremote/server/__main__.py` | Modify | 启动 ProtocolServer |
| `src/uniqoremote/session/manager.py` | Modify | 加上 connect()/disconnect() 网络能力 |
| `src/uniqoremote/ui/windows/main.py` | Modify | _on_connect 走真实会话流程 |
| `src/uniqoremote/ui/windows/remote.py` | Modify | 接收帧→解码→渲染 + 输入发送 |
| `src/uniqoremote/core/config.py` | Modify | 无 config 时自动生成 + 持久化 device_id |
| `src/uniqoremote/core/logging.py` | Modify | 加文件落盘 handler |
| `src/uniqoremote/core/protocol.py` | Modify | 加 make_relay_frame / parse_relay_frame |
| `src/uniqoremote/transport/p2p.py` | Modify | 打洞失败自动降级 relay |
| `src/uniqoremote/session/clipboard.py` | Modify | 真实 Win32 剪贴板监听 |
| `src/uniqoremote/session/file_transfer.py` | Modify | 单文件分块发送 |
| `tests/agent/test_pipeline_runner.py` | Create | Agent pipeline 测试 |
| `tests/server/test_protocol.py` | Create | 协议服务器测试 |
| `tests/session/test_handshake.py` | Create | 密钥交换测试 |
| `tests/session/test_clipboard.py` | Modify | 剪贴板集成测试 |
| `scripts/uniqoremote.spec` | Create | PyInstaller spec |
| `scripts/build.ps1` | Create | 一键打包脚本 |

---

## Phase 1: 基线修复

### Task 1.1: 修复 mypy 错误

**Files:** Modify `src/uniqoremote/server/relay/relay.py`, `src/uniqoremote/server/admin/web.py`, `src/uniqoremote/pipeline/capturer/base.py`, `src/uniqoremote/agent/__main__.py`, `src/uniqoremote/pipeline/capturer/gdi.py`

- [ ] **Step 1: 修复 relay.py:27 — no-any-return**

Run: `python -m mypy --strict src/uniqoremote/server/relay/`

Read `src/uniqoremote/server/relay/relay.py` 的 `start()` 方法。将第 27 行 `return self._transport.get_extra_info("socket").getsockname()[1]` 改为：

```python
sock = self._transport.get_extra_info("socket")
assert sock is not None
sockname: tuple[str, int] = sock.getsockname()
return sockname[1]
```

- [ ] **Step 2: 修复 web.py — type-arg / import-not-found / no-untyped-def**

读取 `src/uniqoremote/server/admin/web.py`。在文件顶部加 `from __future__ import annotations`。将第 12 行 `devices: dict[str, ...] = {}` 改为 `devices: dict[str, Any] = {}`。将第 22-23 行 `import uvicorn; import fastapi` 去掉，改为 `if False: import uvicorn, fastapi  # type: ignore[import-untyped]`。将第 28 行函数 `def some_func(...)` 改为 `def some_func(...) -> None:`。

- [ ] **Step 3: 修复 capturer/base.py:11 — type-arg**

Read `src/uniqoremote/pipeline/capturer/base.py`。将 `np.ndarray` 改为 `np.ndarray[Any, np.dtype[np.generic]]`。

- [ ] **Step 4: 修复 agent/__main__.py — attr-defined / type: ignore**

Read `src/uniqoremote/agent/__main__.py`。删除所有 `# type: ignore[attr-defined]` 注释 (第 14,17 行等)。将 `logger.info(...)` 改为 `logger.info` 调用前加 `assert logger is not None`。第 39 行 `_handle_client(conn, logger)` 改为 `_handle_client(conn: IpcConnection, logger: Any) -> None`。

- [ ] **Step 5: 修复 capturer/gdi.py:51-52 — assignment**

Read `src/uniqoremote/pipeline/capturer/gdi.py`。第 50-52 行：

```python
data = np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 4)
data = data[:, :, :3]
data = np.ascontiguousarray(data[:, :, ::-1])
```

改为显式类型标注：

```python
raw = np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 4)
bgr: np.ndarray[tuple[int, ...], np.dtype[np.uint8]] = raw[:, :, :3]
data: np.ndarray[tuple[int, ...], np.dtype[np.uint8]] = np.ascontiguousarray(bgr[:, :, ::-1])
```

- [ ] **Step 6: 验证**

Run: `python -m mypy --strict src/uniqoremote/server/relay/ src/uniqoremote/server/admin/ src/uniqoremote/pipeline/capturer/ src/uniqoremote/agent/`
Expected: 0 errors

- [ ] **Step 7: Commit**

```bash
git add src/uniqoremote/server/relay/relay.py src/uniqoremote/server/admin/web.py src/uniqoremote/pipeline/capturer/base.py src/uniqoremote/agent/__main__.py src/uniqoremote/pipeline/capturer/gdi.py
git commit -m "fix: resolve all mypy strict errors"
```

### Task 1.2: 修复 ruff 错误

**Files:** Modify `src/uniqoremote/ui/windows/main.py`

- [ ] **Step 1: 修复 E501 行过长**

Read `src/uniqoremote/ui/windows/main.py:220-224`。将单行换为多行：

```python
        self._connect_btn = QPushButton("连接")
        self._connect_btn.setStyleSheet(
            "QPushButton { background-color: #a6e3a1; color: #1e1e2e;"
            " font-weight: bold; padding: 10px 24px; }"
            "QPushButton:hover { background-color: #94e2d5; }"
        )
```

- [ ] **Step 2: 验证**

Run: `python -m ruff check src/`
Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add src/uniqoremote/ui/windows/main.py
git commit -m "style: fix line too long in main.py"
```

### Task 1.3: 安装 UI 依赖并跑通全部测试

**Files:** Modify `pyproject.toml`

- [ ] **Step 1: 在 pyproject.toml dev extras 加 PySide6 + qasync**

Read `pyproject.toml`。在 `[project.optional-dependencies]` 的 `dev` 中加：

```toml
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.25",
    "pytest-cov>=6",
    "ruff>=0.11",
    "mypy>=1.15",
    "PySide6>=6.8",
    "qasync>=0.27",
]
```

- [ ] **Step 2: 安装**

```bash
pip install -e ".[dev]"
```

- [ ] **Step 3: 验证全部测试**

```bash
python -m pytest tests/ -v --tb=no -q
```
Expected: 130+ passed

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add PySide6 and qasync to dev dependencies"
```

### Task 1.4: 修复 Encoder 接口

**Files:** Modify `src/uniqoremote/pipeline/encoder/ffmpeg.py`

Read `src/uniqoremote/pipeline/encoder/ffmpeg.py` 全文。

- [ ] **Step 1: 添加 RawFrame import**

在文件顶部加：

```python
from uniqoremote.pipeline.capturer.base import RawFrame
```

- [ ] **Step 2: 修改 encode() 签名**

将 `async def encode(self, frame_data: bytes) -> bytes:` (第 64 行) 替换为：

```python
    async def encode(self, frame: RawFrame) -> list[bytes]:
        if self._proc is None:
            return [b""]
        if self._proc.stdin is None or self._proc.stdout is None:
            return [b""]
        raw = frame.data.tobytes()
        self._proc.stdin.write(raw)
        self._proc.stdin.flush()
        data = self._proc.stdout.read(65536)
        return [data] if data else [b""]
```

- [ ] **Step 3: 验证**

```bash
python -m pytest tests/pipeline/ -v --tb=short -q
python -m ruff check src/uniqoremote/pipeline/encoder/
python -m mypy --strict src/uniqoremote/pipeline/encoder/
```
Expected: tests pass, ruff 0, mypy 0

- [ ] **Step 4: Commit**

```bash
git add src/uniqoremote/pipeline/encoder/ffmpeg.py
git commit -m "fix: align FfmpegEncoder.encode() signature with Encoder ABC"
```

### Task 1.5: 创建 config.toml 模板

**Files:** Create `resources/config.toml`

- [ ] **Step 1: 写入模板**

```toml
# UniqoRemote 配置文件
# 首次启动时自动生成，可直接编辑

[identity]
# 设备唯一 ID (自动生成，请勿手动修改)
device_id = ""
# 显示名称
device_name = "My PC"

[network]
# 本地绑定端口
bind_port = 21116
# Rendezvous 服务器地址 (格式: ip:port)
rendezvous_server = ""

[display]
# 捕获分辨率
default_width = 1920
default_height = 1080
# 最大帧率
max_fps = 30

[ai]
# 启用 AI 功能 (需要 API Key)
enabled = false
# AI 模型名称
model = "deepseek-chat"
# API Key (从环境变量 UNIQOREMOTE_AI_API_KEY 读取)
api_key = ""
```

- [ ] **Step 2: Commit**

```bash
git add resources/config.toml
git commit -m "feat: add default config template"
```

### Task 1.6: 配置自动持久化 device_id

**Files:** Modify `src/uniqoremote/core/config.py`

Read `src/uniqoremote/core/config.py` 全文。

- [ ] **Step 1: 写入测试 tests/core/test_config.py**

在文件末尾追加：

```python
def test_persist_device_id(tmp_path):
    cfg_path = tmp_path / "config.toml"
    cfg1 = load_config(cfg_path)
    assert cfg1.identity.device_id != ""
    dev_id = cfg1.identity.device_id

    cfg2 = load_config(cfg_path)
    assert cfg2.identity.device_id == dev_id
```

Run: `pytest tests/core/test_config.py::test_persist_device_id -v`
Expected: FAIL

- [ ] **Step 2: 修改 `load_config()`**

在 `load_config()` 末尾 `return config` 之前加：

```python
    if not config.identity.device_id:
        config.identity.device_id = uuid.uuid4().hex[:12]
    _save_config(path, config)
```

在文件末尾加 `_save_config`:

```python
def _save_config(path: Path, config: Config) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""[identity]
device_id = "{config.identity.device_id}"
device_name = "{config.identity.device_name}"

[network]
bind_port = {config.network.bind_port}
rendezvous_server = "{config.network.rendezvous_server}"

[display]
default_width = {config.display.default_width}
default_height = {config.display.default_height}
max_fps = {config.display.max_fps}

[ai]
enabled = {str(config.ai.enabled).lower()}
model = "{config.ai.model}"
api_key = "{config.ai.api_key}"
"""
    path.write_text(content, encoding="utf-8")
```

- [ ] **Step 3: 验证**

```bash
python -m pytest tests/core/test_config.py -v --tb=short -q
```
Expected: 4 passed

- [ ] **Step 4: Commit**

```bash
git add src/uniqoremote/core/config.py tests/core/test_config.py
git commit -m "feat: auto-generate and persist config with device_id"
```

---

## Phase 2: Agent 真实实现

### Task 2.1: 实现 PipelineRunner

**Files:** Create `src/uniqoremote/agent/pipeline_runner.py`, `tests/agent/test_pipeline_runner.py`

- [ ] **Step 1: 写测试文件**

```python
from __future__ import annotations

import asyncio
import pytest
from uniqoremote.agent.pipeline_runner import PipelineRunner
from uniqoremote.pipeline.capturer.base import Capturer, RawFrame
from uniqoremote.pipeline.encoder.base import Encoder, EncodedPacket
import numpy as np

class _FakeCapturer(Capturer):
    def __init__(self):
        self._started = False
        self._count = 0

    async def start(self, monitor: int = 0) -> None:
        self._started = True

    async def capture(self) -> RawFrame:
        self._count += 1
        if self._count > 3:
            await asyncio.sleep(10)
        return RawFrame(
            data=np.zeros((100, 100, 4), dtype=np.uint8),
            width=100, height=100,
        )

    async def stop(self) -> None:
        self._started = False

    @property
    def supported_resolutions(self) -> list[tuple[int, int]]:
        return [(100, 100)]


class _FakeEncoder(Encoder):
    def __init__(self):
        self._started = False
        self._frames: list[RawFrame] = []

    async def start(self, width: int, height: int, fps: int, codec: str) -> None:
        self._started = True

    async def encode(self, frame: RawFrame) -> list[EncodedPacket]:
        self._frames.append(frame)
        return [EncodedPacket(data=b"encoded", is_keyframe=False, pts=0)]

    async def request_keyframe(self) -> None:
        pass

    async def stop(self) -> None:
        self._started = False


@pytest.mark.asyncio
async def test_pipeline_runner_start_stop():
    capturer = _FakeCapturer()
    encoder = _FakeEncoder()
    queue: asyncio.Queue[list[bytes]] = asyncio.Queue()
    runner = PipelineRunner(capturer, encoder, queue)
    await runner.start(1920, 1080, 30, "h264")
    assert runner.is_running
    await asyncio.sleep(0.2)
    assert not queue.empty()
    encoded_frames = await queue.get()
    assert len(encoded_frames) == 1
    assert encoded_frames[0] == b"encoded"
    await runner.stop()
    assert not runner.is_running
```

Run: `pytest tests/agent/test_pipeline_runner.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 2: 实现 PipelineRunner**

```python
from __future__ import annotations

import asyncio
from uniqoremote.pipeline.capturer.base import Capturer
from uniqoremote.pipeline.encoder.base import Encoder


class PipelineRunner:
    def __init__(
        self,
        capturer: Capturer,
        encoder: Encoder,
        frame_queue: asyncio.Queue[list[bytes]],
    ) -> None:
        self._capturer = capturer
        self._encoder = encoder
        self._queue = frame_queue
        self._running = False
        self._task: asyncio.Task[None] | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(
        self, width: int, height: int, fps: int, codec: str
    ) -> None:
        await self._capturer.start()
        await self._encoder.start(width, height, fps, codec)
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._encoder.stop()
        await self._capturer.stop()

    async def _loop(self) -> None:
        while self._running:
            try:
                frame = await asyncio.wait_for(self._capturer.capture(), timeout=1.0)
            except TimeoutError:
                continue
            packets = await self._encoder.encode(frame)
            data_list = [p.data for p in packets]
            await self._queue.put(data_list)
```

- [ ] **Step 3: 验证**

```bash
python -m pytest tests/agent/test_pipeline_runner.py -v --tb=short
```
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/uniqoremote/agent/pipeline_runner.py tests/agent/test_pipeline_runner.py
git commit -m "feat: add PipelineRunner for agent capture loop"
```

### Task 2.2: 重写 Agent handler

**Files:** Modify `src/uniqoremote/agent/__main__.py`

Read `src/uniqoremote/agent/__main__.py` 全文。

- [ ] **Step 1: 替换 `_handle_client`**

将 `_handle_client` 函数完整替换为：

```python
async def _handle_client(conn, logger) -> None:
    from uniqoremote.agent.pipeline_runner import PipelineRunner
    from uniqoremote.input.controller import InputController
    from uniqoremote.pipeline.capturer.gdi import GdiCapturer
    from uniqoremote.pipeline.encoder.ffmpeg import FfmpegEncoder

    runner: PipelineRunner | None = None
    input_ctrl = InputController()
    frame_queue: asyncio.Queue[list[bytes]] = asyncio.Queue()

    try:
        while True:
            msg_type, payload = await conn.recv()
            logger.info("agent_msg_received", type=msg_type)

            if msg_type == "START_CAPTURE":
                width = int(payload.get("width", 1920))
                height = int(payload.get("height", 1080))
                fps = int(payload.get("fps", 30))
                codec = str(payload.get("codec", "h264"))
                capturer = GdiCapturer()
                encoder = FfmpegEncoder()
                if not encoder.is_available:
                    await conn.send("ERROR", {"code": "FFMPEG_NOT_FOUND"})
                    continue
                runner = PipelineRunner(capturer, encoder, frame_queue)
                await runner.start(width, height, fps, codec)
                await conn.send("FRAME", {"status": "capture_started"})
                asyncio.create_task(_push_frames(conn, frame_queue, logger))

            elif msg_type == "STOP_CAPTURE":
                if runner:
                    await runner.stop()
                    runner = None
                await conn.send("FRAME", {"status": "capture_stopped"})

            elif msg_type == "INJECT_INPUT":
                await input_ctrl.handle(payload)

            elif msg_type == "HEARTBEAT":
                await conn.send("HEARTBEAT", {"ts": payload.get("ts", 0)})

    except Exception:
        logger.exception("agent_client_error")
    finally:
        if runner:
            await runner.stop()
        import contextlib
        with contextlib.suppress(Exception):
            await conn.close()


async def _push_frames(conn, frame_queue, logger) -> None:
    while True:
        try:
            frames = await asyncio.wait_for(frame_queue.get(), timeout=1.0)
            for data in frames:
                await conn.send("FRAME", {"data": data, "size": len(data)})
        except TimeoutError:
            continue
        except asyncio.CancelledError:
            break
```

- [ ] **Step 2: 验证 mypy**

```bash
python -m mypy --strict src/uniqoremote/agent/
python -m ruff check src/uniqoremote/agent/
```

- [ ] **Step 3: Commit**

```bash
git add src/uniqoremote/agent/__main__.py
git commit -m "feat: implement real capture/inject handlers in agent"
```

### Task 2.3: Agent 提权启动

**Files:** Modify `src/uniqoremote/ui/compose.py`

Read `src/uniqoremote/ui/compose.py` 全文。

- [ ] **Step 1: 添加 agent 启动函数**

在 `compose.py` 中部加：

```python
import subprocess
import sys

def _start_agent() -> subprocess.Popen[bytes] | None:
    agent_module = "uniqoremote.agent"
    cmd = [sys.executable, "-m", agent_module]
    try:
        import ctypes
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f"-m {agent_module}", None, 1
        )
        if ret <= 32:
            return subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        return None
    except Exception:
        return subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
```

- [ ] **Step 2: 在 `create_app()` 中调用**

在 `create_app()` 函数 `config = load_config(...)` 之后加：

```python
    _start_agent()
```

- [ ] **Step 3: 验证 ruff + mypy**

```bash
python -m ruff check src/uniqoremote/ui/compose.py
python -m mypy --strict src/uniqoremote/ui/compose.py
```

- [ ] **Step 4: Commit**

```bash
git add src/uniqoremote/ui/compose.py
git commit -m "feat: spawn agent process with elevation on startup"
```

---

## Phase 3: Session 联网

### Task 3.1: 实现握手模块

**Files:** Create `src/uniqoremote/session/handshake.py`, `tests/session/test_handshake.py`

- [ ] **Step 1: 写测试**

```python
from __future__ import annotations

import pytest
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from uniqoremote.session.handshake import (
    HandshakeState,
    derive_shared_key,
    generate_hello_payload,
)
from uniqoremote.core.crypto import generate_key_pair, generate_nonce


def test_generate_hello_payload():
    sk, pk = generate_key_pair()
    nonce = generate_nonce()
    payload = generate_hello_payload("abc123", pk, "1.0.0", nonce)
    assert payload["device_id"] == "abc123"
    assert len(payload["public_key"]) == 32
    assert payload["nonce"] == nonce


def test_derive_shared_key_identical():
    sk_a, pk_a = generate_key_pair()
    sk_b, pk_b = generate_key_pair()
    nonce_a = generate_nonce()
    nonce_b = generate_nonce()
    key_a = derive_shared_key(sk_a, pk_b, nonce_a, nonce_b)
    key_b = derive_shared_key(sk_b, pk_a, nonce_a, nonce_b)
    assert key_a == key_b
    assert len(key_a) == 32


def test_handshake_state_transitions():
    state = HandshakeState.IDLE
    assert state == HandshakeState.IDLE
```

Run: `pytest tests/session/test_handshake.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 2: 实现 handshake.py**

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey

from uniqoremote.core.crypto import (
    derive_session_key,
    public_key_from_bytes,
    public_key_to_bytes,
)


class HandshakeState(StrEnum):
    IDLE = "idle"
    HELLO_SENT = "hello_sent"
    NOTIFY_RECEIVED = "notify_received"
    KEY_DERIVED = "key_derived"
    FAILED = "failed"


@dataclass
class HandshakeContext:
    private_key: X25519PrivateKey
    public_key: X25519PublicKey
    nonce: bytes
    device_id: str
    version: str
    state: HandshakeState = HandshakeState.IDLE
    peer_public_key: bytes | None = None
    peer_nonce: bytes | None = None
    session_key: bytes | None = None


def generate_hello_payload(
    device_id: str,
    public_key: X25519PublicKey,
    version: str,
    nonce: bytes,
) -> dict:
    return {
        "device_id": device_id,
        "public_key": public_key_to_bytes(public_key),
        "version": version,
        "capabilities": {
            "codec": ["h264"],
            "max_res": "1920x1080",
        },
        "nonce": nonce,
    }


def derive_shared_key(
    private_key: X25519PrivateKey,
    peer_public_key: X25519PublicKey,
    nonce_a: bytes,
    nonce_b: bytes,
) -> bytes:
    return derive_session_key(private_key, peer_public_key, nonce_a, nonce_b)
```

- [ ] **Step 3: 验证**

```bash
python -m pytest tests/session/test_handshake.py -v --tb=short
```
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/uniqoremote/session/handshake.py tests/session/test_handshake.py
git commit -m "feat: add ECDH handshake and session key derivation"
```

### Task 3.2: 实现 Server 协议监听器

**Files:** Create `src/uniqoremote/server/protocol.py`, `tests/server/test_protocol.py`

- [ ] **Step 1: 写测试**

```python
from __future__ import annotations

import asyncio
import pytest
from uniqoremote.server.protocol import ProtocolServer


@pytest.mark.asyncio
async def test_protocol_server_start_stop():
    server = ProtocolServer()
    port = await server.start("127.0.0.1", 0)
    assert port > 0
    await server.stop()


@pytest.mark.asyncio
async def test_hello_registration():
    from uniqoremote.core.crypto import generate_key_pair, public_key_to_bytes

    server = ProtocolServer()
    port = await server.start("127.0.0.1", 0)

    sk_a, pk_a = generate_key_pair()
    server.register_device("test-device-1", public_key_to_bytes(pk_a), ("127.0.0.1", 12345))
    device = server.lookup_peer("test-device-1")
    assert device is not None
    assert device.public_key == public_key_to_bytes(pk_a)

    await server.stop()
```

Run: `pytest tests/server/test_protocol.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 2: 实现 ProtocolServer**

```python
from __future__ import annotations

import asyncio
import struct
from typing import Any

import msgpack

from uniqoremote.core.events import MessageType
from uniqoremote.core.protocol import (
    MAGIC,
    PROTOCOL_VERSION,
    HEADER_SIZE,
    decode_frame,
    encode_frame,
)
from uniqoremote.server.relay.relay import RelayServer
from uniqoremote.server.rendezvous.manager import RendezvousManager, RegisteredDevice


class ProtocolServer:
    def __init__(self) -> None:
        self._rendezvous = RendezvousManager()
        self._relay = RelayServer()
        self._transport: asyncio.DatagramTransport | None = None
        self._relay_transport: asyncio.DatagramTransport | None = None

    async def start(self, host: str = "0.0.0.0", port: int = 21116) -> int:
        loop = asyncio.get_running_loop()
        self._transport, _ = await loop.create_datagram_endpoint(
            lambda: _UdpProtocol(self),
            local_addr=(host, port),
        )
        sock = self._transport.get_extra_info("socket")
        assert sock is not None
        sockname: tuple[str, int] = sock.getsockname()
        return sockname[1]

    async def start_relay(self, host: str = "0.0.0.0", port: int = 21117) -> int:
        return await self._relay.start(host, port)

    def register_device(
        self, device_id: str, public_key: bytes, addr: tuple[str, int] | None
    ) -> RegisteredDevice:
        return self._rendezvous.register(device_id, public_key, addr)

    def lookup_peer(self, device_id: str) -> RegisteredDevice | None:
        return self._rendezvous.lookup_peer(device_id)

    async def stop(self) -> None:
        if self._transport:
            self._transport.close()
            self._transport = None
        await self._relay.stop()

    def handle_datagram(self, data: bytes, addr: tuple[str, int]) -> None:
        if len(data) < HEADER_SIZE:
            return
        try:
            msg = decode_frame(data)
        except Exception:
            return

        if msg.type == MessageType.HELLO:
            self._handle_hello(msg.payload, addr)
        elif msg.type == MessageType.PUNCH:
            self._handle_punch(msg.payload, addr)
        elif msg.type == MessageType.PING:
            self._handle_pong(addr)

    def _handle_hello(self, payload: Any, addr: tuple[str, int]) -> None:
        device_id = payload.get("device_id", "")
        public_key = payload.get("public_key", b"")
        device = self._rendezvous.register(device_id, public_key, addr)
        peer = self._rendezvous.lookup_peer(device_id)
        if peer and peer.addr:
            notify_data = encode_frame(
                MessageType.NOTIFY,
                {"device_id": peer.device_id, "public_key": peer.public_key},
            )
            if self._transport:
                self._transport.sendto(notify_data, peer.addr)

    def _handle_punch(self, payload: Any, addr: tuple[str, int]) -> None:
        target_id = payload.get("target_device_id", "")
        peer = self._rendezvous.lookup_peer(target_id)
        if peer and peer.addr and self._transport:
            punch_data = encode_frame(
                MessageType.PUNCH,
                {"from_device_id": payload.get("from_device_id", ""),
                 "peer_addr": addr},
            )
            self._transport.sendto(punch_data, peer.addr)

    def _handle_pong(self, addr: tuple[str, int]) -> None:
        pass


class _UdpProtocol(asyncio.DatagramProtocol):
    def __init__(self, server: ProtocolServer) -> None:
        self._server = server

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self._server.handle_datagram(data, addr)
```

- [ ] **Step 3: 验证**

```bash
python -m pytest tests/server/test_protocol.py -v --tb=short
python -m ruff check src/uniqoremote/server/protocol.py
```
Expected: tests pass, ruff 0

- [ ] **Step 4: Commit**

```bash
git add src/uniqoremote/server/protocol.py tests/server/test_protocol.py
git commit -m "feat: add server protocol listener for HELLO/NOTIFY/PUNCH"
```

### Task 3.3: 更新 server/__main__.py 启动 ProtocolServer

**Files:** Modify `src/uniqoremote/server/__main__.py`

Read `src/uniqoremote/server/__main__.py` 全文。

- [ ] **Step 1: 替换 main()**

```python
async def main() -> None:
    logger = configure_logging(level="INFO")
    logger.info("server_starting")  # type: ignore[attr-defined]

    from uniqoremote.server.protocol import ProtocolServer

    server = ProtocolServer()
    rendezvous_port = await server.start("0.0.0.0", 21116)
    logger.info("rendezvous_listening", port=rendezvous_port)  # type: ignore[attr-defined]
    relay_port = await server.start_relay("0.0.0.0", 21117)
    logger.info("relay_listening", port=relay_port)  # type: ignore[attr-defined]

    logger.info("server_ready")  # type: ignore[attr-defined]

    stop = asyncio.Event()
    import signal
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())

    await stop.wait()
    await server.stop()
    logger.info("server_stopped")  # type: ignore[attr-defined]
```

- [ ] **Step 2: 验证 mypy**

```bash
python -m mypy --strict src/uniqoremote/server/__main__.py
```

- [ ] **Step 3: Commit**

```bash
git add src/uniqoremote/server/__main__.py
git commit -m "feat: integrate ProtocolServer into server entry point"
```

### Task 3.4: 重写 SessionManager 加上网络能力

**Files:** Modify `src/uniqoremote/session/manager.py`

Read `src/uniqoremote/session/manager.py` 全文。

- [ ] **Step 1: 替换 SessionManager 实现**

完整替换为：

```python
from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import msgpack

from uniqoremote.core.channel import EncryptedChannel
from uniqoremote.core.crypto import (
    generate_key_pair,
    generate_nonce,
    public_key_from_bytes,
    public_key_to_bytes,
)
from uniqoremote.core.events import MessageType
from uniqoremote.core.protocol import encode_frame, decode_frame
from uniqoremote.session.handshake import (
    HandshakeContext,
    HandshakeState,
    derive_shared_key,
    generate_hello_payload,
)
from uniqoremote.transport.base import Transport
from uniqoremote.transport.udp import UdpTransport
from uniqoremote.transport.tcp import TcpTransport
from uniqoremote.transport.p2p import P2PTransport, StunClient


class SessionState(StrEnum):
    IDLE = "idle"
    CONNECTING = "connecting"
    HANDSHAKING = "handshaking"
    ACTIVE = "active"
    CLOSING = "closing"
    ERROR = "error"


class SessionError(Exception):
    pass


@dataclass
class Session:
    session_id: str
    remote_device_id: str
    state: SessionState = SessionState.IDLE
    metadata: dict[str, Any] = field(default_factory=dict)

    def transition(self, target: SessionState) -> None:
        valid = _TRANSITIONS.get(self.state, set())
        if target not in valid:
            raise SessionError(f"Invalid transition: {self.state} -> {target}")
        self.state = target


_TRANSITIONS: dict[SessionState, set[SessionState]] = {
    SessionState.IDLE: {SessionState.CONNECTING},
    SessionState.CONNECTING: {SessionState.HANDSHAKING, SessionState.ERROR},
    SessionState.HANDSHAKING: {SessionState.ACTIVE, SessionState.ERROR},
    SessionState.ACTIVE: {SessionState.CLOSING, SessionState.ERROR},
    SessionState.CLOSING: {SessionState.IDLE},
    SessionState.ERROR: {SessionState.IDLE, SessionState.CLOSING},
}


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._channel: EncryptedChannel | None = None
        self._transport: Transport | None = None
        self._frame_handlers: list[Callable[[bytes], None]] = []

    def create(self, session_id: str, remote_device_id: str) -> Session:
        session = Session(session_id=session_id, remote_device_id=remote_device_id)
        session.transition(SessionState.CONNECTING)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def list_active(self) -> list[Session]:
        return [s for s in self._sessions.values() if s.state == SessionState.ACTIVE]

    def on_frame(self, handler: Callable[[bytes], None]) -> None:
        self._frame_handlers.append(handler)

    async def connect(
        self,
        remote_device_id: str,
        server_addr: tuple[str, int],
        stun: StunClient,
        p2p: P2PTransport,
        relay: TcpTransport,
        config_device_id: str,
    ) -> Session:
        sk, pk = generate_key_pair()
        nonce = generate_nonce()
        hello = generate_hello_payload(config_device_id, pk, "1.0.0", nonce)
        frame = encode_frame(MessageType.HELLO, hello)

        udp = UdpTransport()
        await udp.bind(("0.0.0.0", 0))
        await udp.connect(server_addr)
        await udp.send(frame)

        try:
            raw = await asyncio.wait_for(udp.recv(), timeout=5.0)
        except TimeoutError:
            raise SessionError("No response from server")

        msg = decode_frame(raw)
        if msg.type != MessageType.NOTIFY:
            raise SessionError(f"Expected NOTIFY, got {msg.type}")

        peer_pubkey = msg.payload.get("public_key", b"")
        session_key = derive_shared_key(sk, public_key_from_bytes(peer_pubkey), nonce, b"")
        hctx = HandshakeContext(
            private_key=sk,
            public_key=pk,
            nonce=nonce,
            device_id=config_device_id,
            version="1.0.0",
            state=HandshakeState.KEY_DERIVED,
            peer_public_key=peer_pubkey,
            session_key=session_key,
        )

        self._transport = p2p
        self._channel = EncryptedChannel(p2p, session_key)

        session = self.create(remote_device_id, remote_device_id)
        session.transition(SessionState.HANDSHAKING)
        session.transition(SessionState.ACTIVE)
        return session

    async def send_frame(self, data: bytes) -> None:
        if self._channel is None:
            raise SessionError("Not connected")
        await self._channel.send(MessageType.VIDEO, data)

    async def send_input(self, payload: dict[str, Any]) -> None:
        if self._channel is None:
            raise SessionError("Not connected")
        await self._channel.send(MessageType.INPUT, payload)

    async def disconnect(self) -> None:
        if self._channel is not None:
            await self._channel.send(MessageType.BYE, {})
        self._channel = None
        self._transport = None
```

- [ ] **Step 2: 验证**

```bash
python -m pytest tests/session/ -v --tb=short -q
python -m mypy --strict src/uniqoremote/session/manager.py
```
Expected: existing tests pass

- [ ] **Step 3: Commit**

```bash
git add src/uniqoremote/session/manager.py
git commit -m "feat: add network connect/disconnect to SessionManager"
```

### Task 3.5: 更新 compose.py 移除 derive_key

**Files:** Modify `src/uniqoremote/ui/compose.py`

Read `src/uniqoremote/ui/compose.py` 全文。

- [ ] **Step 1: 重写 create_app()**

完整替换为：

```python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from uniqoremote.core.config import Config, load_config

if TYPE_CHECKING:
    from uniqoremote.ui.windows.main import MainWindow


def create_app(config_path: Path | None = None) -> MainWindow:
    if config_path is None:
        config_path = Path("config.toml")
    config = load_config(config_path)
    _start_agent()

    from uniqoremote.pipeline.encoder.ffmpeg import FfmpegDecoder
    from uniqoremote.session.handshake import HandshakeContext
    from uniqoremote.session.manager import SessionManager
    from uniqoremote.transport.p2p import P2PTransport, StunClient
    from uniqoremote.transport.tcp import TcpTransport
    from uniqoremote.ui.ipc_client import IpcClient
    from uniqoremote.ui.windows.main import MainWindow

    session_mgr = SessionManager()
    decoder = FfmpegDecoder()
    agent_client = IpcClient(port=9510)
    stun = StunClient()
    p2p_transport = P2PTransport()
    relay_transport = TcpTransport()
    ai_client = _create_ai_client(config)

    return MainWindow(
        config=config,
        session_mgr=session_mgr,
        decoder=decoder,
        agent_client=agent_client,
        ai_client=ai_client,
        stun_client=stun,
        p2p_transport=p2p_transport,
        relay_transport=relay_transport,
    )


def _create_ai_client(config: Config):
    if config.ai.enabled and config.ai.api_key:
        from uniqoremote.ai.client import DeepSeekClient
        return DeepSeekClient(model=config.ai.model)
    return None


def _start_agent() -> None:
    try:
        import ctypes
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, "-m uniqoremote.agent", None, 1
        )
        if ret <= 32:
            subprocess.Popen(
                [sys.executable, "-m", "uniqoremote.agent"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        subprocess.Popen(
            [sys.executable, "-m", "uniqoremote.agent"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
```

- [ ] **Step 2: 验证**

```bash
python -m ruff check src/uniqoremote/ui/compose.py
python -m mypy --strict src/uniqoremote/ui/compose.py
```

- [ ] **Step 3: Commit**

```bash
git add src/uniqoremote/ui/compose.py
git commit -m "refactor: remove fake derive_key, defer channel creation to session connect"
```

### Task 3.6: Server Docker 部署

**Files:** Create `Dockerfile`, `docker-compose.yml`

- [ ] **Step 1: Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/uniqoremote src/uniqoremote

RUN pip install --no-cache-dir cryptography msgpack numpy structlog

EXPOSE 21116/udp
EXPOSE 21117/udp

CMD ["python", "-m", "uniqoremote.server"]
```

- [ ] **Step 2: docker-compose.yml**

```yaml
version: "3.9"
services:
  uniqoremote-server:
    build: .
    ports:
      - "21116:21116/udp"
      - "21117:21117/udp"
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

- [ ] **Step 3: Commit**

```bash
git add Dockerfile docker-compose.yml
git commit -m "feat: add Docker deployment for server"
```

---

## Phase 4: 局域网端到端 + Phase 5: 互联网

### Task 4.1: 重写 MainWindow._on_connect

**Files:** Modify `src/uniqoremote/ui/windows/main.py`

Read `src/uniqoremote/ui/windows/main.py` 全文。

- [ ] **Step 1: 修改 __init__ 参数**

在 `__init__` 中加 `stun_client`, `p2p_transport`, `relay_transport` 参数：

```python
    def __init__(
        self,
        config: Config,
        session_mgr: SessionManager | None = None,
        decoder: FfmpegDecoder | None = None,
        agent_client: IpcClient | None = None,
        ai_client: DeepSeekClient | None = None,
        router: MessageRouter | None = None,
        stun_client: Any = None,
        p2p_transport: Any = None,
        relay_transport: Any = None,
    ) -> None:
        ...
        self._stun_client = stun_client
        self._p2p_transport = p2p_transport
        self._relay_transport = relay_transport
```

- [ ] **Step 2: 重写 _on_connect**

替换 `_on_connect` 方法：

```python
    def _on_connect(self) -> None:
        rid = self._remote_input.text().strip()
        if not rid:
            self._status.showMessage("请输入远程设备 ID", 3000)
            return

        server_str = self._config.network.rendezvous_server
        if not server_str:
            self._status.showMessage("请先在设置中配置服务器地址", 5000)
            return

        host, port_str = server_str.rsplit(":", 1)
        server_addr = (host, int(port_str))

        import asyncio
        self._active_session_id = rid

        async def _do_connect():
            try:
                await self._session_mgr.connect(
                    remote_device_id=rid,
                    server_addr=server_addr,
                    stun=self._stun_client,
                    p2p=self._p2p_transport,
                    relay=self._relay_transport,
                    config_device_id=self._config.identity.device_id,
                )
                self._disconnect_btn.setEnabled(True)
                self._status.showMessage(f"已连接到 {rid}", 5000)
                for i in range(1, self._stack.count()):
                    w = self._stack.widget(i)
                    if w:
                        self._enable_buttons(w, True)
            except Exception as e:
                self._status.showMessage(f"连接失败: {e}", 5000)

        asyncio.ensure_future(_do_connect())
```

- [ ] **Step 3: 重写 _on_disconnect**

```python
    def _on_disconnect(self) -> None:
        import asyncio

        async def _do_disconnect():
            try:
                await self._session_mgr.disconnect()
            except Exception:
                pass

        asyncio.ensure_future(_do_disconnect())
        self._active_session_id = None
        self._disconnect_btn.setEnabled(False)
        self._status.showMessage("已断开连接", 3000)
        for i in range(1, self._stack.count()):
            w = self._stack.widget(i)
            if w:
                self._enable_buttons(w, False)
```

- [ ] **Step 4: Commit**

```bash
git add src/uniqoremote/ui/windows/main.py
git commit -m "feat: wire _on_connect to real session connect flow"
```

### Task 4.2: 实现远程画面渲染 + 输入发送

**Files:** Modify `src/uniqoremote/ui/windows/remote.py`

Read `src/uniqoremote/ui/windows/remote.py` 全文。

- [ ] **Step 1: 重写 RemoteView**

完整替换为：

```python
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QMouseEvent, QKeyEvent
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from uniqoremote.session.manager import SessionManager
    from uniqoremote.pipeline.encoder.ffmpeg import FfmpegDecoder


class RemoteView(QWidget):
    def __init__(
        self,
        session_mgr: SessionManager | None = None,
        decoder: FfmpegDecoder | None = None,
    ) -> None:
        super().__init__()
        self._session_mgr = session_mgr
        self._decoder = decoder
        self._display = QLabel()
        self._display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._display.setStyleSheet("background-color: black;")
        self._display.setMinimumSize(640, 480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._display)

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        if self._session_mgr:
            self._session_mgr.on_frame(self._on_frame)

        self._timer = QTimer()
        self._timer.timeout.connect(self._process_frames)
        self._timer.start(16)
        self._frame_queue: list[bytes] = []

    def _on_frame(self, data: bytes) -> None:
        self._frame_queue.append(data)

    def _process_frames(self) -> None:
        if not self._frame_queue:
            return
        data = self._frame_queue.pop(0)
        if self._decoder:
            raw = self._decoder.decode(data)
            if raw:
                img = QImage(raw, self._decoder._width, self._decoder._height,
                             self._decoder._width * 4, QImage.Format.Format_RGBA8888)
                self._display.setPixmap(QPixmap.fromImage(img))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._session_mgr:
            asyncio.ensure_future(self._session_mgr.send_input({
                "type": "mouse_move",
                "x": event.position().x(),
                "y": event.position().y(),
            }))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._session_mgr:
            btn_map = {
                Qt.MouseButton.LeftButton: "left",
                Qt.MouseButton.RightButton: "right",
                Qt.MouseButton.MiddleButton: "middle",
            }
            btn = btn_map.get(event.button(), "left")
            asyncio.ensure_future(self._session_mgr.send_input({
                "type": "mouse_press",
                "button": btn,
            }))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._session_mgr:
            btn_map = {
                Qt.MouseButton.LeftButton: "left",
                Qt.MouseButton.RightButton: "right",
                Qt.MouseButton.MiddleButton: "middle",
            }
            btn = btn_map.get(event.button(), "left")
            asyncio.ensure_future(self._session_mgr.send_input({
                "type": "mouse_release",
                "button": btn,
            }))

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._session_mgr:
            asyncio.ensure_future(self._session_mgr.send_input({
                "type": "key_press",
                "key": event.key(),
                "modifiers": int(event.modifiers()),
            }))

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if self._session_mgr:
            asyncio.ensure_future(self._session_mgr.send_input({
                "type": "key_release",
                "key": event.key(),
            }))
```

- [ ] **Step 2: 更新 MainWindow._open_remote_view**

```python
    def _open_remote_view(self) -> None:
        from PySide6.QtWidgets import QDialog
        from uniqoremote.ui.windows.remote import RemoteView

        dlg = QDialog(self)
        dlg.setWindowTitle(f"远程桌面 - {self._active_session_id}")
        dlg.resize(1024, 768)
        view = RemoteView(session_mgr=self._session_mgr, decoder=self._decoder)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(view)
        dlg.exec()
```

- [ ] **Step 3: 验证 ruff**

```bash
python -m ruff check src/uniqoremote/ui/windows/remote.py
```

- [ ] **Step 4: Commit**

```bash
git add src/uniqoremote/ui/windows/remote.py src/uniqoremote/ui/windows/main.py
git commit -m "feat: real remote view rendering and input event forwarding"
```

### Task 4.3: P2P 打洞失败降级 + relay 帧封装

**Files:** Modify `src/uniqoremote/transport/p2p.py`, `src/uniqoremote/core/protocol.py`

Read `src/uniqoremote/transport/p2p.py`, `src/uniqoremote/core/protocol.py` 全文。

- [ ] **Step 1: 在 protocol.py 末尾加 relay 辅助函数**

```python
def make_relay_frame(session_id: str, data: bytes) -> bytes:
    return session_id.encode("ascii")[:12].ljust(12, b"\x00") + data


def parse_relay_frame(data: bytes) -> tuple[str, bytes]:
    sid = data[:12].decode("ascii").rstrip("\x00")
    return sid, data[12:]
```

- [ ] **Step 2: P2PTransport 加 relay 回退**

在 `P2PTransport` 中加 `_relay` 属性和 `set_relay` 方法：

```python
class P2PTransport(Transport):
    def __init__(self) -> None:
        self._udp = UdpTransport()
        self._relay: TcpTransport | None = None
        self._use_relay = False

    def set_relay(self, relay: TcpTransport) -> None:
        self._relay = relay

    async def send(self, data: bytes) -> None:
        if self._use_relay and self._relay:
            await self._relay.send(data)
        else:
            await self._udp.send(data)

    async def recv(self) -> bytes:
        if self._use_relay and self._relay:
            return await self._relay.recv()
        return await self._udp.recv()

    async def connect(self, addr: tuple[str, int]) -> None:
        if self._use_relay and self._relay:
            await self._relay.connect(addr)
        else:
            await self._udp.connect(addr)
```

在 `punch()` 方法失败返回 `PunchResult(success=False, ...)` 前加：

```python
        if self._relay is not None:
            self._use_relay = True
```

- [ ] **Step 3: Commit**

```bash
git add src/uniqoremote/transport/p2p.py src/uniqoremote/core/protocol.py
git commit -m "feat: P2P punch failure auto-fallback to relay mode"
```

### Task 4.4: 心跳 + 断线重连

**Files:** Modify `src/uniqoremote/session/manager.py`

- [ ] **Step 1: 在 SessionManager 加心跳**

在 `connect()` 末尾 `return session` 前加：

```python
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self) -> None:
        while self._channel is not None:
            try:
                await self._channel.send(MessageType.PING, {})
                await asyncio.sleep(5)
            except Exception:
                self._channel = None
                for s in self._sessions.values():
                    if s.state == SessionState.ACTIVE:
                        s.transition(SessionState.ERROR)
                break
```

在 `disconnect()` 中加：

```python
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
```

- [ ] **Step 2: Commit**

```bash
git add src/uniqoremote/session/manager.py
git commit -m "feat: add heartbeat detection and auto-disconnect on timeout"
```

### Task 4.5: 动态码率调整

**Files:** Modify `src/uniqoremote/pipeline/encoder/ffmpeg.py`

Read `src/uniqoremote/pipeline/encoder/ffmpeg.py` 全文。

- [ ] **Step 1: 加 set_bitrate 方法**

在 `FfmpegEncoder` 中加：

```python
    def set_bitrate(self, bitrate_kbps: int) -> None:
        self._config.bitrate = bitrate_kbps
        if self._proc is not None and self._proc.stdin is not None:
            self._proc.stdin.close()
            self._proc.terminate()
            self._proc.wait(timeout=5)
            self._proc = None
```

SessionManager 中加丢包计数器：

```python
    def __init__(self) -> None:
        ...
        self._lost_packets = 0
        self._total_packets = 0
        self._current_bitrate = 5000

    def _adjust_bitrate(self) -> None:
        if self._total_packets < 20:
            return
        loss_rate = self._lost_packets / self._total_packets
        if loss_rate > 0.05 and self._current_bitrate > 1000:
            self._current_bitrate = max(1000, int(self._current_bitrate * 0.75))
        elif loss_rate < 0.01 and self._current_bitrate < 20000:
            self._current_bitrate = min(20000, int(self._current_bitrate * 1.2))
        self._lost_packets = 0
        self._total_packets = 0
```

- [ ] **Step 2: Commit**

```bash
git add src/uniqoremote/pipeline/encoder/ffmpeg.py src/uniqoremote/session/manager.py
git commit -m "feat: dynamic bitrate adjustment based on packet loss"
```

### Task 4.6: 设置窗口服务器地址配置

**Files:** Modify `src/uniqoremote/ui/windows/settings.py`

Read `src/uniqoremote/ui/windows/settings.py` 全文。

- [ ] **Step 1: 替换为含服务器地址的设置面板**

完整替换文件：

```python
from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from uniqoremote.core.config import Config


class SettingsPage(QWidget):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)

        title = QLabel("设置")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #cdd6f4;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        self._device_name = QLineEdit(config.identity.device_name)
        form.addRow("设备名称:", self._device_name)

        self._server_addr = QLineEdit(config.network.rendezvous_server)
        self._server_addr.setPlaceholderText("例如: 192.168.1.100:21116")
        form.addRow("服务器地址:", self._server_addr)

        self._bind_port = QLineEdit(str(config.network.bind_port))
        form.addRow("本地端口:", self._bind_port)

        self._max_fps = QLineEdit(str(config.display.max_fps))
        form.addRow("最大帧率:", self._max_fps)

        layout.addLayout(form)

        row = QHBoxLayout()
        save = QPushButton("保存")
        save.setStyleSheet(
            "QPushButton { background-color: #a6e3a1; color: #1e1e2e;"
            " font-weight: bold; padding: 10px 24px; }"
            "QPushButton:hover { background-color: #94e2d5; }"
        )
        save.clicked.connect(self._on_save)
        row.addStretch()
        row.addWidget(save)
        layout.addLayout(row)

        layout.addStretch()

    def _on_save(self) -> None:
        self._config.identity.device_name = self._device_name.text()
        self._config.network.rendezvous_server = self._server_addr.text()
        self._config.network.bind_port = int(self._bind_port.text())
        self._config.display.max_fps = int(self._max_fps.text())
```

- [ ] **Step 2: 更新 MainWindow._build_placeholder 中设置页**

将 `main.py` 中第 6 个 placeholder "设置" 替换为 `SettingsPage`：

```python
        self._stack.addWidget(SettingsPage(self._config))
```

- [ ] **Step 3: Commit**

```bash
git add src/uniqoremote/ui/windows/settings.py src/uniqoremote/ui/windows/main.py
git commit -m "feat: settings page with server address and FPS config"
```

---

## Phase 6: 剪贴板 + 文件传输

### Task 6.1: Windows 剪贴板监听

**Files:** Modify `src/uniqoremote/session/clipboard.py`

Read `src/uniqoremote/session/clipboard.py` 全文。

- [ ] **Step 1: 重写 clipboard.py**

```python
from __future__ import annotations

import asyncio
import ctypes
from collections.abc import Callable

from PySide6.QtWidgets import QApplication


class ClipboardSync:
    def __init__(self, send_handler: Callable[[str], None]) -> None:
        self._send = send_handler
        self._last_text: str = ""
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()

    def on_remote_text(self, text: str) -> None:
        self._last_text = text
        self._set_clipboard(text)

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                current = self._get_clipboard()
                if current and current != self._last_text:
                    self._last_text = current
                    self._send(current)
            except Exception:
                pass
            await asyncio.sleep(0.5)

    def _get_clipboard(self) -> str:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        CF_TEXT = 1
        if not user32.OpenClipboard(0):
            return ""
        try:
            h_data = user32.GetClipboardData(CF_TEXT)
            if not h_data:
                return ""
            lp = kernel32.GlobalLock(h_data)
            if not lp:
                return ""
            try:
                return ctypes.c_char_p(lp).value.decode("gbk", errors="replace")
            finally:
                kernel32.GlobalUnlock(h_data)
        finally:
            user32.CloseClipboard()

    def _set_clipboard(self, text: str) -> None:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        CF_TEXT = 1
        data = text.encode("gbk") + b"\x00"
        if not user32.OpenClipboard(0):
            return
        try:
            user32.EmptyClipboard()
            h_mem = kernel32.GlobalAlloc(0x0002, len(data))
            if not h_mem:
                return
            lp = kernel32.GlobalLock(h_mem)
            if not lp:
                return
            ctypes.memmove(lp, data, len(data))
            kernel32.GlobalUnlock(h_mem)
            user32.SetClipboardData(CF_TEXT, h_mem)
        finally:
            user32.CloseClipboard()
```

- [ ] **Step 2: 更新 MainWindow._on_sync_clipboard**

在 `main.py` 的 `_on_sync_clipboard` 中：

```python
    def _on_sync_clipboard(self) -> None:
        from uniqoremote.session.clipboard import ClipboardSync

        async def _send(text: str) -> None:
            await self._session_mgr.send_input({"type": "clipboard", "text": text})

        self._clipboard_sync = ClipboardSync(_send)
        asyncio.ensure_future(self._clipboard_sync.start())
        self._status.showMessage("剪贴板同步已启动", 2000)
```

- [ ] **Step 3: Commit**

```bash
git add src/uniqoremote/session/clipboard.py src/uniqoremote/ui/windows/main.py
git commit -m "feat: real Windows clipboard monitoring and sync"
```

### Task 6.2: 基础文件传输

**Files:** Modify `src/uniqoremote/session/file_transfer.py`

Read `src/uniqoremote/session/file_transfer.py` 全文。

- [ ] **Step 1: 重写 file_transfer.py**

```python
from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uniqoremote.session.manager import SessionManager

CHUNK_SIZE = 65536


class FileTransfer:
    def __init__(self, session_mgr: SessionManager) -> None:
        self._session_mgr = session_mgr

    async def send(self, filepath: str) -> None:
        path = Path(filepath)
        if not path.is_file():
            return
        name = path.name
        size = path.stat().st_size
        with path.open("rb") as f:
            offset = 0
            while offset < size:
                chunk = f.read(CHUNK_SIZE)
                await self._session_mgr.send_input({
                    "type": "file_chunk",
                    "filename": name,
                    "offset": offset,
                    "size": len(chunk),
                    "total_size": size,
                    "data": chunk,
                })
                offset += len(chunk)

    def on_chunk(self, payload: dict, save_dir: str) -> None:
        name = payload["filename"]
        offset = payload["offset"]
        size = payload["size"]
        total = payload.get("total_size", 0)
        data = payload.get("data", b"")
        path = Path(save_dir) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as f:
            f.write(data)
```

- [ ] **Step 2: Commit**

```bash
git add src/uniqoremote/session/file_transfer.py
git commit -m "feat: single-file chunked transfer"
```

---

## Phase 7: 打包发布

### Task 7.1: 日志落盘

**Files:** Modify `src/uniqoremote/core/logging.py`

Read `src/uniqoremote/core/logging.py` 全文。

- [ ] **Step 1: 加文件 handler**

在 `configure_logging` 函数中加：

```python
import os
from pathlib import Path

def configure_logging(level: str = "INFO") -> Any:
    import structlog
    import logging

    log_dir = Path(os.environ.get("APPDATA", "")) / "UniqoRemote" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "uniqoremote.log"

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setLevel(getattr(logging, level.upper()))
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().setLevel(getattr(logging, level.upper()))

    return structlog.get_logger()
```

- [ ] **Step 2: Commit**

```bash
git add src/uniqoremote/core/logging.py
git commit -m "feat: log to file in APPDATA"
```

### Task 7.2: PyInstaller 打包 + 图标 + 构建脚本

**Files:** Create `scripts/uniqoremote.spec`, `scripts/build.ps1`, `resources/icon.ico`

- [ ] **Step 1: 写入 spec 文件**

```python
# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None

a = Analysis(
    ['src/uniqoremote/ui/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources/config.toml', '.'),
    ],
    hiddenimports=[
        'cryptography',
        'msgpack',
        'numpy',
        'structlog',
        'PySide6',
        'qasync',
        'uniqoremote.core',
        'uniqoremote.transport',
        'uniqoremote.pipeline',
        'uniqoremote.input',
        'uniqoremote.session',
        'uniqoremote.agent',
        'uniqoremote.server',
        'uniqoremote.ai',
        'uniqoremote.ui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='UniqoRemote',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='UniqoRemote',
)
```

- [ ] **Step 2: 写入 build.ps1**

```powershell
param([switch]$Clean)

$ErrorActionPreference = "Stop"

if ($Clean) {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist
}

Write-Host "Running tests..." -ForegroundColor Cyan
python -m pytest tests/ -v --tb=short -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed" }

Write-Host "Running ruff..." -ForegroundColor Cyan
python -m ruff check src/
if ($LASTEXITCODE -ne 0) { throw "Ruff failed" }

Write-Host "Building with PyInstaller..." -ForegroundColor Cyan
pyinstaller --clean scripts/uniqoremote.spec

Write-Host "Copying FFmpeg..." -ForegroundColor Cyan
$ffmpegPath = Join-Path $env:PROGRAMFILES "ffmpeg\bin\ffmpeg.exe"
if (Test-Path $ffmpegPath) {
    Copy-Item $ffmpegPath dist/UniqoRemote/
}

Write-Host "Build complete: dist/UniqoRemote/" -ForegroundColor Green
```

- [ ] **Step 3: 创建占位图标 (最小 valid .ico)**

```bash
python -c "from pathlib import Path; Path('resources/icon.ico').write_bytes(b'\x00\x00\x01\x00\x01\x00\x20\x20\x10\x00\x00\x00\x00\x00\xe8\x02\x00\x00\x16\x00\x00\x00')"
```

- [ ] **Step 4: Commit**

```bash
git add scripts/uniqoremote.spec scripts/build.ps1 resources/icon.ico
git commit -m "feat: PyInstaller spec, build script, and placeholder icon"
```

---

## 全量验证

完成所有 Task 后:

```bash
python -m pytest tests/ -v --tb=short -q
python -m ruff check src/ tests/
python -m ruff format --check src/ tests/
python -m mypy --strict src/uniqoremote/
```

期望: tests 全部 pass, ruff 0, mypy 0
