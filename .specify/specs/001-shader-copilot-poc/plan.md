# Implementation Plan: AI 驱动的 URP Shader 编写助手 (PoC)

**Branch**: `001-shader-copilot-poc` | **Date**: 2025-12-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-shader-copilot-poc/spec.md`

## Summary

构建一个 AI 驱动的 URP Shader 编写助手 PoC，用户通过对话界面描述需求或上传参考图，系统自动完成 Shader 生成、编译验证、材质创建、效果预览全流程。

技术方案：Unity Editor 扩展 + Python 后端（LangGraph），通过 WebSocket 双向通信，支持流式响应和工具调用。

## Technical Context

**Language/Version**: 
- Unity 端: C# (.NET Standard 2.1, Unity 2021.3+)
- Agent 端: Python 3.11+

**Primary Dependencies**: 
- Unity: URP, Newtonsoft.Json, WebSocketSharp
- Python: LangGraph, websockets, httpx, pydantic

**Storage**: 文件系统（JSON 格式会话持久化）

**Testing**: 
- Unity: Unity Test Framework (Edit Mode + Play Mode)
- Python: pytest + pytest-asyncio

**Target Platform**: Unity Editor (Windows/macOS)

**Project Type**: 双端项目（Unity + Python Backend）

**Performance Goals**: 
- 用户输入到预览效果 < 60s（不含 LLM 响应时间）
- Shader 首次编译成功率 ≥ 70%
- 重试后编译成功率 ≥ 90%

**Constraints**: 
- WebSocket 连接超时 < 10s
- 后端断连自动重连 < 10s
- 单次 LLM 调用超时 < 120s

**Scale/Scope**: PoC 阶段，单用户本地运行

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|-----------|-------|--------|
| I. Readability First | 命名表达业务语义（ShaderCompiler, MaterialManager），无技巧性代码 | ✅ |
| II. System Consistency | 遵循双端架构模式，通信协议统一，无隐式约定 | ✅ |
| III. Stability First | 错误分层处理，重试机制，无静默失败 | ✅ |
| IV. Error Handling | 分层捕获（Unity/Backend/LLM），用户可理解的错误提示 | ✅ |
| V. Single Source of Truth | 状态集中于 SessionState，派生而非复制 | ✅ |
| VI. Separation of Concerns | 四层架构清晰（Presentation/Application/Domain/Infrastructure） | ✅ |
| VII. Testability | 目标单元覆盖率 ≥ 80%，E2E 覆盖关键路径 | ✅ |
| VIII. Technology Governance | 技术选型已确定：Unity+URP, Python+LangGraph+WebSocket | ✅ |
| IX. Convention Clarity | 通信协议、消息类型显式定义 | ✅ |
| X. Documentation Discipline | Docs/ 目录维护，API 契约文档化 | ✅ |

## Project Structure

### Documentation (this feature)

```text
specs/001-shader-copilot-poc/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (WebSocket protocol)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
UnityProject/Assets/ShaderCopilot/
├── Editor/                        # Editor 扩展
│   ├── Window/                    # UI 窗口
│   │   ├── ShaderCopilotWindow.cs
│   │   ├── ChatPanel.cs
│   │   ├── PreviewPanel.cs
│   │   └── SettingsPanel.cs
│   ├── Communication/             # 通信层
│   │   ├── WebSocketClient.cs
│   │   ├── BackendLauncher.cs
│   │   └── MessageHandler.cs
│   └── Services/                  # 业务服务
│       ├── ShaderCompilerService.cs
│       ├── MaterialManagerService.cs
│       ├── PreviewSceneService.cs
│       └── FileManagerService.cs
├── Runtime/                       # 共享运行时（如有需要）
└── Tests/
    ├── Editor/                    # Edit Mode Tests
    └── Runtime/                   # Play Mode Tests

Agent/
├── src/
│   ├── server/                    # WebSocket 服务器
│   │   ├── __init__.py
│   │   ├── websocket_server.py
│   │   └── message_handler.py
│   ├── router/                    # Router Agent (意图分析与任务路由)
│   │   ├── __init__.py
│   │   └── router_agent.py
│   ├── graphs/                    # LangGraph 工作流
│   │   ├── __init__.py
│   │   ├── shader_gen/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py
│   │   │   ├── nodes.py
│   │   │   └── state.py
│   │   └── base/
│   │       └── state.py
│   ├── tools/                     # Tool 实现
│   │   ├── __init__.py
│   │   ├── unity_tools.py         # 调用 Unity 的工具
│   │   └── llm_tools.py           # LLM 相关工具
│   ├── models/                    # 模型管理
│   │   ├── __init__.py
│   │   └── model_manager.py
│   └── session/                   # 会话管理
│       ├── __init__.py
│       └── session_manager.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── pyproject.toml
└── README.md
```

**Structure Decision**: 采用双端项目结构（Unity + Python Backend），通过 WebSocket 通信。Unity 端负责 UI 和执行器，Python 端负责 Agent 逻辑和 LLM 调用。

## Complexity Tracking

> 无需填写 - Constitution Check 未发现需要辩护的违规项
