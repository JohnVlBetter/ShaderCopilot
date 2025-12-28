# Data Model: AI 驱动的 URP Shader 编写助手 (PoC)

**Feature**: `001-shader-copilot-poc`  
**Date**: 2025-12-28  
**Status**: Complete

---

## Entity Overview

```
┌─────────────┐       ┌─────────────┐       ┌─────────────────┐
│   Session   │ 1───* │   Message   │       │  ShaderAsset    │
├─────────────┤       ├─────────────┤       ├─────────────────┤
│ session_id  │       │ message_id  │       │ asset_id        │
│ created_at  │       │ role        │       │ shader_name     │
│ updated_at  │       │ content     │       │ code            │
│ status      │       │ timestamp   │       │ compile_status  │
│ config      │       │ artifacts   │       │ file_path       │
└─────────────┘       │ images      │       │ created_at      │
                      └─────────────┘       └─────────────────┘
                                                    │
                                                    │ 1
                                                    ▼
                                            ┌─────────────────┐
                                            │ MaterialAsset   │
                                            ├─────────────────┤
                                            │ asset_id        │
                                            │ material_name   │
                                            │ shader_ref      │
                                            │ properties      │
                                            │ file_path       │
                                            └─────────────────┘

┌─────────────────┐
│ PreviewConfig   │
├─────────────────┤
│ object_type     │
│ background_type │
│ camera_settings │
└─────────────────┘
```

---

## Entity Definitions

### Session（会话）

用户与系统的一次完整交互过程。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | string (UUID) | ✅ | 唯一标识符 |
| created_at | datetime | ✅ | 创建时间 |
| updated_at | datetime | ✅ | 最后更新时间 |
| status | SessionStatus | ✅ | 会话状态 |
| config | SessionConfig | ✅ | 会话配置 |
| messages | List[Message] | ✅ | 消息列表 |

**SessionStatus 枚举**:
- `active`: 活跃会话
- `completed`: 已完成
- `archived`: 已归档

**会话文件命名约定**:
- 文件路径: `Assets/ShaderCopilot/Sessions/{session_id}.json`
- 文件名格式: `{UUID}.json`，例如 `550e8400-e29b-41d4-a716-446655440000.json`
- 会话索引: `Assets/ShaderCopilot/Sessions/index.json` 存储所有会话的元数据列表

**SessionConfig**:
```python
class SessionConfig:
    output_directory: str       # Shader/材质输出目录
    max_retry_count: int        # 最大重试次数 (default: 3)
    model_config: ModelConfig   # 模型配置
```

---

### Message（消息）

对话中的单条消息。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| message_id | string (UUID) | ✅ | 唯一标识符 |
| role | MessageRole | ✅ | 消息角色 |
| content | string | ✅ | 消息文本内容 |
| timestamp | datetime | ✅ | 消息时间戳 |
| images | List[ImageData] | ❌ | 附带的图片 |
| artifacts | List[string] | ❌ | 关联的资产路径 |
| metadata | Dict | ❌ | 扩展元数据 |

**MessageRole 枚举**:
- `user`: 用户消息
- `assistant`: 助手消息
- `system`: 系统消息

**ImageData**:
```python
class ImageData:
    image_id: str           # 图片标识
    data: bytes             # 图片二进制数据
    mime_type: str          # MIME 类型 (image/png, image/jpeg)
    thumbnail: Optional[bytes]  # 缩略图
```

---

### ShaderAsset（Shader 资产）

生成的 Shader 文件。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| asset_id | string (UUID) | ✅ | 唯一标识符 |
| shader_name | string | ✅ | Shader 名称 |
| code | string | ✅ | Shader 源代码 |
| compile_status | CompileStatus | ✅ | 编译状态 |
| compile_errors | List[CompileError] | ❌ | 编译错误列表 |
| file_path | string | ❌ | 保存的文件路径 |
| created_at | datetime | ✅ | 创建时间 |
| version | int | ✅ | 版本号（迭代计数） |

**CompileStatus 枚举**:
- `pending`: 待编译
- `compiling`: 编译中
- `success`: 编译成功
- `failed`: 编译失败

**CompileError**:
```python
class CompileError:
    line: int               # 错误行号
    column: int             # 错误列号
    message: str            # 错误消息
    severity: str           # error / warning
```

---

### MaterialAsset（材质资产）

创建的材质。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| asset_id | string (UUID) | ✅ | 唯一标识符 |
| material_name | string | ✅ | 材质名称 |
| shader_ref | string | ✅ | 关联的 Shader asset_id |
| properties | Dict[str, PropertyValue] | ✅ | 材质属性 |
| textures | Dict[str, string] | ❌ | 纹理槽位映射 |
| file_path | string | ❌ | 保存的文件路径 |
| created_at | datetime | ✅ | 创建时间 |

**PropertyValue**:
```python
class PropertyValue:
    type: str       # float, color, vector, texture
    value: Any      # 具体值
```

---

### PreviewConfig（预览配置）

预览场景设置。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| object_type | PreviewObjectType | ✅ | 预览物体类型 |
| background_type | BackgroundType | ✅ | 背景类型 |
| background_color | Color | ❌ | 背景颜色 |
| camera_distance | float | ✅ | 相机距离 |
| camera_rotation | Vector3 | ✅ | 相机旋转 |
| light_intensity | float | ✅ | 光照强度 |

**PreviewObjectType 枚举**:
- `sphere`: 球体
- `cube`: 立方体
- `plane`: 平面
- `custom`: 自定义物体

**BackgroundType 枚举**:
- `solid`: 纯色
- `gradient`: 渐变
- `skybox`: 天空盒

---

## State Models (LangGraph)

### SessionState（全局共享状态）

```python
@dataclass
class SessionState:
    session_id: str
    conversation_history: List[Message]
    project_path: str
    output_directory: str
    current_task_id: Optional[str]
    model_config: ModelConfig
```

### ShaderGenState（Shader 生成图状态）

```python
@dataclass
class ShaderGenState:
    user_requirement: str
    reference_image: Optional[bytes]
    image_analysis: Optional[str]
    generated_code: Optional[str]
    shader_name: Optional[str]
    compile_result: Optional[CompileResult]
    material_id: Optional[str]
    screenshot: Optional[bytes]
    retry_count: int = 0
    max_retries: int = 3
    pending_textures: List[TextureSlot] = field(default_factory=list)
    status: GraphStatus = GraphStatus.PENDING
```

**GraphStatus 枚举**:
- `pending`: 待处理
- `analyzing`: 分析需求/图片
- `generating`: 生成代码
- `compiling`: 编译中
- `fixing`: 修复错误
- `previewing`: 预览中
- `completed`: 完成
- `failed`: 失败
- `awaiting_user`: 等待用户输入

---

## Validation Rules

### Session
- `session_id` MUST be valid UUID v4
- `messages` MUST NOT be empty for active sessions
- `config.max_retry_count` MUST be in range [1, 10]

### Message
- `content` MUST NOT be empty for user/assistant messages
- `images` MUST have valid MIME type (image/png, image/jpeg, image/webp)
- `images` size MUST NOT exceed 10MB per image

### ShaderAsset
- `shader_name` MUST match pattern `^[A-Za-z][A-Za-z0-9_]*$`
- `code` MUST NOT be empty
- `version` MUST be >= 1

### MaterialAsset
- `shader_ref` MUST reference existing ShaderAsset
- `material_name` MUST match pattern `^[A-Za-z][A-Za-z0-9_]*$`

---

## Storage Format

### Session JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["session_id", "created_at", "status", "messages"],
  "properties": {
    "session_id": { "type": "string", "format": "uuid" },
    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" },
    "status": { "enum": ["active", "completed", "archived"] },
    "config": {
      "type": "object",
      "properties": {
        "output_directory": { "type": "string" },
        "max_retry_count": { "type": "integer", "minimum": 1, "maximum": 10 }
      }
    },
    "messages": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["message_id", "role", "content", "timestamp"],
        "properties": {
          "message_id": { "type": "string", "format": "uuid" },
          "role": { "enum": ["user", "assistant", "system"] },
          "content": { "type": "string" },
          "timestamp": { "type": "string", "format": "date-time" },
          "artifacts": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}
```

---

## Entity Relationships

| Relationship | Type | Description |
|--------------|------|-------------|
| Session → Message | 1:N | 一个会话包含多条消息 |
| Message → ShaderAsset | 1:N | 一条消息可产生多个 Shader 版本 |
| ShaderAsset → MaterialAsset | 1:1 | 一个 Shader 对应一个材质 |
| Session → PreviewConfig | 1:1 | 每个会话有独立的预览配置 |
