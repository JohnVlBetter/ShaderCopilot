# Tasks: AI 驱动的 URP Shader 编写助手 (PoC)

**Input**: Design documents from `/specs/001-shader-copilot-poc/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are included for core functionality to ensure stability per Constitution Principle VII.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Unity**: `UnityProject/Assets/ShaderCopilot/`
- **Agent**: `Agent/src/`
- **Tests Unity**: `UnityProject/Assets/ShaderCopilot/Tests/`
- **Tests Agent**: `Agent/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for both Unity and Agent

- [x] T001 Create Agent Python project structure with pyproject.toml in Agent/
- [x] T002 [P] Create Unity ShaderCopilot folder structure in UnityProject/Assets/ShaderCopilot/
- [x] T003 [P] Configure Python dependencies (langgraph, websockets, httpx, pydantic) in Agent/pyproject.toml
- [x] T004 [P] Add Newtonsoft.Json package reference to Unity project (using native WebSocket)
- [x] T005 [P] Create .env.example with LLM API configuration template in Agent/.env.example
- [x] T006 [P] Create ShaderCopilotSettings ScriptableObject in UnityProject/Assets/ShaderCopilot/Editor/Settings/ShaderCopilotSettings.cs

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Communication Layer

- [x] T007 Implement WebSocket server entry point in Agent/src/server/websocket_server.py
- [x] T008 Implement message handler with JSON parsing in Agent/src/server/message_handler.py
- [x] T009 [P] Define message type enums and base message models in Agent/src/server/messages.py
- [x] T010 Implement WebSocket client for Unity in UnityProject/Assets/ShaderCopilot/Editor/Communication/WebSocketClient.cs
- [x] T011 [P] Implement message handler for Unity in UnityProject/Assets/ShaderCopilot/Editor/Communication/MessageHandler.cs
- [x] T012 Implement backend process launcher in UnityProject/Assets/ShaderCopilot/Editor/Communication/BackendLauncher.cs

### Data Models

- [x] T013 [P] Define SessionState and base state models in Agent/src/graphs/base/state.py
- [x] T014 [P] Define ShaderGenState in Agent/src/graphs/shader_gen/state.py
- [x] T015 [P] Define message and entity models in Agent/src/models/entities.py

### Model Management

- [x] T016 Implement ModelManager with multi-model routing in Agent/src/models/model_manager.py
- [x] T017 [P] Add LLM configuration loading from environment in Agent/src/models/config.py

### Unity Services (Core)

- [x] T018 Implement ShaderCompilerService with ShaderUtil API in UnityProject/Assets/ShaderCopilot/Editor/Services/ShaderCompilerService.cs
- [x] T019 [P] Implement MaterialManagerService in UnityProject/Assets/ShaderCopilot/Editor/Services/MaterialManagerService.cs
- [x] T020 [P] Implement FileManagerService in UnityProject/Assets/ShaderCopilot/Editor/Services/FileManagerService.cs

### Tests for Foundational

- [x] T021 [P] Unit tests for WebSocket message parsing in Agent/tests/unit/test_message_parsing.py
- [x] T022 [P] Unit tests for ShaderCompilerService in UnityProject/Assets/ShaderCopilot/Tests/Editor/ShaderCompilerServiceTests.cs
- [x] T023 Contract tests for WebSocket protocol in Agent/tests/contract/test_websocket_protocol.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 文本描述生成 Shader (Priority: P1) 🎯 MVP

**Goal**: 用户输入文本描述，系统生成 Shader 并预览效果

**Independent Test**: 输入"创建一个简单的卡通着色器" → 生成可编译 Shader → 预览显示效果

### Tests for User Story 1

- [x] T024 [P] [US1] Integration test for text-to-shader flow in Agent/tests/integration/test_shader_gen_flow.py
- [x] T025 [P] [US1] E2E test for compile and preview in UnityProject/Assets/ShaderCopilot/Tests/Editor/TextToShaderE2ETests.cs

### Implementation for User Story 1

- [x] T026 [US1] Implement Router Agent for intent classification in Agent/src/router/router_agent.py
- [x] T027 [US1] Implement ShaderGenGraph main graph in Agent/src/graphs/shader_gen/graph.py
- [x] T028 [US1] Implement ShaderGenGraph nodes (analyze, generate, validate) in Agent/src/graphs/shader_gen/nodes.py
- [x] T029 [P] [US1] Implement generate_shader_code LLM tool in Agent/src/tools/llm_tools.py
- [x] T030 [US1] Implement Unity tool wrappers (compile, create_material, apply_to_preview) in Agent/src/tools/unity_tools.py
- [x] T030a [P] [US1] Implement capture_screenshot tool in Agent/src/tools/unity_tools.py
- [x] T031 [US1] Implement PreviewSceneService (including screenshot capture) in UnityProject/Assets/ShaderCopilot/Editor/Services/PreviewSceneService.cs
- [x] T032 [P] [US1] Create preview scene with Sphere/Cube/Plane prefabs in UnityProject/Assets/ShaderCopilot/PreviewScene/
- [x] T033 [US1] Implement ChatPanel UI with text input in UnityProject/Assets/ShaderCopilot/Editor/Window/ChatPanel.cs
- [x] T034 [P] [US1] Implement PreviewPanel UI with RenderTexture display in UnityProject/Assets/ShaderCopilot/Editor/Window/PreviewPanel.cs
- [x] T035 [US1] Implement ShaderCopilotWindow main entry in UnityProject/Assets/ShaderCopilot/Editor/Window/ShaderCopilotWindow.cs
- [x] T036 [US1] Implement retry logic with error feedback in Agent/src/graphs/shader_gen/nodes.py (retry node)
- [x] T037 [US1] Add streaming text display to ChatPanel in UnityProject/Assets/ShaderCopilot/Editor/Window/ChatPanel.cs

**Checkpoint**: User Story 1 complete - text description to Shader generation works end-to-end

---

## Phase 4: User Story 2 - 参考图分析生成 Shader (Priority: P1) 🎯 MVP

**Goal**: 用户上传参考图，系统分析并生成匹配风格的 Shader

**Independent Test**: 上传卡通风格效果图 → 分析图片 → 生成匹配 Shader → 预览显示

### Tests for User Story 2

- [x] T038 [P] [US2] Unit test for image analysis tool in Agent/tests/unit/test_image_analysis.py
- [x] T039 [P] [US2] Integration test for image-to-shader flow in Agent/tests/integration/test_image_shader_flow.py

### Implementation for User Story 2

- [x] T040 [US2] Implement analyze_image VL tool in Agent/src/tools/llm_tools.py
- [x] T041 [US2] Add image handling node to ShaderGenGraph in Agent/src/graphs/shader_gen/nodes.py (analyze_image node)
- [x] T042 [US2] Update Router Agent to detect image input in Agent/src/router/router_agent.py
- [x] T043 [US2] Add image upload UI to ChatPanel in UnityProject/Assets/ShaderCopilot/Editor/Window/ChatPanel.cs
- [x] T044 [P] [US2] Implement image encoding/decoding utilities in Agent/src/utils/image_utils.py
- [x] T045 [US2] Add combined text+image handling to ShaderGenGraph in Agent/src/graphs/shader_gen/graph.py

**Checkpoint**: User Story 2 complete - image reference to Shader generation works

---

## Phase 5: User Story 3 - 效果确认与迭代 (Priority: P2)

**Goal**: 用户可以通过对话迭代改进 Shader

**Independent Test**: 生成 Shader 后说"把边缘光改成蓝色" → Shader 更新 → 预览刷新

### Tests for User Story 3

- [x] T046 [P] [US3] Integration test for iterative modification in Agent/tests/integration/test_shader_iteration.py

### Implementation for User Story 3

- [x] T047 [US3] Implement SessionManager for conversation history in Agent/src/session/session_manager.py
- [x] T048 [US3] Add context awareness to ShaderGenGraph (reference previous code) in Agent/src/graphs/shader_gen/nodes.py
- [x] T049 [US3] Implement save_shader and save_material tools in Agent/src/tools/unity_tools.py
- [x] T050 [US3] Add save confirmation dialog to ChatPanel in UnityProject/Assets/ShaderCopilot/Editor/Window/ChatPanel.cs
- [x] T051 [US3] Implement file overwrite confirmation handling in UnityProject/Assets/ShaderCopilot/Editor/Services/FileManagerService.cs

**Checkpoint**: User Story 3 complete - users can iterate and save their work

---

## Phase 6: User Story 4 - 会话管理 (Priority: P3)

**Goal**: 用户可以查看历史会话并继续之前的工作

**Independent Test**: 关闭 Unity → 重新打开 → 看到之前的对话历史

### Tests for User Story 4

- [x] T052 [P] [US4] Unit test for session persistence in Agent/tests/unit/test_session_manager.py

### Implementation for User Story 4

- [x] T053 [US4] Implement session JSON file persistence in Agent/src/session/session_manager.py
- [x] T054 [P] [US4] Create Sessions folder structure in UnityProject/Assets/ShaderCopilot/Sessions/
- [x] T055 [US4] Add session list UI to ShaderCopilotWindow in UnityProject/Assets/ShaderCopilot/Editor/Window/ShaderCopilotWindow.cs
- [x] T056 [US4] Implement new session / load session logic in UnityProject/Assets/ShaderCopilot/Editor/Window/ShaderCopilotWindow.cs

**Checkpoint**: User Story 4 complete - session history works

---

## Phase 7: User Story 5 - 预览场景配置 (Priority: P3)

**Goal**: 用户可以切换预览物体和背景

**Independent Test**: 切换到立方体 → 预览更新为立方体

### Tests for User Story 5

- [x] T057 [P] [US5] Unit test for preview object switching in UnityProject/Assets/ShaderCopilot/Tests/Editor/PreviewSceneServiceTests.cs

### Implementation for User Story 5

- [x] T058 [US5] Implement list_preview_objects and switch_preview_object tools in Agent/src/tools/unity_tools.py
- [x] T059 [US5] Implement set_background tool in Agent/src/tools/unity_tools.py
- [x] T060 [US5] Add preview config UI to SettingsPanel in UnityProject/Assets/ShaderCopilot/Editor/Window/SettingsPanel.cs
- [x] T061 [US5] Extend PreviewSceneService with background control in UnityProject/Assets/ShaderCopilot/Editor/Services/PreviewSceneService.cs

**Checkpoint**: User Story 5 complete - preview scene is configurable

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, documentation, and final quality checks

- [x] T062 Add comprehensive error handling to all Unity services in UnityProject/Assets/ShaderCopilot/Editor/Services/*.cs
- [x] T063 [P] Add comprehensive error handling to all Agent modules in Agent/src/**/*.py
- [x] T064 [P] Implement connection health check and auto-reconnect in UnityProject/Assets/ShaderCopilot/Editor/Communication/WebSocketClient.cs
- [x] T065 [P] Add logging throughout Agent codebase in Agent/src/**/*.py
- [x] T066 [P] Add logging throughout Unity codebase in UnityProject/Assets/ShaderCopilot/Editor/**/*.cs
- [x] T067 Create Agent README with setup instructions in Agent/README.md
- [x] T068 [P] Create user documentation in Docs/user-guide.md
- [x] T069 Final integration test covering all user stories in Agent/tests/integration/test_full_flow.py
- [x] T070 Update quickstart.md with final paths and commands in specs/001-shader-copilot-poc/quickstart.md

**Checkpoint**: All phases complete - PoC implementation finished!

---

## Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ← All must complete before user stories
    ↓
┌───────────────────────────────────────┐
│  Phase 3 (US1) ←─── MVP Core          │
│       ↓                               │
│  Phase 4 (US2) ←─── MVP Extension     │
│       ↓                               │
│  Phase 5 (US3) ←─── Iteration         │
└───────────────────────────────────────┘
    ↓
Phase 6 (US4) + Phase 7 (US5) ← Can run in parallel
    ↓
Phase 8 (Polish)
```

## Parallel Execution Examples

### Phase 2 Parallelization

```
T007 (WS Server) ──┐
T008 (Msg Handler)─┼─→ T010 (WS Client)
T009 (Messages) ───┘
                       
T013 (SessionState) ─┬→ T014 (ShaderGenState)
                     └→ T015 (Entities)

T018 (ShaderCompiler) ─┬→ T019 (MaterialManager)
                       └→ T020 (FileManager)
```

### Phase 3 (US1) Parallelization

```
T024 (Test) ────────┐
T025 (E2E Test) ────┤
T029 (LLM Tool) ────┼─→ T026 (Router) → T027 (Graph) → T028 (Nodes)
T032 (Prefabs) ─────┤
T034 (Preview UI) ──┘
```

---

## Implementation Strategy

### MVP Scope (US1 + US2)

1. Complete Phase 1-2 (Setup + Foundational)
2. Complete Phase 3 (US1 - Text to Shader) ← **First demo milestone**
3. Complete Phase 4 (US2 - Image to Shader) ← **MVP complete**

### Full PoC Scope

4. Complete Phase 5 (US3 - Iteration)
5. Complete Phase 6-7 (US4 + US5 - Session + Preview) in parallel
6. Complete Phase 8 (Polish)

---

## Summary

| Phase | Task Count | Parallel Opportunities |
|-------|------------|----------------------|
| Phase 1: Setup | 6 | 4 |
| Phase 2: Foundational | 17 | 10 |
| Phase 3: US1 (P1) | 15 | 5 |
| Phase 4: US2 (P1) | 8 | 3 |
| Phase 5: US3 (P2) | 6 | 1 |
| Phase 6: US4 (P3) | 5 | 2 |
| Phase 7: US5 (P3) | 5 | 1 |
| Phase 8: Polish | 9 | 5 |
| **Total** | **71** | **31** |

### Suggested MVP (US1 only)

- Phase 1: T001-T006 (6 tasks)
- Phase 2: T007-T023 (17 tasks)  
- Phase 3: T024-T037 (15 tasks)
- **MVP Total: 38 tasks**
