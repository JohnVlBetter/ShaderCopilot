# Feature Specification: AI 驱动的 URP Shader 编写助手 (PoC)

**Feature Branch**: `001-shader-copilot-poc`  
**Created**: 2025-12-28  
**Status**: Draft  
**Input**: User description: "为 Unity 开发人员（TA、程序、美术）提供一个 AI 驱动的 URP Shader 编写助手，用户只需描述需求或提供参考图，助手自动完成 Shader 生成、材质创建、纹理生成、效果验证等全流程工作。"

---

## System Architecture

### 通信架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Unity Editor                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    ShaderCopilot Window                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │  │
│  │  │ Chat Panel  │  │ Preview     │  │ Settings Panel      │   │  │
│  │  │ (对话界面)   │  │ (预览区域)  │  │ (模型/目录/重试次数) │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Unity Executor (执行器)                     │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐   │  │
│  │  │ Shader   │ │ Material │ │ Preview  │ │ File Manager   │   │  │
│  │  │ Compiler │ │ Manager  │ │ Scene    │ │ (读写文件)      │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              WebSocket Client + Backend Launcher              │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ WebSocket
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Python Backend                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     WebSocket Server                          │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │           Router Agent (意图分析与任务路由)                    │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐   │
│  │ ShaderGenGraph  │ │ShaderAnalysisGra│ │ TextureGenGraph     │   │
│  │ (生成Shader)    │ │ph(分析/优化/问答)│ │ (生成纹理)          │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────────┘   │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                        Tools Layer                            │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Model Manager (多模型管理/自动路由)               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Session Manager (会话持久化)                      │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ HTTP API
                                   ▼
                    ┌─────────────────────────────┐
                    │         ComfyUI             │
                    └─────────────────────────────┘
```

### 技术栈

| 模块 | 技术选型 | 说明 |
|------|---------|------|
| Unity Project | Unity + URP | 参见 ProjectSettings |
| Agent Backend | Python + WebSocket | 异步通信，支持流式响应 |
| Agent Framework | LangGraph | 工作流编排，支持多图协作 |
| LLM Integration | 多模型支持 | 路由模型 / 代码模型 / VL 模型 |
| 纹理生成 | ComfyUI (可选) | HTTP API 调用 |

### 模块结构

**Unity 端**

```
UnityProject/Assets/ShaderCopilot/
├── Editor/                        # Editor 扩展
│   ├── Window/                    # UI 窗口
│   │   ├── ShaderCopilotWindow    # 主窗口入口
│   │   ├── ChatPanel              # 对话界面
│   │   ├── PreviewPanel           # 预览区域
│   │   └── SettingsPanel          # 设置面板
│   ├── Communication/             # 通信层
│   │   ├── WebSocketClient        # 与后端通信
│   │   ├── BackendLauncher        # 后端进程管理
│   │   └── MessageHandler         # 消息处理
│   └── Services/                  # 业务服务
│       ├── ShaderCompilerService  # Shader 编译验证
│       ├── MaterialManagerService # 材质创建与管理
│       ├── PreviewSceneService    # 预览场景控制
│       └── FileManagerService     # 文件读写操作
├── Tests/                         # 测试
│   └── Editor/                    # Edit Mode Tests
└── PreviewScene/                  # 预览场景资源
```

**Agent 端**

```
Agent/
├── server/                    # WebSocket 服务器
├── router/                    # Router Agent (任务分发)
├── graphs/                    # LangGraph 工作流
│   ├── shader_gen/            # Shader 生成图
│   ├── shader_analysis/       # Shader 分析/优化图
│   └── texture_gen/           # 纹理生成图
├── tools/                     # Tool 实现
├── models/                    # 模型管理器
└── session/                   # 会话持久化
```

### 模型管理策略

| 策略 | 说明 |
|------|------|
| 自动路由 | 图像理解任务 → VL 模型，纯文本/代码任务 → 文本模型 |
| 用户覆盖 | 用户可在设置中指定使用特定模型 |
| 运行时切换 | 支持运行时动态切换模型 |
| 模型配置 | 路由模型、代码模型、VL 模型分别可配置 |

**默认模型配置**:
- 路由模型 (router_model): `qwen-turbo` - 轻量级，用于意图分类
- 代码模型 (code_model): `qwen-max` - 高质量代码生成
- VL 模型 (vl_model): `qwen-vl-plus` - 图像理解与分析

### 错误处理与重试策略

| 策略 | 说明 |
|------|------|
| 重试次数 | 可配置（默认 3 次） |
| 重试判断 | Agent 自主判断：语法错误 → 修复代码重试；完全不符合 → 重新生成 |
| 超限处理 | 达到最大重试次数后询问用户 |

### Human-in-the-Loop 介入点

| 介入点 | 说明 |
|--------|------|
| 最终效果确认 | 生成完成后，用户确认效果是否符合预期 |
| 重试超限 | 自动重试失败后，询问用户如何处理 |
| 关键决策 | 涉及重大修改时（如覆盖现有文件）询问用户 |

> 中间步骤（编译、截图等）自动执行，不打断用户。

---

## LangGraph 设计

### Graph 结构

采用**多 Graph 组合**架构：

| Graph | 职责 |
|-------|------|
| Router Agent | 分析用户意图，路由到对应 Graph |
| ShaderGenGraph | 生成 Shader、创建材质、验证效果 |
| ShaderAnalysisGraph | 分析现有 Shader、问答、优化、修 Bug（PoC 后续） |
| TextureGenGraph | 调用 ComfyUI 或程序化生成纹理（PoC 后续） |

**Graph 协作方式**：并行 + 等待
- ShaderGenGraph 声明需要的纹理槽位
- TextureGenGraph 并行生成纹理
- 纹理生成后自动绑定到材质

### 状态设计

```python
# 全局共享状态
class SessionState:
    conversation_history: List[Message]  # 对话历史
    project_path: str                     # Unity 项目路径
    output_directory: str                 # 用户指定的输出目录
    current_task_id: str                  # 当前任务 ID

# ShaderGenGraph 状态
class ShaderGenState:
    user_requirement: str                 # 用户需求描述
    reference_image: Optional[bytes]      # 参考效果图
    image_analysis: Optional[str]         # VL 模型分析结果
    generated_code: str                   # 生成的 Shader 代码
    compile_result: CompileResult         # 编译结果
    material_id: str                      # 创建的材质 ID
    screenshot: bytes                     # 预览截图
    retry_count: int                      # 当前重试次数
    pending_textures: List[TextureSlot]   # 等待生成的纹理槽位

# TextureGenGraph 状态
class TextureGenState:
    texture_requirements: List[TextureReq]  # 纹理需求列表
    generation_method: str                  # comfyui / procedural
    generated_textures: List[TextureResult] # 生成结果

# ShaderAnalysisGraph 状态
class ShaderAnalysisState:
    shader_code: str                      # 待分析的 Shader 代码
    analysis_type: str                    # bug_fix / optimize / explain / qa
    analysis_result: str                  # 分析结果
    suggested_code: Optional[str]         # 建议的修改代码
```

---

## Tools 定义

| Tool | 执行位置 | 说明 |
|------|----------|------|
| `generate_shader_code` | 后端（LLM） | 生成 Shader 代码 |
| `analyze_image` | 后端（VL 模型） | 分析参考效果图 |
| `compile_shader` | Unity | 编译 Shader 并返回结果 |
| `save_shader` | Unity | 保存 Shader 文件 |
| `save_material` | Unity | 保存材质文件 |
| `create_material` | Unity | 创建材质球 |
| `set_material_texture` | Unity | 设置材质纹理 |
| `apply_to_preview` | Unity | 应用材质到预览物体 |
| `capture_screenshot` | Unity | 截取预览场景截图（用于效果验证） |
| `save_texture` | Unity | 保存纹理文件（PoC 后续） |
| `read_shader` | Unity | 读取 Shader 文件（用于迭代修改时获取上下文） |
| `list_preview_objects` | Unity | 列出可用预览物体 |
| `switch_preview_object` | Unity | 切换预览物体 |
| `set_background` | Unity | 设置背景 |
| `generate_texture_comfyui` | 后端 → ComfyUI | 调用 ComfyUI 生成纹理（PoC 后续） |
| `generate_texture_procedural` | 后端 | 程序化生成纹理（PoC 后续） |
| `run_mali_compiler` | 后端 | 调用 Mali Offline Compiler（PoC 后续） |
| `check_comfyui_available` | 后端 | 检测 ComfyUI 是否可用（PoC 后续） |

---

## Unity ↔ Backend 通信协议

### 指令协议（Backend → Unity）

| 指令类型 | 参数 | 返回 |
|----------|------|------|
| `compile_shader` | shader_code, shader_name | success, errors[] |
| `save_shader` | shader_code, file_path | success, file_path |
| `create_material` | shader_name, properties | material_id |
| `set_material_texture` | material_id, slot_name, texture_path | success |
| `apply_to_preview` | material_id, preview_object | success |
| `capture_screenshot` | camera_settings | image_bytes |
| `save_texture` | texture_bytes, file_path, format | success, file_path |
| `read_shader` | file_path | shader_code |
| `list_preview_objects` | - | object_names[] |
| `switch_preview_object` | object_name | success |
| `set_background` | background_type, params | success |

### 消息协议（Backend → Unity 推送）

```python
class MessageType(Enum):
    THINKING = "thinking"           # Agent 正在思考
    TOOL_CALL = "tool_call"         # 调用工具
    TOOL_RESULT = "tool_result"     # 工具返回结果
    STREAM_TEXT = "stream_text"     # 流式文本输出
    PROGRESS = "progress"           # 进度更新
    REQUIRE_CONFIRM = "require_confirm"  # 需要用户确认
    COMPLETE = "complete"           # 任务完成
    ERROR = "error"                 # 错误
```

---

## 存储设计

| 内容 | 位置 |
|------|------|
| 助手预设资源 | `Assets/ShaderCopilot/` |
| 预览场景 | `Assets/ShaderCopilot/PreviewScene/` |
| 会话历史 | `Assets/ShaderCopilot/Sessions/` |
| 生成的 Shader | 用户指定目录 |
| 生成的材质 | 用户指定目录 |
| 生成的纹理 | 用户指定目录 |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 文本描述生成 Shader (Priority: P1)

用户在对话界面输入 Shader 需求描述（如"我需要一个卡通风格的水面效果"），系统自动生成 URP Shader 代码，编译验证，创建材质，并在预览场景中展示效果。

**Why this priority**: 这是核心功能，验证 AI 生成 Shader 的可行性，是整个产品的价值基础。

**Independent Test**: 用户输入一句话需求，系统输出可编译的 Shader 并在预览窗口显示效果，即可验证此功能完整性。

**Acceptance Scenarios**:

1. **Given** 用户打开 ShaderCopilot 窗口且后端已连接, **When** 用户输入"创建一个简单的卡通着色器", **Then** 系统生成 Shader 代码、自动编译成功、创建材质并在预览区域显示效果
2. **Given** 用户已输入需求, **When** 生成的 Shader 编译失败, **Then** Agent 自动分析错误并尝试修复（最多重试 3 次），修复成功后继续流程
3. **Given** 用户已输入需求, **When** 重试次数达到上限仍失败, **Then** 系统询问用户是否继续尝试或提供更多描述

---

### User Story 2 - 参考图分析生成 Shader (Priority: P1)

用户上传一张效果参考图，系统分析图片特征（颜色、光照、纹理风格等），自动生成匹配该效果的 Shader。

**Why this priority**: 与文本描述同等重要，美术用户更习惯通过图片表达需求，是差异化能力的关键。

**Independent Test**: 用户上传一张效果图，系统生成的 Shader 在预览窗口产生视觉上接近参考图的效果。

**Acceptance Scenarios**:

1. **Given** 用户打开 ShaderCopilot 窗口, **When** 用户上传一张卡通渲染风格的效果图, **Then** 系统分析图片并生成匹配风格的 Shader，预览效果与参考图风格相似
2. **Given** 用户上传了效果图, **When** VL 模型无法识别图片内容, **Then** 系统提示用户提供更清晰的图片或补充文字描述
3. **Given** 用户同时提供效果图和文字描述, **When** 系统处理请求, **Then** 综合图片分析结果和文字描述生成 Shader

---

### User Story 3 - 效果确认与迭代 (Priority: P2)

用户查看生成的效果后，可以通过对话方式请求调整（如"把高光范围调大一点"），系统根据反馈修改 Shader。

**Why this priority**: 用户很少一次满意，迭代能力是实际可用性的保障。

**Independent Test**: 在已生成 Shader 的基础上，用户提出修改意见，系统生成修改后的版本并更新预览。

**Acceptance Scenarios**:

1. **Given** 系统已生成一个 Shader 并预览, **When** 用户说"把边缘光的颜色改成蓝色", **Then** 系统修改 Shader 并更新预览，边缘光变为蓝色
2. **Given** 系统已生成一个 Shader, **When** 用户确认"效果可以，保存吧", **Then** 系统保存 Shader 文件和材质到用户指定目录

---

### User Story 4 - 会话管理 (Priority: P3)

用户可以查看历史对话，继续之前的工作，或开始新的会话。

**Why this priority**: 提升用户体验，但不影响核心功能验证。

**Independent Test**: 用户关闭 Unity 后重新打开，能看到之前的对话记录并继续工作。

**Acceptance Scenarios**:

1. **Given** 用户有历史会话记录, **When** 用户打开 ShaderCopilot 窗口, **Then** 显示之前的对话历史
2. **Given** 用户正在进行对话, **When** 用户点击"新建会话", **Then** 当前会话保存，开始新的空白会话

---

### User Story 5 - 预览场景配置 (Priority: P3)

用户可以切换预览物体（球体、立方体、平面等）和背景，以便在不同条件下查看 Shader 效果。

**Why this priority**: 提升验证效果的灵活性，但基础预设即可满足 PoC 需求。

**Independent Test**: 用户切换预览物体，材质自动应用到新物体上并更新显示。

**Acceptance Scenarios**:

1. **Given** 当前预览物体是球体, **When** 用户选择切换到立方体, **Then** 预览区域显示应用了当前材质的立方体
2. **Given** 当前背景是纯色, **When** 用户选择渐变背景, **Then** 预览区域背景更新为渐变

---

### Edge Cases

- 用户输入的描述过于模糊（如"好看的效果"）：系统提示用户提供更具体的描述或参考图
- 用户上传的图片格式不支持或损坏：系统提示格式要求
- 后端进程意外退出：Unity 端检测到断连后尝试自动重启后端
- 用户请求生成的 Shader 超出 URP 能力范围：系统说明限制并建议替代方案
- 网络超时或 LLM 服务不可用：系统显示错误状态并允许重试

---

## Requirements *(mandatory)*

### Functional Requirements

**对话与交互**
- **FR-001**: 系统 MUST 提供对话界面，支持用户输入文本描述
- **FR-002**: 系统 MUST 支持用户上传图片作为参考
- **FR-003**: 系统 MUST 支持流式显示 AI 响应内容
- **FR-004**: 系统 MUST 保持对话上下文，支持多轮交互

**Shader 生成**
- **FR-005**: 系统 MUST 能根据文本描述生成 URP 兼容的 Shader 代码
- **FR-006**: 系统 MUST 能分析参考图并生成匹配风格的 Shader
- **FR-007**: 系统 MUST 自动编译生成的 Shader 并返回编译结果
- **FR-008**: 系统 MUST 在编译失败时自动尝试修复（可配置重试次数，默认 3 次）

**材质与预览**
- **FR-009**: 系统 MUST 自动创建使用生成 Shader 的材质
- **FR-010**: 系统 MUST 将材质应用到预览物体并显示效果
- **FR-011**: 系统 MUST 支持截取预览场景截图
- **FR-012**: 系统 MUST 提供预设预览物体（球体、立方体、平面）

**文件管理**
- **FR-013**: 系统 MUST 能保存 Shader 文件到用户指定目录
- **FR-014**: 系统 MUST 能保存材质文件到用户指定目录
- **FR-015**: 覆盖已存在文件前 MUST 询问用户确认

**后端管理**
- **FR-016**: Unity 打开 ShaderCopilot 窗口时 MUST 自动启动后端进程
- **FR-017**: 后端进程生命周期 MUST 跟随 Editor 窗口
- **FR-018**: 系统 MUST 通过 WebSocket 实现 Unity 与后端通信

**会话管理**
- **FR-019**: 系统 MUST 持久化会话历史
- **FR-020**: 系统 MUST 支持新建会话

**配置**
- **FR-021**: 用户 MUST 能配置 Shader 输出目录
- **FR-022**: 用户 MUST 能配置重试次数
- **FR-023**: 用户 MUST 能选择使用的 LLM 模型

---

### Key Entities

- **Session（会话）**: 用户与系统的一次完整交互过程，包含消息列表、创建时间、状态
- **Message（消息）**: 对话中的单条消息，包含角色（用户/助手）、内容（文本/图片）、时间戳
- **ShaderAsset（Shader 资产）**: 生成的 Shader 文件，包含代码内容、编译状态、关联材质
- **MaterialAsset（材质资产）**: 创建的材质，包含使用的 Shader、纹理引用、参数值
- **PreviewConfig（预览配置）**: 预览场景设置，包含当前物体类型、背景设置、相机参数

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户从输入需求到看到预览效果，整个流程在 60 秒内完成（不含 LLM 响应时间）
- **SC-002**: 生成的 Shader 首次编译成功率达到 70% 以上
- **SC-003**: 经过自动重试后，Shader 编译成功率达到 90% 以上
- **SC-004**: 用户能在 3 轮对话内完成一个满意的 Shader 效果
- **SC-005**: 系统在 Unity Editor 中稳定运行，无崩溃或卡死
- **SC-006**: 后端断连后，系统能在 10 秒内自动恢复连接

---

## Assumptions

- 用户已安装 Unity 2021.3+ 并配置 URP 管线
- 用户已配置可用的 LLM API（支持文本和视觉理解）
- 生成的 Shader 限于 URP Lit/Unlit 基础上的变体，不涉及自定义渲染管线
- PoC 阶段不支持复杂的后处理效果或多 Pass 渲染

---

## Out of Scope (PoC)

- ComfyUI 纹理生成集成
- 程序化纹理生成
- Mali Offline Compiler 性能分析
- Shader 代码分析/优化/问答
- 复杂预览场景（多物体、动态光照、动画）
- 多用户协作
- Shader 版本管理
