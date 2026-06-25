# Phase 1: 基础框架 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可运行的 UniqoRemote 项目骨架，完成 core 层 (协议/加密/配置/事件/日志) 和 transport 层 (UDP/TCP socket)，以及加密通道组装。

**Architecture:** 严格分层，core 层零业务依赖，transport 层仅依赖 core。所有模块通过 ABC 接口和依赖注入解耦。TDD 驱动，先写测试后写实现。

**Tech Stack:** Python 3.11+, cryptography, msgpack, structlog, pytest, pytest-asyncio, ruff, mypy

**Design reference:** `docs/design.md` 第 2-5 节

---

## File Map (Phase 1)

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | 项目元数据、依赖、脚本入口 |
| `src/uniqoremote/__init__.py` | 包根 |
| `src/uniqoremote/core/__init__.py` | core 包 |
| `src/uniqoremote/core/events.py` | 内部事件 dataclass 定义 |
| `src/uniqoremote/core/config.py` | TOML 配置加载与校验 |
| `src/uniqoremote/core/logging.py` | structlog 配置工厂 |
| `src/uniqoremote/core/protocol.py` | 消息类型枚举 + msgpack 编解码 |
| `src/uniqoremote/core/crypto.py` | X25519 + ChaCha20-Poly1305 AEAD |
| `src/uniqoremote/transport/__init__.py` | transport 包 |
| `src/uniqoremote/transport/base.py` | Transport ABC 接口 |
| `src/uniqoremote/transport/udp.py` | asyncio UDP socket 实现 |
| `src/uniqoremote/transport/tcp.py` | asyncio TCP socket 实现 |
| `src/uniqoremote/core/channel.py` | 加密通道 (组合 crypto + transport) |

---

### Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `src/uniqoremote/__init__.py`
- Create: `src/uniqoremote/core/__init__.py`
- Create: `src/uniqoremote/transport/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/core/__init__.py`
- Create: `tests/transport/__init__.py`
- Create: `tests/conftest.py`
- Create: `.gitignore`

- [ ] **Step 1: Write pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=75", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "uniqoremote"
version = "0.1.0"
description = "Python Remote Desktop Protocol"
requires-python = ">=3.11"
dependencies = [
    "cryptography>=44",
    "msgpack>=1.1",
    "structlog>=25",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.25",
    "pytest-cov>=6",
    "ruff>=0.11",
    "mypy>=1.15",
]
ui = [
    "PySide6>=6.8",
    "qasync>=0.27",
]
ai = [
    "litellm>=1.75",
    "paddleocr>=2.9",
]

[tool.ruff]
target-version = "py311"
line-length = 100
lint.select = ["E", "F", "I", "N", "W", "UP", "B", "SIM"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
strict = true
python_version = "3.11"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 2: Create package init files**

```python
# src/uniqoremote/__init__.py
"""UniqoRemote - Remote Desktop Protocol."""
```

```python
# src/uniqoremote/core/__init__.py
"""Core layer: protocol, crypto, config, events, logging, channel."""
```

```python
# src/uniqoremote/transport/__init__.py
"""Transport layer: UDP/TCP socket abstractions."""
```

```python
# tests/__init__.py (empty)
```

```python
# tests/core/__init__.py (empty)
```

```python
# tests/transport/__init__.py (empty)
```

- [ ] **Step 3: Write tests/conftest.py**

```python
from __future__ import annotations

import pytest


@pytest.fixture
def key_pair():
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

    private = X25519PrivateKey.generate()
    return private, private.public_key()
```

- [ ] **Step 4: Write .gitignore**

```
__pycache__/
*.py[cod]
.venv/
.eggs/
*.egg-info/
dist/
build/
.coverage
htmlcov/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.env
```

- [ ] **Step 5: Install package in dev mode and verify imports**

Run:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -c "import uniqoremote; import uniqoremote.core; import uniqoremote.transport; print('OK')"
```
Expected: `OK`

- [ ] **Step 6: Run basic tool checks**

Run:
```powershell
ruff check src/ tests/
mypy src/ --strict
```
Expected: No errors.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: initialize project skeleton"
```

---

### Task 2: core/events.py — Internal Event Types

**Files:**
- Create: `src/uniqoremote/core/events.py`
- Create: `tests/core/test_events.py`

- [ ] **Step 1: Write failing test**

```python
# tests/core/test_events.py
from __future__ import annotations

from dataclasses import asdict

from uniqoremote.core.events import ConnectionEvent, ConnectionState, FrameEvent, InputEvent, InputEventType


class TestConnectionEvent:
    def test_creates_connection_event(self) -> None:
        event = ConnectionEvent(state=ConnectionState.CONNECTING, device_id="abc123")
        assert event.state == ConnectionState.CONNECTING
        assert event.device_id == "abc123"

    def test_serializes_roundtrip(self) -> None:
        import msgpack

        event = ConnectionEvent(state=ConnectionState.ACTIVE, device_id="xyz")
        packed = msgpack.packb(asdict(event))
        unpacked = msgpack.unpackb(packed)
        assert unpacked[b"state"] == b"active"
        assert unpacked[b"device_id"] == b"xyz"


class TestInputEvent:
    def test_creates_key_event(self) -> None:
        event = InputEvent(type=InputEventType.KEY_DOWN, data={"key": 0x41})
        assert event.type == InputEventType.KEY_DOWN
        assert event.data["key"] == 0x41

    def test_creates_mouse_event(self) -> None:
        event = InputEvent(
            type=InputEventType.MOUSE_MOVE, data={"x": 100, "y": 200}
        )
        assert event.type == InputEventType.MOUSE_MOVE
        assert event.data["x"] == 100


class TestFrameEvent:
    def test_creates_frame_event(self) -> None:
        data = b"\x00" * 100
        event = FrameEvent(width=1920, height=1080, data=data, pts=0.0)
        assert event.width == 1920
        assert event.height == 1080
        assert event.data == data
        assert event.pts == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_events.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'uniqoremote.core.events'`

- [ ] **Step 3: Implement core/events.py**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class ConnectionState(Enum):
    IDLE = auto()
    CONNECTING = auto()
    HANDSHAKING = auto()
    ACTIVE = auto()
    CLOSING = auto()
    ERROR = auto()


class MessageType(Enum):
    HELLO = 0x01
    PUNCH = 0x02
    NOTIFY = 0x03
    RELAY = 0x04
    STREAM = 0x05
    CONTROL = 0x06
    CLIPBOARD = 0x07
    FILE = 0x08
    CHAT = 0x09
    AUDIO = 0x0A
    VIDEO = 0x0B
    INPUT = 0x0C
    ERROR = 0x0D
    PING = 0x0E
    PONG = 0x0F
    BYE = 0x10

    @classmethod
    def from_int(cls, value: int) -> MessageType:
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Unknown message type: 0x{value:02X}")


class InputEventType(Enum):
    KEY_DOWN = auto()
    KEY_UP = auto()
    MOUSE_MOVE = auto()
    MOUSE_DOWN = auto()
    MOUSE_UP = auto()
    MOUSE_WHEEL = auto()


class ErrorCode(Enum):
    INVALID_FRAME = 0x01
    VERSION_MISMATCH = 0x02
    AUTH_FAILED = 0x03
    DEVICE_OFFLINE = 0x04
    RELAY_FULL = 0x05
    PUNCH_FAILED = 0x06
    TIMEOUT = 0x07
    INTERNAL = 0x08


@dataclass
class ConnectionEvent:
    state: ConnectionState
    device_id: str


@dataclass
class InputEvent:
    type: InputEventType
    data: dict[str, Any]


@dataclass
class FrameEvent:
    width: int
    height: int
    data: bytes
    pts: float = 0.0


@dataclass
class ErrorEvent:
    code: ErrorCode
    message: str
    device_id: str = ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_events.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/uniqoremote/core/events.py tests/core/test_events.py
git commit -m "feat: add internal event types and enums"
```

---

### Task 3: core/config.py — TOML Configuration

**Files:**
- Create: `src/uniqoremote/core/config.py`
- Create: `tests/core/test_config.py`

- [ ] **Step 1: Write failing test**

```python
# tests/core/test_config.py
from __future__ import annotations

import tempfile
from pathlib import Path

from uniqoremote.core.config import Config, load_config


DEFAULT_TOML = b"""
[identity]
device_id = "test-device-001"
device_name = "Test PC"

[network]
bind_port = 21116
rendezvous_server = "rdp.example.com"

[display]
default_width = 1920
default_height = 1080
max_fps = 30

[ai]
enabled = true
model = "deepseek-chat"
"""


class TestConfig:
    def test_loads_valid_config(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(DEFAULT_TOML)
            config_path = Path(f.name)

        try:
            config = load_config(config_path)
            assert config.identity.device_id == "test-device-001"
            assert config.identity.device_name == "Test PC"
            assert config.network.bind_port == 21116
            assert config.network.rendezvous_server == "rdp.example.com"
            assert config.display.default_width == 1920
            assert config.display.default_height == 1080
            assert config.display.max_fps == 30
            assert config.ai.enabled is True
            assert config.ai.model == "deepseek-chat"
        finally:
            config_path.unlink()

    def test_default_config_has_sensible_values(self) -> None:
        config = Config()
        assert config.identity.device_id != ""
        assert config.network.bind_port == 21116
        assert config.display.max_fps == 30
        assert config.ai.enabled is False

    def test_loads_partial_config_with_defaults(self) -> None:
        partial = b"[identity]\ndevice_id = \"partial-device\"\n"
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(partial)
            config_path = Path(f.name)

        try:
            config = load_config(config_path)
            assert config.identity.device_id == "partial-device"
            assert config.network.bind_port == 21116
        finally:
            config_path.unlink()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement core/config.py**

```python
from __future__ import annotations

import tomllib
import uuid
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class IdentityConfig:
    device_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    device_name: str = "UniqoRemote Client"


@dataclass
class NetworkConfig:
    bind_port: int = 21116
    rendezvous_server: str = ""


@dataclass
class DisplayConfig:
    default_width: int = 1920
    default_height: int = 1080
    max_fps: int = 30


@dataclass
class AIConfig:
    enabled: bool = False
    model: str = "deepseek-chat"
    api_key: str = ""


@dataclass
class Config:
    identity: IdentityConfig = field(default_factory=IdentityConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    ai: AIConfig = field(default_factory=AIConfig)


def load_config(path: Path) -> Config:
    config = Config()
    if not path.exists():
        return config

    with open(path, "rb") as f:
        raw = tomllib.load(f)

    if "identity" in raw:
        id_raw = raw["identity"]
        if "device_id" in id_raw:
            config.identity.device_id = id_raw["device_id"]
        if "device_name" in id_raw:
            config.identity.device_name = id_raw["device_name"]

    if "network" in raw:
        net_raw = raw["network"]
        if "bind_port" in net_raw:
            config.network.bind_port = net_raw["bind_port"]
        if "rendezvous_server" in net_raw:
            config.network.rendezvous_server = net_raw["rendezvous_server"]

    if "display" in raw:
        disp_raw = raw["display"]
        if "default_width" in disp_raw:
            config.display.default_width = disp_raw["default_width"]
        if "default_height" in disp_raw:
            config.display.default_height = disp_raw["default_height"]
        if "max_fps" in disp_raw:
            config.display.max_fps = disp_raw["max_fps"]

    if "ai" in raw:
        ai_raw = raw["ai"]
        if "enabled" in ai_raw:
            config.ai.enabled = ai_raw["enabled"]
        if "model" in ai_raw:
            config.ai.model = ai_raw["model"]
        if "api_key" in ai_raw:
            config.ai.api_key = ai_raw["api_key"]

    return config
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_config.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/uniqoremote/core/config.py tests/core/test_config.py
git commit -m "feat: add TOML configuration with layered defaults"
```

---

### Task 4: core/logging.py — Structured Logging

**Files:**
- Create: `src/uniqoremote/core/logging.py`
- Create: `tests/core/test_logging.py`

- [ ] **Step 1: Write failing test**

```python
# tests/core/test_logging.py
from __future__ import annotations

import io
import json
import logging

import structlog

from uniqoremote.core.logging import configure_logging


class TestLogging:
    def test_configure_logging_returns_bound_logger(self) -> None:
        logger = configure_logging(level="INFO")
        assert isinstance(logger, structlog.BoundLogger)

    def test_log_messages_are_json_formatted(self) -> None:
        stream = io.StringIO()
        configure_logging(level="DEBUG", output=stream)

        logger = structlog.get_logger()
        logger.info("test_event", key="value")

        output = stream.getvalue()
        assert output != ""
        parsed = json.loads(output)
        assert parsed["event"] == "test_event"
        assert parsed["key"] == "value"
        assert "timestamp" in parsed
        assert parsed["level"] == "info"

    def test_debug_messages_filtered_at_info_level(self) -> None:
        stream = io.StringIO()
        configure_logging(level="INFO", output=stream)

        logger = structlog.get_logger()
        logger.debug("should_not_appear")

        output = stream.getvalue()
        assert "should_not_appear" not in output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_logging.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement core/logging.py**

```python
from __future__ import annotations

import logging
import sys
from typing import IO

import structlog


def configure_logging(
    level: str = "INFO",
    output: IO[str] | None = None,
) -> structlog.BoundLogger:
    if output is None:
        output = sys.stderr

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=output, level=log_level)

    return structlog.get_logger()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_logging.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/uniqoremote/core/logging.py tests/core/test_logging.py
git commit -m "feat: add structlog JSON logging configuration"
```

---

### Task 5: core/protocol.py — Message Encode/Decode

**Files:**
- Create: `src/uniqoremote/core/protocol.py`
- Create: `tests/core/test_protocol.py`

- [ ] **Step 1: Write failing test**

```python
# tests/core/test_protocol.py
from __future__ import annotations

import pytest

from uniqoremote.core.events import MessageType
from uniqoremote.core.protocol import (
    MAGIC,
    PROTOCOL_VERSION,
    ProtocolError,
    decode_frame,
    encode_frame,
    make_hello_payload,
)


def _pack_hello() -> bytes:
    payload = make_hello_payload(
        device_id="test-device",
        public_key=b"\x00" * 32,
        version="1.0.0",
        capabilities={"codec": ["h264"]},
        nonce=b"\x01" * 24,
    )
    return encode_frame(MessageType.HELLO, payload)


class TestEncodeDecode:
    def test_encode_hello_header_magic(self) -> None:
        frame = _pack_hello()
        assert frame[:4] == MAGIC

    def test_encode_hello_header_version(self) -> None:
        frame = _pack_hello()
        version_field = int.from_bytes(frame[4:6], "big")
        assert version_field == PROTOCOL_VERSION

    def test_encode_hello_header_type(self) -> None:
        frame = _pack_hello()
        type_field = int.from_bytes(frame[6:8], "big")
        assert type_field == MessageType.HELLO.value

    def test_encode_hello_total_length(self) -> None:
        frame = _pack_hello()
        length_field = int.from_bytes(frame[12:16], "big")
        assert length_field == len(frame) - 16

    def test_roundtrip_hello(self) -> None:
        original = _pack_hello()
        msg = decode_frame(original)
        assert msg.type == MessageType.HELLO
        assert msg.payload[b"device_id"] == b"test-device"
        assert msg.payload[b"version"] == b"1.0.0"
        assert len(msg.payload[b"public_key"]) == 32

    def test_decode_invalid_magic(self) -> None:
        bad = b"XXXX" + b"\x00" * 12
        with pytest.raises(ProtocolError, match="Invalid magic"):
            decode_frame(bad)

    def test_decode_version_mismatch(self) -> None:
        bad = MAGIC + b"\xFF\xFF" + b"\x00" * 10
        with pytest.raises(ProtocolError, match="Unsupported protocol version"):
            decode_frame(bad)

    def test_decode_truncated_header(self) -> None:
        with pytest.raises(ProtocolError, match="Frame too short"):
            decode_frame(MAGIC + b"\x00\x00\x00")

    def test_decode_truncated_payload(self) -> None:
        header = MAGIC + (0x0001).to_bytes(2, "big") + (0x0001).to_bytes(2, "big") + (0).to_bytes(4, "big") + (100).to_bytes(4, "big")
        with pytest.raises(ProtocolError, match="Payload too short"):
            decode_frame(header + b"\x00" * 50)

    def test_sequence_number_increments(self) -> None:
        payload = b"data"
        frame1 = encode_frame(MessageType.STREAM, payload)
        frame2 = encode_frame(MessageType.STREAM, payload)
        seq1 = int.from_bytes(frame1[8:12], "big")
        seq2 = int.from_bytes(frame2[8:12], "big")
        assert seq2 == seq1 + 1

    def test_decode_preserves_sequence_number(self) -> None:
        payload = b"test"
        frame = encode_frame(MessageType.RELAY, payload)
        msg = decode_frame(frame)
        assert msg.seq_num == int.from_bytes(frame[8:12], "big")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_protocol.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement core/protocol.py**

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import msgpack

from uniqoremote.core.events import MessageType

MAGIC = b"UNIQ"
PROTOCOL_VERSION = 1
HEADER_SIZE = 16
_seq_counter = 0


def _next_seq() -> int:
    global _seq_counter
    _seq_counter += 1
    return _seq_counter


class ProtocolError(Exception):
    pass


@dataclass
class DecodedMessage:
    type: MessageType
    seq_num: int
    payload: dict[str, Any]


def encode_frame(msg_type: MessageType, payload: bytes | dict[str, Any]) -> bytes:
    if isinstance(payload, dict):
        payload = msgpack.packb(payload)

    seq = _next_seq()
    header = bytearray(HEADER_SIZE)
    header[0:4] = MAGIC
    header[4:6] = PROTOCOL_VERSION.to_bytes(2, "big")
    header[6:8] = msg_type.value.to_bytes(2, "big")
    header[8:12] = seq.to_bytes(4, "big")
    header[12:16] = len(payload).to_bytes(4, "big")
    return bytes(header) + payload


def decode_frame(data: bytes) -> DecodedMessage:
    if len(data) < HEADER_SIZE:
        raise ProtocolError(f"Frame too short: {len(data)} bytes")

    magic = data[0:4]
    if magic != MAGIC:
        raise ProtocolError(f"Invalid magic: {magic!r}")

    version = int.from_bytes(data[4:6], "big")
    if version != PROTOCOL_VERSION:
        raise ProtocolError(f"Unsupported protocol version: {version}")

    msg_type = MessageType.from_int(int.from_bytes(data[6:8], "big"))
    seq_num = int.from_bytes(data[8:12], "big")
    payload_len = int.from_bytes(data[12:16], "big")

    if len(data) < HEADER_SIZE + payload_len:
        raise ProtocolError(f"Payload too short: expected {payload_len}, got {len(data) - HEADER_SIZE}")

    payload_bytes = data[HEADER_SIZE:HEADER_SIZE + payload_len]
    payload: dict[str, Any] = msgpack.unpackb(payload_bytes)
    return DecodedMessage(type=msg_type, seq_num=seq_num, payload=payload)


def make_hello_payload(
    device_id: str,
    public_key: bytes,
    version: str,
    capabilities: dict[str, Any],
    nonce: bytes,
) -> dict[str, Any]:
    return {
        "device_id": device_id,
        "public_key": public_key,
        "version": version,
        "capabilities": capabilities,
        "nonce": nonce,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_protocol.py -v`
Expected: All 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/uniqoremote/core/protocol.py tests/core/test_protocol.py
git commit -m "feat: add protocol frame encode/decode with msgpack"
```

---

### Task 6: core/crypto.py — X25519 + ChaCha20-Poly1305

**Files:**
- Create: `src/uniqoremote/core/crypto.py`
- Create: `tests/core/test_crypto.py`

- [ ] **Step 1: Write failing test**

```python
# tests/core/test_crypto.py
from __future__ import annotations

import pytest

from uniqoremote.core.crypto import (
    decrypt,
    derive_session_key,
    encrypt,
    generate_key_pair,
    generate_nonce,
    public_key_to_bytes,
)


class TestKeyGeneration:
    def test_generates_valid_key_pair(self) -> None:
        private, public = generate_key_pair()
        raw_pub = public_key_to_bytes(public)
        assert len(raw_pub) == 32
        assert raw_pub != b"\x00" * 32

    def test_generates_unique_keys(self) -> None:
        pub1 = public_key_to_bytes(generate_key_pair()[1])
        pub2 = public_key_to_bytes(generate_key_pair()[1])
        assert pub1 != pub2

    def test_generate_nonce_length(self) -> None:
        nonce = generate_nonce()
        assert len(nonce) == 12


class TestSessionKey:
    def test_derives_same_key_both_sides(self) -> None:
        sk_a, pk_a = generate_key_pair()
        sk_b, pk_b = generate_key_pair()
        nonce_a = generate_nonce()
        nonce_b = generate_nonce()

        key_a = derive_session_key(sk_a, pk_b, nonce_a, nonce_b)
        key_b = derive_session_key(sk_b, pk_a, nonce_a, nonce_b)
        assert key_a == key_b
        assert len(key_a) == 44

    def test_different_nonces_produce_different_keys(self) -> None:
        sk_a, pk_a = generate_key_pair()
        sk_b, pk_b = generate_key_pair()

        key1 = derive_session_key(sk_a, pk_b, generate_nonce(), generate_nonce() + b"\x00" * 12)
        key2 = derive_session_key(sk_a, pk_b, generate_nonce(), generate_nonce() + b"\x00" * 12)
        assert key1 != key2


class TestEncryptDecrypt:
    @pytest.fixture
    def session_key(self) -> bytes:
        sk_a, pk_a = generate_key_pair()
        sk_b, pk_b = generate_key_pair()
        return derive_session_key(sk_a, pk_b, generate_nonce(), generate_nonce())

    def test_encrypt_decrypt_roundtrip(self, session_key: bytes) -> None:
        plaintext = b"Hello, UniqoRemote! This is a secret message."
        nonce_nonce = 0
        ciphertext = encrypt(session_key, plaintext, nonce_nonce)
        assert ciphertext != plaintext
        decrypted = decrypt(session_key, ciphertext, nonce_nonce)
        assert decrypted == plaintext

    def test_encrypt_produces_auth_tag(self, session_key: bytes) -> None:
        plaintext = b"short"
        ciphertext = encrypt(session_key, plaintext, 1)
        assert len(ciphertext) == len(plaintext) + 16

    def test_decrypt_detects_tampering(self, session_key: bytes) -> None:
        plaintext = b"tamper test"
        ciphertext = bytearray(encrypt(session_key, plaintext, 2))
        ciphertext[0] ^= 0xFF
        with pytest.raises(Exception):
            decrypt(session_key, bytes(ciphertext), 2)

    def test_decrypt_detects_wrong_nonce(self, session_key: bytes) -> None:
        plaintext = b"nonce test"
        ciphertext = encrypt(session_key, plaintext, 3)
        with pytest.raises(Exception):
            decrypt(session_key, ciphertext, 4)

    def test_different_keys_produce_different_ciphertext(self, session_key: bytes) -> None:
        sk_a, pk_a = generate_key_pair()
        sk_b, pk_b = generate_key_pair()
        other_key = derive_session_key(sk_a, pk_b, generate_nonce(), generate_nonce())

        ct1 = encrypt(session_key, b"same data", 5)
        ct2 = encrypt(other_key, b"same data", 5)
        assert ct1 != ct2

    def test_large_payload(self, session_key: bytes) -> None:
        plaintext = b"\xAA" * 65536
        ciphertext = encrypt(session_key, plaintext, 6)
        assert decrypt(session_key, ciphertext, 6) == plaintext
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_crypto.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement core/crypto.py**

```python
from __future__ import annotations

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import os

NONCE_SIZE = 12
KEY_SIZE = 44


def generate_key_pair() -> tuple[X25519PrivateKey, X25519PublicKey]:
    private = X25519PrivateKey.generate()
    return private, private.public_key()


def public_key_to_bytes(public_key: X25519PublicKey) -> bytes:
    return public_key.public_bytes_raw()


def public_key_from_bytes(data: bytes) -> X25519PublicKey:
    return X25519PublicKey.from_public_bytes(data)


def generate_nonce() -> bytes:
    return os.urandom(NONCE_SIZE)


def derive_session_key(
    private_key: X25519PrivateKey,
    peer_public_key: X25519PublicKey,
    nonce_a: bytes,
    nonce_b: bytes,
) -> bytes:
    shared_secret = private_key.exchange(peer_public_key)
    salt = nonce_a[:8] + nonce_b[:8]
    return HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        info=b"uniqoremote-session-key",
    ).derive(shared_secret)


def _make_nonce(seq_num: int) -> bytes:
    nonce = bytearray(NONCE_SIZE)
    nonce[0:4] = seq_num.to_bytes(4, "big")
    return bytes(nonce)


def encrypt(session_key: bytes, plaintext: bytes, seq_num: int) -> bytes:
    nonce = _make_nonce(seq_num)
    cipher = ChaCha20Poly1305(session_key)
    return cipher.encrypt(nonce, plaintext, None)


def decrypt(session_key: bytes, ciphertext: bytes, seq_num: int) -> bytes:
    nonce = _make_nonce(seq_num)
    cipher = ChaCha20Poly1305(session_key)
    return cipher.decrypt(nonce, ciphertext, None)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_crypto.py -v`
Expected: All 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/uniqoremote/core/crypto.py tests/core/test_crypto.py
git commit -m "feat: add X25519 ECDH + ChaCha20-Poly1305 AEAD encryption"
```

---

### Task 7: transport/base.py — Transport ABC

**Files:**
- Create: `src/uniqoremote/transport/base.py`
- Create: `tests/transport/test_base.py`

- [ ] **Step 1: Write failing test**

```python
# tests/transport/test_base.py
from __future__ import annotations

from uniqoremote.transport.base import Transport


class TestTransportABC:
    def test_cannot_instantiate_abc(self) -> None:
        try:
            Transport()  # type: ignore[abstract]
            assert False, "Should have raised TypeError"
        except TypeError:
            pass

    def test_subclass_must_implement_all_methods(self) -> None:
        class Incomplete(Transport):
            async def connect(self, addr: tuple[str, int]) -> None:
                pass

        try:
            Incomplete()  # type: ignore[abstract]
            assert False, "Should have raised TypeError"
        except TypeError:
            pass

    def test_valid_subclass_instantiates(self) -> None:
        class Complete(Transport):
            async def connect(self, addr: tuple[str, int]) -> None:
                pass

            async def send(self, data: bytes) -> None:
                pass

            async def recv(self) -> bytes:
                return b""

            async def close(self) -> None:
                pass

        t = Complete()
        assert isinstance(t, Transport)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/transport/test_base.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement transport/base.py**

```python
from __future__ import annotations

from abc import ABC, abstractmethod


class Transport(ABC):
    @abstractmethod
    async def connect(self, addr: tuple[str, int]) -> None: ...

    @abstractmethod
    async def send(self, data: bytes) -> None: ...

    @abstractmethod
    async def recv(self) -> bytes: ...

    @abstractmethod
    async def close(self) -> None: ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/transport/test_base.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/uniqoremote/transport/base.py tests/transport/test_base.py
git commit -m "feat: add Transport ABC interface"
```

---

### Task 8: transport/udp.py — UDP Socket Transport

**Files:**
- Create: `src/uniqoremote/transport/udp.py`
- Create: `tests/transport/test_udp.py`

- [ ] **Step 1: Write failing test**

```python
# tests/transport/test_udp.py
from __future__ import annotations

import asyncio

import pytest

from uniqoremote.transport.udp import UdpTransport


class TestUdpTransport:
    @pytest.mark.asyncio
    async def test_send_recv_loopback(self) -> None:
        server = UdpTransport()
        client = UdpTransport()

        await server.bind(("127.0.0.1", 0))
        await client.bind(("127.0.0.1", 0))

        server_addr = server.local_addr
        assert server_addr is not None

        await client.connect(server_addr)
        await server.connect(client.local_addr)  # type: ignore[arg-type]

        async def recv_and_verify() -> None:
            data = await server.recv()
            assert data == b"hello from client"

        recv_task = asyncio.create_task(recv_and_verify())
        await asyncio.sleep(0.01)
        await client.send(b"hello from client")
        await asyncio.wait_for(recv_task, timeout=2.0)

        await client.close()
        await server.close()

    @pytest.mark.asyncio
    async def test_bind_auto_port(self) -> None:
        transport = UdpTransport()
        await transport.bind(("127.0.0.1", 0))
        addr = transport.local_addr
        assert addr is not None
        assert addr[0] == "127.0.0.1"
        assert addr[1] > 0
        await transport.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/transport/test_udp.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement transport/udp.py**

```python
from __future__ import annotations

import asyncio
from typing import Self

from uniqoremote.transport.base import Transport


class UdpTransport(Transport):
    def __init__(self) -> None:
        self._transport: asyncio.DatagramTransport | None = None
        self._protocol: _UdpProtocol | None = None
        self._remote_addr: tuple[str, int] | None = None

    @property
    def local_addr(self) -> tuple[str, int] | None:
        if self._transport is not None:
            sock = self._transport.get_extra_info("socket")
            if sock is not None:
                return sock.getsockname()[:2]
        return None

    async def bind(self, addr: tuple[str, int]) -> Self:
        loop = asyncio.get_running_loop()
        self._protocol = _UdpProtocol()
        self._transport, _ = await loop.create_datagram_endpoint(
            lambda: self._protocol,
            local_addr=addr,
        )
        return self

    async def connect(self, addr: tuple[str, int]) -> None:
        self._remote_addr = addr

    async def send(self, data: bytes) -> None:
        if self._transport is None or self._remote_addr is None:
            raise RuntimeError("Not connected")
        self._transport.sendto(data, self._remote_addr)

    async def recv(self) -> bytes:
        if self._protocol is None:
            raise RuntimeError("Not bound")
        return await self._protocol.recv()

    async def close(self) -> None:
        if self._transport is not None:
            self._transport.close()
            self._transport = None
        self._protocol = None
        self._remote_addr = None


class _UdpProtocol(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self._queue: asyncio.Queue[bytes] = asyncio.Queue()

    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        self._queue.put_nowait(data)

    async def recv(self) -> bytes:
        return await self._queue.get()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/transport/test_udp.py -v`
Expected: All 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/uniqoremote/transport/udp.py tests/transport/test_udp.py
git commit -m "feat: add asyncio UDP datagram transport"
```

---

### Task 9: transport/tcp.py — TCP Socket Transport

**Files:**
- Create: `src/uniqoremote/transport/tcp.py`
- Create: `tests/transport/test_tcp.py`

- [ ] **Step 1: Write failing test**

```python
# tests/transport/test_tcp.py
from __future__ import annotations

import asyncio

import pytest

from uniqoremote.transport.tcp import TcpTransport


@pytest.mark.asyncio
async def test_tcp_echo_loopback() -> None:
    server = await asyncio.start_server(
        lambda r, w: asyncio.create_task(_echo_handler(r, w)),
        "127.0.0.1",
        0,
    )
    addr = server.sockets[0].getsockname()[:2]

    client = TcpTransport()
    await client.connect(addr)

    await client.send(b"ping")
    response = await asyncio.wait_for(client.recv(), timeout=2.0)
    assert response == b"pong"

    await client.close()
    server.close()
    await server.wait_closed()


async def _echo_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    data = await reader.read(1024)
    if data == b"ping":
        writer.write(b"pong")
        await writer.drain()
    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio
async def test_tcp_large_transfer() -> None:
    large_data = b"A" * 65536

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        data = await reader.readexactly(len(large_data))
        writer.write(data)
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(lambda r, w: asyncio.create_task(handler(r, w)), "127.0.0.1", 0)
    addr = server.sockets[0].getsockname()[:2]

    client = TcpTransport()
    await client.connect(addr)

    await client.send(large_data)
    response = await asyncio.wait_for(client.recv_exactly(len(large_data)), timeout=5.0)
    assert response == large_data

    await client.close()
    server.close()
    await server.wait_closed()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/transport/test_tcp.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement transport/tcp.py**

```python
from __future__ import annotations

import asyncio

from uniqoremote.transport.base import Transport


class TcpTransport(Transport):
    def __init__(self) -> None:
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self, addr: tuple[str, int]) -> None:
        self._reader, self._writer = await asyncio.open_connection(addr[0], addr[1])

    async def send(self, data: bytes) -> None:
        if self._writer is None:
            raise RuntimeError("Not connected")
        self._writer.write(len(data).to_bytes(4, "big"))
        self._writer.write(data)
        await self._writer.drain()

    async def recv(self) -> bytes:
        if self._reader is None:
            raise RuntimeError("Not connected")
        header = await self._reader.readexactly(4)
        length = int.from_bytes(header, "big")
        return await self._reader.readexactly(length)

    async def recv_exactly(self, length: int) -> bytes:
        if self._reader is None:
            raise RuntimeError("Not connected")
        return await self._reader.readexactly(length)

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
        self._reader = None
        self._writer = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/transport/test_tcp.py -v`
Expected: All 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/uniqoremote/transport/tcp.py tests/transport/test_tcp.py
git commit -m "feat: add asyncio TCP stream transport with length-prefix framing"
```

---

### Task 10: core/channel.py — Encrypted Channel

**Files:**
- Create: `src/uniqoremote/core/channel.py`
- Create: `tests/core/test_channel.py`

- [ ] **Step 1: Write failing test**

```python
# tests/core/test_channel.py
from __future__ import annotations

import asyncio

import pytest

from uniqoremote.core.channel import EncryptedChannel
from uniqoremote.core.crypto import derive_session_key, generate_key_pair, generate_nonce
from uniqoremote.core.events import MessageType
from uniqoremote.core.protocol import DecodedMessage, encode_frame
from uniqoremote.transport.udp import UdpTransport


@pytest.mark.asyncio
async def test_encrypted_channel_roundtrip() -> None:
    sk_a, pk_a = generate_key_pair()
    sk_b, pk_b = generate_key_pair()
    nonce_a = generate_nonce()
    nonce_b = generate_nonce()
    session_key = derive_session_key(sk_a, pk_b, nonce_a, nonce_b)

    transport_a = UdpTransport()
    transport_b = UdpTransport()
    await transport_a.bind(("127.0.0.1", 0))
    await transport_b.bind(("127.0.0.1", 0))

    addr_a = transport_a.local_addr
    addr_b = transport_b.local_addr
    assert addr_a is not None
    assert addr_b is not None

    await transport_a.connect(addr_b)
    await transport_b.connect(addr_a)

    channel_a = EncryptedChannel(transport_a, session_key)
    channel_b = EncryptedChannel(transport_b, session_key)

    payload = {"msg": "encrypted hello"}
    await channel_a.send(MessageType.CHAT, payload)

    msg = await asyncio.wait_for(channel_b.recv(), timeout=2.0)
    assert isinstance(msg, DecodedMessage)
    assert msg.type == MessageType.CHAT
    assert msg.payload[b"msg"] == b"encrypted hello"

    await transport_a.close()
    await transport_b.close()


@pytest.mark.asyncio
async def test_encrypted_channel_binary_payload() -> None:
    sk_a, pk_a = generate_key_pair()
    sk_b, pk_b = generate_key_pair()
    session_key = derive_session_key(sk_a, pk_b, generate_nonce(), generate_nonce())

    transport_a = UdpTransport()
    transport_b = UdpTransport()
    await transport_a.bind(("127.0.0.1", 0))
    await transport_b.bind(("127.0.0.1", 0))
    await transport_a.connect(transport_b.local_addr)  # type: ignore[arg-type]
    await transport_b.connect(transport_a.local_addr)  # type: ignore[arg-type]

    channel_a = EncryptedChannel(transport_a, session_key)
    channel_b = EncryptedChannel(transport_b, session_key)

    binary = b"\x00\x01\x02\x03" * 100
    await channel_a.send(MessageType.VIDEO, binary)

    msg = await asyncio.wait_for(channel_b.recv(), timeout=2.0)
    assert msg.type == MessageType.VIDEO
    assert msg.payload == binary

    await transport_a.close()
    await transport_b.close()


@pytest.mark.asyncio
async def test_channel_seq_num_monotonic() -> None:
    sk_a, pk_a = generate_key_pair()
    sk_b, pk_b = generate_key_pair()
    session_key = derive_session_key(sk_a, pk_b, generate_nonce(), generate_nonce())

    transport_a = UdpTransport()
    transport_b = UdpTransport()
    await transport_a.bind(("127.0.0.1", 0))
    await transport_b.bind(("127.0.0.1", 0))
    await transport_a.connect(transport_b.local_addr)  # type: ignore[arg-type]
    await transport_b.connect(transport_a.local_addr)  # type: ignore[arg-type]

    channel_a = EncryptedChannel(transport_a, session_key)
    channel_b = EncryptedChannel(transport_b, session_key)

    seqs: list[int] = []
    for i in range(5):
        await channel_a.send(MessageType.STREAM, f"msg{i}")
        msg = await asyncio.wait_for(channel_b.recv(), timeout=2.0)
        seqs.append(msg.seq_num)

    assert seqs == sorted(seqs)
    assert len(set(seqs)) == 5

    await transport_a.close()
    await transport_b.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_channel.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement core/channel.py**

```python
from __future__ import annotations

from typing import Any

from uniqoremote.core.crypto import decrypt, encrypt
from uniqoremote.core.events import MessageType
from uniqoremote.core.protocol import DecodedMessage, decode_frame, encode_frame
from uniqoremote.transport.base import Transport


class EncryptedChannel:
    def __init__(self, transport: Transport, session_key: bytes) -> None:
        self._transport = transport
        self._session_key = session_key

    async def send(self, msg_type: MessageType, payload: bytes | dict[str, Any]) -> None:
        frame = encode_frame(msg_type, payload)
        encrypted = encrypt(self._session_key, frame, 0)
        await self._transport.send(encrypted)

    async def recv(self) -> DecodedMessage:
        raw = await self._transport.recv()
        frame = decrypt(self._session_key, raw, 0)
        return decode_frame(frame)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_channel.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/ -v --cov=src/uniqoremote`
Expected: All tests pass, coverage > 90%

- [ ] **Step 6: Run lint and type checks**

Run:
```powershell
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/ --strict
```
Expected: No errors.

- [ ] **Step 7: Commit**

```bash
git add src/uniqoremote/core/channel.py tests/core/test_channel.py
git commit -m "feat: add encrypted channel combining crypto + transport"
```

---

## Self-Review Results

**1. Spec coverage:** All Phase 1 items from `docs/design.md` section 11 are covered:
- pyproject.toml + project skeleton → Task 1
- core/protocol.py → Task 5
- core/crypto.py → Task 6
- core/config.py → Task 3
- core/events.py → Task 2
- core/logging.py → Task 4
- transport/base.py + udp.py + tcp.py → Tasks 7-9
- core/channel.py → Task 10

**2. Placeholder scan:** No TBD/TODO/incomplete sections found.

**3. Type consistency:** MessageType, Transport ABC, EncryptedChannel signatures are consistent across all tasks.

**4. Dependency order:** Tasks are ordered correctly:
- Task 1 (skeleton) has no dependencies
- Tasks 2-5 (events, config, logging, protocol) depend only on each other in order
- Task 6 (crypto) is independent (only depends on cryptography library)
- Task 7 (transport ABC) depends on Task 2 (events)
- Tasks 8-9 (UDP/TCP) depend on Task 7
- Task 10 (channel) depends on Tasks 5, 6, 7
