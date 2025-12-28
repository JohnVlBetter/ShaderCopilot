# Quickstart: AI 驱动的 URP Shader 编写助手 (PoC)

**Feature**: `001-shader-copilot-poc`  
**Status**: ✅ Implementation Complete  
**Date**: 2025-01-15

---

## Prerequisites

### Unity 端
- Unity 2021.3 LTS 或更高版本
- URP (Universal Render Pipeline) 已配置
- .NET Standard 2.1

### Agent 端
- Python 3.11+
- uv 包管理器

### 外部服务
- LLM API 访问（Qwen3 或 OpenAI 兼容 API）
- API Key 配置

---

## Quick Setup

### 1. Clone & Setup

```bash
# Clone 仓库
git clone <repository-url>
cd ShaderCopilot

# 切换到 feature 分支
git checkout 001-shader-copilot-poc
```

### 2. Agent 后端配置

```bash
cd Agent

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.\.venv\Scripts\Activate.ps1

# 激活虚拟环境 (macOS/Linux)
source .venv/bin/activate

# 安装依赖
uv pip install -e .
```

### 3. 环境变量配置

创建 `Agent/.env` 文件：

```env
# LLM API 配置
QWEN_API_KEY=your-api-key-here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 或使用 OpenAI 兼容 API
# OPENAI_API_KEY=your-api-key-here
# OPENAI_BASE_URL=https://api.openai.com/v1

# 服务器配置
WEBSOCKET_HOST=localhost
WEBSOCKET_PORT=8765

# 日志级别
LOG_LEVEL=INFO
```

### 4. Unity 项目配置

1. 打开 Unity Hub
2. 打开 `UnityProject/` 目录
3. 确认 URP 管线已配置
4. 打开菜单 `Window > ShaderCopilot`

---

## Development Workflow

### 启动后端（开发模式）

**使用 UV (推荐)**:
```bash
cd Agent
uv run python -m shader_copilot.server.websocket_server
```

**使用 Python**:
```bash
cd Agent
python -m shader_copilot.server.websocket_server
```

后端将在 `ws://localhost:8765` 启动。

### 启动 Unity

1. 打开 Unity 项目
2. 打开 `Window > ShaderCopilot` 窗口
3. 窗口会自动连接后端（或自动启动后端）

### 运行测试

**Python 测试**:
```bash
cd Agent
pytest tests/ -v
```

**Unity 测试**:
1. 打开 `Window > General > Test Runner`
2. 运行 Edit Mode Tests 和 Play Mode Tests

---

## Project Structure Overview

```
ShaderCopilot/
├── Agent/                         # Python 后端
│   ├── src/
│   │   ├── server/                # WebSocket 服务器
│   │   ├── router/                # Router Agent
│   │   ├── graphs/                # LangGraph 工作流
│   │   │   └── shader_gen/        # Shader 生成图
│   │   ├── tools/                 # Tool 实现
│   │   ├── models/                # 模型管理
│   │   └── session/               # 会话管理
│   ├── tests/
│   ├── pyproject.toml
│   └── .env
│
├── UnityProject/                  # Unity 工程
│   └── Assets/
│       └── ShaderCopilot/
│           ├── Editor/            # Editor 扩展
│           │   ├── Window/        # UI 窗口
│           │   ├── Communication/ # 通信层
│           │   └── Services/      # 业务服务
│           ├── Runtime/           # 运行时组件
│           ├── PreviewScene/      # 预览场景资源
│           └── Tests/             # Unity 测试
│
├── Docs/                          # 项目文档
└── specs/                         # 功能规格
    └── 001-shader-copilot-poc/
        ├── spec.md
        ├── plan.md
        ├── research.md
        ├── data-model.md
        ├── quickstart.md          # 本文件
        └── contracts/
            └── websocket-protocol.md
```

---

## Key Files

### Agent 端

| File | Purpose |
|------|---------|
| `src/server/websocket_server.py` | WebSocket 服务器入口 |
| `src/router/router_agent.py` | 意图路由 Agent |
| `src/graphs/shader_gen/graph.py` | Shader 生成工作流 |
| `src/tools/unity_tools.py` | Unity 工具调用 |
| `src/models/model_manager.py` | LLM 模型管理 |
| `src/session/session_manager.py` | 会话持久化 |

### Unity 端

| File | Purpose |
|------|---------|
| `Editor/Window/ShaderCopilotWindow.cs` | 主窗口 |
| `Editor/Communication/WebSocketClient.cs` | WebSocket 客户端 |
| `Editor/Communication/BackendLauncher.cs` | 后端进程管理 |
| `Editor/Services/ShaderCompilerService.cs` | Shader 编译服务 |
| `Editor/Services/MaterialManagerService.cs` | 材质管理服务 |
| `Editor/Services/PreviewSceneService.cs` | 预览场景服务 |

---

## Configuration

### Unity Settings (ScriptableObject)

```
Assets/ShaderCopilot/Settings/ShaderCopilotSettings.asset
```

| Setting | Default | Description |
|---------|---------|-------------|
| Output Directory | `Assets/Shaders/Generated` | Shader 输出目录 |
| Max Retry Count | 3 | 最大重试次数 |
| Backend Port | 8765 | 后端端口 |
| Auto Start Backend | true | 自动启动后端 |
| Python Path | `python` | Python 解释器路径 |

### Model Configuration

| Model Role | Default | Description |
|------------|---------|-------------|
| Router Model | `qwen-turbo` | 意图路由（轻量级） |
| Code Model | `qwen-max` | 代码生成 |
| VL Model | `qwen-vl-plus` | 图像理解 |

---

## Common Commands

```bash
# Agent 开发
cd Agent
uv run pytest tests/ -v                    # 运行测试
uv run pytest tests/ --cov=shader_copilot  # 测试覆盖率
uv run python -m shader_copilot.server.websocket_server  # 启动服务器

# 代码质量
uv run ruff check src/                     # Linting
uv run ruff format src/                    # Formatting
uv run mypy src/                           # Type checking
```

---

## Troubleshooting

### 后端连接失败

1. 检查后端是否启动：`netstat -an | findstr 8765`
2. 检查防火墙设置
3. 查看后端日志

### LLM API 调用失败

1. 检查 API Key 是否正确
2. 检查网络连接
3. 查看 API 配额

### Shader 编译失败

1. 查看 Unity Console 错误
2. 检查 Shader 代码语法
3. 确认 URP 版本兼容性

---

## Next Steps

1. 阅读 [用户指南](../../../Docs/user-guide.md) 了解如何使用
2. 阅读 [spec.md](spec.md) 了解功能需求
3. 阅读 [data-model.md](data-model.md) 了解数据结构
4. 阅读 [contracts/websocket-protocol.md](contracts/websocket-protocol.md) 了解通信协议
5. 查看 [Agent README](../../../Agent/README.md) 了解后端架构
