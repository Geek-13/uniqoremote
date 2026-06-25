# UniqoRemote 开发指南

> AI 编程助手行为规范，所有开发必须严格参照 `docs/design.md`。

---

## 1. 项目概览

Python + PySide6 远程桌面系统，全新协议，兼容 Windows。

**核心文档:** `docs/design.md` — 架构/协议/路线图的唯一权威。

### 1.1 目录结构

```
src/uniqoremote/
├── core/         # 基础层: 协议、加密、配置、事件、日志 — 零业务依赖
├── transport/    # 传输层: UDP/TCP socket — 仅依赖 core
├── pipeline/     # 采集管道: 捕获+编码 — 仅依赖 core
├── input/        # 输入控制: 键鼠注入 — 仅依赖 core
├── session/      # 会话服务: 生命周期、剪贴板、文件、聊天 — 依赖 core + pipeline
├── agent/        # 本地代理进程 (系统权限) — 独立进程, 通过 IPC 通信
├── ui/           # UI 进程 (用户权限) — 唯一组装点: ui/compose.py
├── ai/           # AI 子系统 — 可选, 无 GPU 时降级
└── server/       # 云端服务器 — 独立部署, 与客户端共享 core
```

### 1.2 层间依赖规则 (严格单向)

```
ui → session → core
       │         │
       ▼         ▼
   pipeline   transport (接口)
       │         │
       ▼         │
   agent ◀────────┘
```

- **内层不能 import 外层**
- **同层之间不直接依赖，通过上层协调**
- **core 层零业务依赖** (仅 Python 标准库 + cryptography)

---

## 2. 架构规则

### 2.1 依赖注入

- `ui/compose.py` 是**唯一组装点**，所有具体实现在此创建并注入
- 其他模块只使用 ABC 接口，不直接实例化具体类
- 禁止在构造函数中使用 `import` 绕过注入

```python
# 正确: compose.py 中组装
transport = UdpTransport()
channel = EncryptedChannel(transport, key_pair)
session_mgr = SessionManager(channel)

# 错误: 模块内直接实例化具体类
class SessionManager:
    def __init__(self):
        self.channel = EncryptedChannel(UdpTransport(), ...)  # 禁止
```

### 2.2 双进程模型

| 进程 | 入口 | 权限 | 职责 |
|------|------|------|------|
| UI | `python -m uniqoremote.ui` | user | 界面、网络、会话管理 |
| Agent | `python -m uniqoremote.agent` | system | 屏幕捕获、输入注入、音频 |

- Agent 与 UI 通过命名管道 IPC 通信
- 消息格式与网络层统一 (msgpack)
- UI 进程崩溃不得影响 Agent，反之亦然

### 2.3 协议规范

参见 `docs/design.md` 第 5 节：
- 帧头 16 字节: Magic(4) + Version(2) + Type(2) + SeqNum(4) + Length(4)
- 序列号单调递增，接收端检测重放帧
- 加密: X25519 ECDH 密钥协商 + ChaCha20-Poly1305 AEAD
- P2P 打洞失败自动降级 RELAY 模式

---

## 3. Python 规则

### 3.1 通用

- 严格遵循 **PEP 8** 编码规范
- 所有公开函数/方法必须有**类型注解**
- 使用 `ruff format` 格式化代码
- 使用 `ruff check` 进行代码检查
- 使用 `mypy --strict` 进行类型检查
- Python 最低版本: **3.11**

### 3.2 异步

- 所有 I/O 操作用 `async/await`
- Qt 事件循环通过 `qasync` 桥接
- **禁止**在 async 函数中调用 `time.sleep()`，用 `asyncio.sleep()`
- **禁止**在 async 函数中调用阻塞的 socket/文件操作，用 `run_in_executor()`
- 热路径 (捕获→编码→发送) 使用 `asyncio.Queue` 而非回调

### 3.3 依赖

- 添加新依赖前，先检查 `pyproject.toml` 是否已有同类库
- 禁止引入零使用第三方依赖
- `core` 层新依赖需要充分理由 (该层目标是零依赖)
- 禁止假设任何第三方库已安装

### 3.4 安全

- **禁止**在代码中硬编码密钥、密码、Token
- **禁止**在日志中输出密钥、密码、Token、完整帧数据
- API Key 通过环境变量 `UNIQOREMOTE_AI_API_KEY` 存储
- 加密操作统一通过 `core/crypto.py`，禁止模块自行实现加密

---

## 4. 测试规则

### 4.1 测试先行

- 每个子系统在实施前必须构建完整的测试架构
- **先写测试，后写实现** (TDD)
- 测试文件放在 `tests/`，镜像 `src/` 结构
- 测试框架: `pytest` + `pytest-asyncio` + `pytest-qt`

### 4.2 覆盖率

- 新增代码必须有对应测试
- `core` 层目标: 95%+ 覆盖率
- `transport` / `pipeline` / `input`: 80%+ 覆盖率
- `session`: 80%+ 覆盖率
- `ui`: 60%+ 覆盖率 (UI 测试成本高)
- `ai`: 70%+ 覆盖率

### 4.3 CI

- PR 前必须通过全部测试
- 所有测试必须在 5 分钟内完成 (不含 UI 测试)

---

## 5. 编辑规范

### 5.1 变更原则

- 只改需要改的，不重构无关代码
- 不做纯格式化变更
- Mimic 现有代码风格，保持命名一致性
- 禁止在代码中添加注释 (除非用户明确要求)
- 不使用 `todo`、`fixme` 等临时标记

### 5.2 Git 操作

- Commit message 格式: `<type>: <简短描述>`
- 禁止 force push 到 main/master
- 禁止修改 git config
- **自主 Loop 内:** 每完成一个通过全部验证的任务后自动提交
- **Loop 外:** 不主动提交，除非用户明确要求

---

## 6. 技术栈速查

| 用途 | 技术 | 导入路径 |
|------|------|---------|
| UI | PySide6 | `from PySide6.QtWidgets import ...` |
| 异步桥接 | qasync | `import qasync` |
| 加密 | cryptography | `from cryptography.hazmat.primitives import ...` |
| 序列化 | msgpack | `import msgpack` |
| 日志 | structlog | `import structlog` |
| 配置 | TOML | `import tomllib` (stdlib) |
| AI (LLM) | LiteLLM | `import litellm` |
| AI (OCR) | PaddleOCR | `from paddleocr import PaddleOCR` |
| 测试 | pytest | `import pytest` |
| 代码检查 | ruff | CLI only |
| 类型检查 | mypy | CLI only |
| 打包 | PyInstaller / Nuitka | CLI only |

### 明确禁止导入

- `protobuf`
- `zmq` / `pynng`
- `av` (PyAV)
- `websockets` (不引入 Web 依赖到桌面端)

---

## 7. 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 模块/文件 | snake_case | `file_transfer.py` |
| 类 | PascalCase | `SessionManager` |
| 函数/方法 | snake_case | `async def send_frame()` |
| 常量 | UPPER_SNAKE | `MAX_FRAME_SIZE` |
| 私有成员 | _leading_underscore | `self._channel` |
| ABC 接口 | 无特殊前缀, 文件名 base.py | `class Transport(ABC):` |

---

## 8. 开发流程

1. 阅读 `docs/design.md` 对应章节
2. 先写测试，确认测试失败
3. 实现功能，确认测试通过
4. 运行 `ruff check && ruff format && mypy --strict`
5. 运行 `pytest tests/<module>/ -v`
6. 不主动提交，等待用户指令

---

## 9. 自主开发循环 (Autonomous Development Loop)

> 当用户启动自主开发模式时，严格遵循此循环。目标是最大化自主吞吐量，最小化人工打断。
> 设计参考: SWE-agent (Princeton)、mini-swe-agent、Aider、OpenHands 的实战架构。

### 9.1 循环状态机

```
                    ┌──────────┐
          ┌────────▶│  SELECT  │ 选择 plan 中下一个待执行 Task
          │         └────┬─────┘
          │              ▼
          │         ┌──────────┐
          │         │ CONTEXT  │ 读取 Task 涉及的所有文件 + design.md 相关章节
          │         └────┬─────┘
          │              ▼
          │         ┌──────────┐
          │    ┌───▶│  TEST    │ 写测试代码 → 运行 → 确认 FAIL
          │    │    └────┬─────┘
          │    │         │ FAIL CONFIRMED
          │    │         ▼
          │    │    ┌──────────┐
          │    │    │IMPLEMENT │ 写最小实现使测试通过 (YAGNI)
          │    │    └────┬─────┘
          │    │         ▼
          │    │    ┌──────────┐
          │    │    │ SELF-    │ 自读变更代码, 预判问题:
          │    │    │ CHECK    │ · imports 是否存在?
          │    │    │          │ · 类型是否与接口匹配?
          │    │    │          │ · 逻辑是否覆盖所有 case?
          │    │    └────┬─────┘
          │    │         │
          │    │    ┌────▼──────┐
          │    │    │  ISSUES   │  发现问题?
          │    │    │  FOUND?   │
          │    │    └────┬──────┘
          │    │     YES │  NO
          │    │         │          ┌──────────┐
          │    │    ┌────▼─────┐    │ VERIFY   │ 运行全部检查:
          │    │    │ FIX SELF │    │          │ 1. pytest (本模块)
          │    │    │ (no retry│    │          │ 2. ruff check
          │    │    │  limit)  │    │          │ 3. ruff format --check
          │    │    └────┬─────┘    │          │ 4. mypy --strict
          │    │         │          └────┬─────┘
          │    │         └──────────────┘
          │    │                         │
          │    │                    ┌────┴─────┐
          │    │                    │  PASS?   │
          │    │                    └────┬─────┘
          │    │           ┌───────── NO │ YES
          │    │           ▼             │
          │    │    ┌──────────────┐     │
          │    │    │ CLASSIFY ERR │     │
          │    │    │ SYNTAX?      │─▶ 语法错误: 直接对照 lint 输出修复
          │    │    │ TYPE?        │─▶ 类型错误: 检查签名与接口是否匹配
          │    │    │ LOGIC?       │─▶ 逻辑错误: 重读测试预期, 检查边界
          │    │    │ IMPORT?      │─▶ 导入错误: 检查目录结构与 __init__.py
          │    │    │ ENV?         │─▶ 环境错误: 检查依赖是否安装 → 升级
          │    │    └──────┬───────┘
          │    │           ▼
          │    │    ┌──────────────┐     ┌──────────┐
          │    │    │   FIX        │     │ COMMIT   │ git add + commit
          │    │    │ (max 3 per   │     └────┬─────┘
          │    │    │  error cat)  │          │
          │    │    └──────┬───────┘     ┌────▼─────┐
          │    │           │             │ REPORT   │ 报告进度给用户
          │    │    ┌──────▼───────┐     └────┬─────┘
          │    │    │  RETRIES     │          │
          │    │    │  < 3 ?       │──────────┘ (回到 SELECT)
          │    │    └──────┬───────┘
          │    └───────────┘ YES
          │         NO → ESCALATE
          │
          └── (所有 Task 完成后) → 报告最终结果
```

### 9.2 各阶段操作规范

#### SELECT
- 从当前 Phase 的 Plan 文件中读取 TODO 列表
- 按依赖顺序选择下一个未完成的 Task
- 识别可并行 Task (见 9.4)，标记为一组
- 如果 Phase 所有 Task 完成，运行 9.5 Gate 检查后进入下一 Phase
- 如果所有 Phase 完成，报告项目完成

#### CONTEXT
- **优化上下文选择** (参考 Aider repo-map 策略):
  - 读取 Task 涉及的每个 `Create:` 文件的父目录, 了解同层代码风格
  - 读取 Task 涉及的每个 `Modify:` 文件的完整内容
  - 读取 `docs/design.md` 中相关章节
  - 读取 `AGENTS.md` 中相关规则
  - **不要** 全量读取无关文件，按需加载
- 验证理解: 在开始前确认自己知道:
  - 这个模块的职责边界是什么
  - 它依赖哪些已有模块 (检查 imports)
  - 哪些模块将依赖它
- 不得跳过此阶段直接写代码

#### TEST
- 按照 Plan 中的测试代码写入测试文件
- 运行 `pytest` 确认失败原因符合预期 (如 `ModuleNotFoundError`)
- **反模式检测:**
  - 如果测试意外通过，说明已有实现覆盖了该行为 → 检查是否误用了已有代码
  - 如果测试报错原因不是预期的，检查测试代码本身 (不是去修改实现)
- 测试应覆盖:
  - 正常路径 (happy path)
  - 边界条件 (空输入、极大值、None)
  - 错误路径 (非法输入、异常抛出)

#### IMPLEMENT
- **最小实现原则** (参考 mini-swe-agent: 100 行解决 65% SWE-bench):
  - 只写使测试通过的最少代码
  - 不做"以后可能会用到"的抽象
  - 不添加测试未覆盖的功能
  - 不添加注释
- 严格遵循 Plan 中的实现代码结构
- 如果 Plan 代码与测试不匹配，优先按测试修正实现

#### SELF-CHECK (新增)
- 在运行 VERIFY 之前，自读所有变更代码
- **线性调试轨迹** (参考 mini-swe-agent linear history):
  - 按顺序检视: imports → 类型签名 → 核心逻辑 → 边界处理
- 预判问题清单:
  - 所有 imports 对应的模块是否存在？路径是否正确？
  - 函数签名与 Plan/接口定义是否一致？
  - 类型注解是否与返回值匹配？
  - 逻辑是否覆盖了所有测试用例的路径？
  - 是否有明显的 off-by-one、None 未处理等低级错误？
- 发现问题 → 直接进入 FIX SELF (不消耗重试次数)
- 无问题 → 进入 VERIFY

#### VERIFY
- 运行 `pytest tests/<module>/ -v` — 必须全部 PASS
- 运行 `ruff check src/<module>/ tests/<module>/` — 必须零错误
- 运行 `ruff format --check src/<module>/ tests/<module>/` — 必须已格式化
- 运行 `mypy --strict src/<module>/` — 必须零错误
- **全量回归**: 每完成 3 个 Task 或一个 Phase 结束时，运行 `pytest tests/ -v` 确保不破坏已有功能

#### FIX (含错误分级)

**禁止修改测试来"通过"测试。** 只修改源代码。

错误分类及处理策略:

| 错误类别 | 判断依据 | 处理方式 |
|---------|---------|---------|
| SYNTAX | ruff check 报 E/F 类错误 | 直接对照 lint 输出修复 |
| IMPORT | `ModuleNotFoundError` | 检查目录结构、`__init__.py`、PYTHONPATH |
| TYPE | mypy 报错 | 检查类型签名与接口定义的匹配 |
| LOGIC | pytest 失败, 非语法/类型问题 | 重读测试预期, 检查边界条件 |
| ENV | 工具链报错 (pip/venv) | 检查依赖安装 → 升级为环境问题 |
| REGRESSION | 全量测试中其他模块失败 | 优先检查是否修改了共享代码 |

**重试上限: 同一错误类别连续 3 次失败 → ESCALATE。**

不同错误类别独立计数。例如: 语法错 1 次 + 类型错 1 次 ≠ 2 次语法重试。

#### COMMIT
- `git add` 该 Task 涉及的所有文件
- `git commit -m "feat: <Task 描述>"` 或 `"fix: <修复描述>"`
- 使用 `--no-verify` 仅在 hook 因外部原因失败时 (不在默认流程中)
- 不 push (除非用户要求)

#### REPORT
- 每完成一个 Task 后输出简洁进度: `[N/Total] Task 完成: <名称>`
- 每完成一个 Phase 后输出 Phase 摘要:
  ```
  Phase X 完成 ✓
  测试: N passed, 0 failed
  覆盖率: XX% (目标: XX%)
  Lint: clean
  Typecheck: clean
  ```

### 9.3 升级触发条件 (Escalate to User)

**仅以下情况打断自主循环，向用户提问:**

| 触发条件 | 说明 |
|----------|------|
| RETRY_EXHAUSTED | 同一错误类别连续 3 次修复后 VERIFY 仍未通过 |
| MISSING_DEPENDENCY | 需要的系统工具未安装 (如 ffmpeg) |
| DESIGN_CONFLICT | 实现过程中发现与 design.md 的设计矛盾 |
| AMBIGUOUS_SPEC | Plan 中的指令不清晰，有两种以上合理解读 |
| BLOCKING_TASK | 当前 Task 依赖另一个未完成 Phase 的产物 |
| STALENESS | 同一 Task 耗时超过 30 分钟或循环超过 10 次 |
| USER_INTERRUPT | 用户主动发消息要求暂停 |

**以下情况不升级，自主处理:**

| 情况 | 处理方式 |
|------|---------|
| 测试失败 (非预期原因) | 分析失败日志 → 分类错误 → 修复代码 |
| ruff/mypy 报错 | 根据错误信息分类修复 |
| 导入路径错误 | 检查目录结构与 `__init__.py` |
| 类型注解不匹配 | 修正函数签名使其符合接口定义 |
| 测试数据依赖冲突 | 使用独立 fixture 隔离 |
| 已删除/重命名模块的引用 | 搜索全项目更新所有引用点 |
| 文件未格式化 | 运行 `ruff format` 自动格式化 |

### 9.4 批量执行策略

**并行判定规则:** Task A 和 Task B 可并行当且仅当:
1. B 不 import A 的任何模块
2. A 不 import B 的任何模块
3. A 和 B 不修改同一文件

```
Phase 1 示例:
  Task 2 (events)  ─┐
  Task 3 (config)   ├── 可并行 (互不依赖)
  Task 4 (logging)  ┘
  Task 5 (protocol) ── 串行 (依赖 Task 2 的 MessageType)
  Task 6 (crypto)   ── 可并行 (仅依赖外部 cryptography 库)
  Task 7 (transport)── 可并行 (仅依赖 Task 2)
  Task 10 (channel) ── 串行 (依赖 Task 5,6,7)
```

**批量操作方式:**
1. 并行组: 同时写入多个测试文件 → 逐一实现 → 全部通过后统一 commit
2. 串行组: 按标准 9.1 流程逐个执行

### 9.5 线性调试轨迹 (Debug Trail)

参考 mini-swe-agent 的 "completely linear history" 原则:
- 每次测试失败/校验失败时，在修复前输出简洁分析:
  ```
  [FIX] Task X: <错误类别> — <具体问题> → <修复方案>
  ```
- 这种线性历史内嵌于 REPORT 中，形成完整的调试链路便于回溯

### 9.6 Phase 间 Gate

进入下一个 Phase 前必须满足:
- [ ] 本 Phase 所有 Task 的测试全部通过
- [ ] `ruff check` 全项目零错误
- [ ] `ruff format --check` 全项目通过
- [ ] `mypy --strict` 全项目通过
- [ ] `pytest tests/ -v` 全项目通过
- [ ] 覆盖率不低于目标值

满足全部条件后，自主进入下一 Phase，输出 Gate 检查结果。
