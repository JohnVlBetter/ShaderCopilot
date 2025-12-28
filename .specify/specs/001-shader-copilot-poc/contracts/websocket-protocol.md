# WebSocket Protocol Contract

**Feature**: `001-shader-copilot-poc`  
**Version**: 1.0.0  
**Date**: 2025-12-28

---

## Overview

Unity Editor (Client) ↔ Python Backend (Server) 通过 WebSocket 双向通信。

- **Server**: `ws://localhost:8765` (默认端口)
- **Protocol**: JSON 消息格式
- **Encoding**: UTF-8

---

## Message Structure

### Base Message

所有消息共享的基础结构：

```json
{
  "id": "uuid-v4",           // 消息唯一标识
  "type": "message_type",    // 消息类型
  "timestamp": "ISO-8601",   // 时间戳
  "payload": {}              // 具体内容
}
```

---

## Client → Server Messages

### 1. USER_MESSAGE

用户发送对话消息。

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "user_message",
  "timestamp": "2025-12-28T10:00:00Z",
  "payload": {
    "session_id": "session-uuid",
    "content": "创建一个卡通风格的着色器",
    "images": [
      {
        "image_id": "img-001",
        "data": "base64-encoded-image-data",
        "mime_type": "image/png"
      }
    ]
  }
}
```

### 2. TOOL_RESPONSE

Unity 执行工具后返回结果。

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "type": "tool_response",
  "timestamp": "2025-12-28T10:00:05Z",
  "payload": {
    "request_id": "tool-request-uuid",
    "tool_name": "compile_shader",
    "success": true,
    "result": {
      "shader_id": "shader-uuid",
      "has_errors": false,
      "errors": []
    },
    "error": null
  }
}
```

### 3. SESSION_INIT

初始化或恢复会话。

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "type": "session_init",
  "timestamp": "2025-12-28T10:00:00Z",
  "payload": {
    "session_id": "session-uuid",  // null 表示新建会话
    "project_path": "E:/Projects/MyGame",
    "config": {
      "output_directory": "Assets/Shaders/Generated",
      "max_retry_count": 3,
      "model_config": {
        "router_model": "qwen-turbo",
        "code_model": "qwen-max",
        "vl_model": "qwen-vl-plus"
      }
    }
  }
}
```

### 4. USER_CONFIRM

用户确认操作。

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "type": "user_confirm",
  "timestamp": "2025-12-28T10:00:30Z",
  "payload": {
    "confirm_id": "confirm-uuid",
    "confirmed": true,
    "message": "确认保存"
  }
}
```

### 5. CANCEL_TASK

取消当前任务。

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "type": "cancel_task",
  "timestamp": "2025-12-28T10:00:35Z",
  "payload": {
    "task_id": "task-uuid"
  }
}
```

### 6. PING

心跳检测。

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440005",
  "type": "ping",
  "timestamp": "2025-12-28T10:00:00Z",
  "payload": {}
}
```

---

## Server → Client Messages

### 1. SESSION_READY

会话初始化完成。

```json
{
  "id": "650e8400-e29b-41d4-a716-446655440000",
  "type": "session_ready",
  "timestamp": "2025-12-28T10:00:01Z",
  "payload": {
    "session_id": "session-uuid",
    "history": [
      {
        "message_id": "msg-001",
        "role": "user",
        "content": "之前的消息...",
        "timestamp": "2025-12-28T09:00:00Z"
      }
    ]
  }
}
```

### 2. THINKING

Agent 正在思考。

```json
{
  "id": "650e8400-e29b-41d4-a716-446655440001",
  "type": "thinking",
  "timestamp": "2025-12-28T10:00:02Z",
  "payload": {
    "task_id": "task-uuid",
    "message": "正在分析您的需求..."
  }
}
```

### 3. STREAM_TEXT

流式文本输出。

```json
{
  "id": "650e8400-e29b-41d4-a716-446655440002",
  "type": "stream_text",
  "timestamp": "2025-12-28T10:00:03Z",
  "payload": {
    "task_id": "task-uuid",
    "delta": "我将为您创建一个",
    "is_final": false
  }
}
```

### 4. TOOL_CALL

请求 Unity 执行工具。

```json
{
  "id": "650e8400-e29b-41d4-a716-446655440003",
  "type": "tool_call",
  "timestamp": "2025-12-28T10:00:04Z",
  "payload": {
    "request_id": "tool-request-uuid",
    "tool_name": "compile_shader",
    "arguments": {
      "shader_code": "Shader \"Custom/Toon\" { ... }",
      "shader_name": "Toon"
    }
  }
}
```

### 5. PROGRESS

进度更新。

```json
{
  "id": "650e8400-e29b-41d4-a716-446655440004",
  "type": "progress",
  "timestamp": "2025-12-28T10:00:05Z",
  "payload": {
    "task_id": "task-uuid",
    "stage": "compiling",
    "progress": 0.5,
    "message": "正在编译 Shader..."
  }
}
```

**Stage 枚举**:
- `analyzing`: 分析需求
- `generating`: 生成代码
- `compiling`: 编译 Shader
- `creating_material`: 创建材质
- `previewing`: 生成预览
- `saving`: 保存文件

### 6. REQUIRE_CONFIRM

请求用户确认。

```json
{
  "id": "650e8400-e29b-41d4-a716-446655440005",
  "type": "require_confirm",
  "timestamp": "2025-12-28T10:00:06Z",
  "payload": {
    "confirm_id": "confirm-uuid",
    "confirm_type": "overwrite_file",
    "message": "文件 Assets/Shaders/Toon.shader 已存在，是否覆盖？",
    "options": ["confirm", "cancel", "rename"]
  }
}
```

### 7. TASK_COMPLETE

任务完成。

```json
{
  "id": "650e8400-e29b-41d4-a716-446655440006",
  "type": "task_complete",
  "timestamp": "2025-12-28T10:00:10Z",
  "payload": {
    "task_id": "task-uuid",
    "success": true,
    "message": "Shader 创建成功！",
    "artifacts": {
      "shader_path": "Assets/Shaders/Toon.shader",
      "material_path": "Assets/Materials/Toon.mat"
    },
    "screenshot": "base64-encoded-image"
  }
}
```

### 8. ERROR

错误消息。

```json
{
  "id": "650e8400-e29b-41d4-a716-446655440007",
  "type": "error",
  "timestamp": "2025-12-28T10:00:07Z",
  "payload": {
    "task_id": "task-uuid",
    "error_code": "COMPILE_FAILED",
    "message": "Shader 编译失败",
    "details": "Line 15: unexpected token '}'",
    "recoverable": true,
    "retry_count": 1,
    "max_retries": 3
  }
}
```

**Error Codes**:
- `COMPILE_FAILED`: Shader 编译失败
- `LLM_ERROR`: LLM 调用失败
- `TIMEOUT`: 操作超时
- `INVALID_INPUT`: 无效输入
- `FILE_ERROR`: 文件操作失败
- `CONNECTION_ERROR`: 连接错误
- `INTERNAL_ERROR`: 内部错误

### 9. PONG

心跳响应。

```json
{
  "id": "650e8400-e29b-41d4-a716-446655440008",
  "type": "pong",
  "timestamp": "2025-12-28T10:00:00Z",
  "payload": {}
}
```

---

## Tool Definitions

### compile_shader

编译 Shader 代码。

**Arguments**:
```json
{
  "shader_code": "string",    // Shader 源代码
  "shader_name": "string"     // Shader 名称
}
```

**Result**:
```json
{
  "shader_id": "string",      // Shader 实例 ID
  "has_errors": "boolean",    // 是否有错误
  "errors": [                 // 错误列表
    {
      "line": "number",
      "column": "number",
      "message": "string",
      "severity": "error|warning"
    }
  ]
}
```

### save_shader

保存 Shader 文件。

**Arguments**:
```json
{
  "shader_code": "string",    // Shader 源代码
  "file_path": "string"       // 保存路径（相对于 Assets）
}
```

**Result**:
```json
{
  "success": "boolean",
  "file_path": "string"       // 完整文件路径
}
```

### create_material

创建材质。

**Arguments**:
```json
{
  "shader_name": "string",    // Shader 名称
  "material_name": "string",  // 材质名称
  "properties": {             // 材质属性
    "_Color": { "r": 1, "g": 1, "b": 1, "a": 1 }
  }
}
```

**Result**:
```json
{
  "material_id": "string",    // 材质实例 ID
  "success": "boolean"
}
```

### apply_to_preview

应用材质到预览物体。

**Arguments**:
```json
{
  "material_id": "string",    // 材质 ID
  "object_type": "sphere|cube|plane"  // 预览物体类型
}
```

**Result**:
```json
{
  "success": "boolean"
}
```

### capture_screenshot

截取预览场景截图。

**Arguments**:
```json
{
  "width": "number",          // 截图宽度
  "height": "number"          // 截图高度
}
```

**Result**:
```json
{
  "image_data": "string",     // Base64 编码的图片
  "mime_type": "image/png"
}
```

### list_preview_objects

列出可用预览物体。

**Arguments**: `{}`

**Result**:
```json
{
  "objects": ["sphere", "cube", "plane"]
}
```

### switch_preview_object

切换预览物体。

**Arguments**:
```json
{
  "object_type": "sphere|cube|plane"
}
```

**Result**:
```json
{
  "success": "boolean"
}
```

### set_background

设置预览背景。

**Arguments**:
```json
{
  "background_type": "solid|gradient|skybox",
  "color": { "r": 0.2, "g": 0.2, "b": 0.2, "a": 1 },  // for solid
  "gradient_top": { "r": 0.3, "g": 0.3, "b": 0.5, "a": 1 },  // for gradient
  "gradient_bottom": { "r": 0.1, "g": 0.1, "b": 0.2, "a": 1 }
}
```

**Result**:
```json
{
  "success": "boolean"
}
```

---

## Connection Lifecycle

```
Unity                                    Backend
  │                                         │
  │──────── WebSocket Connect ─────────────>│
  │                                         │
  │<─────── Connection Accepted ────────────│
  │                                         │
  │──────── SESSION_INIT ──────────────────>│
  │                                         │
  │<─────── SESSION_READY ──────────────────│
  │                                         │
  │──────── PING (every 30s) ──────────────>│
  │<─────── PONG ───────────────────────────│
  │                                         │
  │──────── USER_MESSAGE ──────────────────>│
  │<─────── THINKING ───────────────────────│
  │<─────── STREAM_TEXT (multiple) ─────────│
  │<─────── TOOL_CALL ──────────────────────│
  │──────── TOOL_RESPONSE ─────────────────>│
  │<─────── PROGRESS ───────────────────────│
  │<─────── TASK_COMPLETE ──────────────────│
  │                                         │
  │──────── WebSocket Close ───────────────>│
  │                                         │
```

---

## Error Handling

### Connection Errors
- 连接失败：Unity 自动重试，最多 3 次，间隔 2s
- 连接断开：Unity 尝试重连，超时 10s 后提示用户

### Message Errors
- 无效 JSON：记录日志，发送 ERROR 消息
- 未知消息类型：记录日志，忽略消息
- 超时：30s 无响应视为超时

### Tool Errors
- 工具执行失败：返回 TOOL_RESPONSE with error
- 工具不存在：返回 ERROR with INVALID_INPUT
