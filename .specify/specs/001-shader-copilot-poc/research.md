# Research: AI 驱动的 URP Shader 编写助手 (PoC)

**Feature**: `001-shader-copilot-poc`  
**Date**: 2025-12-28  
**Status**: Complete

---

## 1. LangGraph 架构设计

### Decision: 多 Graph 组合架构

**Rationale**: 
- 单一巨型 Graph 难以维护和测试
- 不同任务类型（生成/分析/纹理）有不同的节点流程
- 便于后续扩展新的 Graph（如 ShaderAnalysisGraph）

**Alternatives Considered**:
1. **单一 Graph + 条件分支**: 逻辑集中但复杂度高，难以独立测试
2. **纯链式调用**: 缺乏状态管理和重试能力
3. **多 Graph + Router**: ✅ 选择此方案 - 职责清晰，可独立演进

**Implementation Notes**:
- Router Agent 使用轻量级 LLM 做意图分类
- 每个 Graph 有独立的 State 类
- 共享 SessionState 用于跨 Graph 数据传递

---

## 2. Unity ↔ Python 通信方案

### Decision: WebSocket 双向通信

**Rationale**:
- 支持流式输出（LLM 响应）
- 支持服务端主动推送（进度、状态）
- 低延迟双向通信
- Unity 端可用 WebSocketSharp 或 NativeWebSocket

**Alternatives Considered**:
1. **HTTP REST API**: 不支持流式，需轮询，延迟高
2. **gRPC**: Unity 支持有限，配置复杂
3. **WebSocket**: ✅ 选择 - 简单、流式、双向

**Implementation Notes**:
- Unity 作为 Client，Python 作为 Server
- 消息格式统一用 JSON
- 定义明确的 MessageType 枚举
- 心跳机制保持连接

---

## 3. Unity Editor 扩展方案

### Decision: EditorWindow + ScriptableObject 配置

**Rationale**:
- EditorWindow 是 Unity Editor 扩展的标准方式
- ScriptableObject 便于持久化配置
- 支持 IMGUI 和 UI Toolkit（推荐后者）

**Alternatives Considered**:
1. **纯 IMGUI**: 传统方式，代码量大，样式控制弱
2. **UI Toolkit (UIElements)**: ✅ 选择 - 现代、灵活、可复用
3. **第三方 UI 库**: 增加依赖，维护风险

**Implementation Notes**:
- 使用 UI Toolkit 构建 UI
- USS 文件定义样式
- VisualTreeAsset (UXML) 定义结构
- C# 控制逻辑

---

## 4. Shader 编译验证方案

### Decision: ShaderUtil.CreateShaderAsset + ShaderUtil.ShaderHasError

**Rationale**:
- Unity 内置 API，无需外部依赖
- 可获取详细编译错误信息
- 支持运行时编译（Editor 环境）

**API 选择**:
```csharp
// 编译 Shader
Shader shader = ShaderUtil.CreateShaderAsset(shaderCode);

// 检查错误
bool hasError = ShaderUtil.ShaderHasError(shader);
string[] errors = ShaderUtil.GetShaderMessages(shader);
```

**Implementation Notes**:
- 编译后需检查 hasError
- 错误信息需解析行号用于 Agent 修复
- 成功后创建 Material 实例

---

## 5. 会话持久化方案

### Decision: JSON 文件存储

**Rationale**:
- PoC 阶段无需数据库
- JSON 可读性好，便于调试
- 文件系统存储简单可靠

**存储位置**: `Assets/ShaderCopilot/Sessions/`

**文件格式**:
```json
{
  "session_id": "uuid",
  "created_at": "2025-12-28T10:00:00Z",
  "messages": [
    {
      "role": "user",
      "content": "创建一个卡通着色器",
      "timestamp": "2025-12-28T10:00:01Z"
    },
    {
      "role": "assistant", 
      "content": "...",
      "timestamp": "2025-12-28T10:00:15Z",
      "artifacts": ["Shaders/Toon.shader"]
    }
  ]
}
```

**Implementation Notes**:
- 每个 Session 一个 JSON 文件
- 文件名使用 session_id
- Unity 端和 Python 端都需读写能力

---

## 6. LLM 模型选择

### Decision: Qwen3 系列（可配置）

**Rationale**:
- Qwen3 Max 代码能力强
- Qwen3-VL-Plus 支持图像理解
- 国内访问稳定
- API 兼容 OpenAI 格式

**模型分配**:
| 任务 | 模型 | 说明 |
|------|------|------|
| 路由 | Qwen3-Turbo 或更便宜 | 意图分类，token 少 |
| 代码生成 | Qwen3-Max | Shader 代码生成 |
| 图像理解 | Qwen3-VL-Plus | 参考图分析 |

**Implementation Notes**:
- 使用 litellm 或直接 httpx 调用
- 支持配置切换其他模型（OpenAI, Claude 等）
- API Key 从环境变量读取

---

## 7. 预览场景设计

### Decision: 独立预览场景 + RenderTexture

**Rationale**:
- 不干扰用户正在编辑的场景
- 可控的光照和相机设置
- RenderTexture 便于在 EditorWindow 中显示

**场景结构**:
```
PreviewScene/
├── PreviewCamera         # 预览相机
├── DirectionalLight      # 主光源
├── PreviewObjects/
│   ├── Sphere           # 预设球体
│   ├── Cube             # 预设立方体
│   └── Plane            # 预设平面
└── Background           # 背景（Skybox 或纯色）
```

**Implementation Notes**:
- 使用 EditorSceneManager.OpenPreviewScene
- 相机输出到 RenderTexture
- RenderTexture 在 EditorWindow 中用 GUI.DrawTexture 显示

---

## 8. 错误处理分层

### Decision: 三层错误处理

**层次**:
1. **Infrastructure 层**: 网络超时、文件 IO 错误、API 调用失败
2. **Application 层**: 工作流错误、状态不一致、重试逻辑
3. **Presentation 层**: 用户友好错误提示、重试按钮

**实现策略**:
| 层次 | 处理方式 |
|------|---------|
| Infrastructure | 抛出具体异常，记录日志 |
| Application | 捕获异常，决定重试或上报 |
| Presentation | 显示用户友好消息，提供操作选项 |

**Implementation Notes**:
- Python 端使用自定义 Exception 类
- Unity 端使用 try-catch + 日志
- 错误信息同时记录技术细节和用户消息

---

## 9. 后端进程管理

### Decision: Unity 启动子进程

**Rationale**:
- 后端生命周期跟随 Editor 窗口
- 无需用户手动启动服务
- 简化部署和使用

**实现方式**:
```csharp
Process backendProcess = new Process();
backendProcess.StartInfo.FileName = pythonPath;
backendProcess.StartInfo.Arguments = "main.py";
backendProcess.StartInfo.WorkingDirectory = agentPath;
backendProcess.Start();
```

**Implementation Notes**:
- 窗口打开时启动，关闭时终止
- 检测进程是否存活，死亡时自动重启
- 支持配置 Python 解释器路径

---

## 10. 测试策略

### Decision: 分层测试 + Mock

**Unity 端**:
- Edit Mode Tests: 服务类逻辑测试
- Play Mode Tests: UI 交互测试（有限）
- Mock WebSocket 响应

**Python 端**:
- Unit Tests: 各模块独立测试
- Integration Tests: Graph 流程测试
- Contract Tests: WebSocket 协议测试
- Mock LLM 响应

**覆盖率目标**:
- 单元测试: ≥ 80%
- 关键路径 E2E: 100%

---

## Summary

所有技术决策已明确，无 NEEDS CLARIFICATION 项。主要决策：

1. **架构**: 多 Graph 组合 + Router Agent
2. **通信**: WebSocket 双向通信
3. **UI**: Unity UI Toolkit (EditorWindow)
4. **编译**: ShaderUtil 内置 API
5. **存储**: JSON 文件持久化
6. **模型**: Qwen3 系列（可配置）
7. **预览**: 独立场景 + RenderTexture
8. **错误**: 三层错误处理
9. **进程**: Unity 管理子进程
10. **测试**: 分层测试 + Mock
