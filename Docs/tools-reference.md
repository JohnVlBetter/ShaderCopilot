# ShaderCopilot Tools Reference

> **Version**: 1.0.0 | **Last Updated**: 2025-12-28

本文档定义了 ShaderCopilot 系统中所有可用的 Tools 及其执行位置。

## 概述

Tools 分为三类执行位置：
- **Unity**: 在 Unity Editor 中执行
- **Backend (LLM)**: 在 Python 后端通过 LLM 执行
- **Backend → External**: 后端调用外部服务

---

## Tool 定义

### Shader 相关

| Tool | 执行位置 | 说明 |
|------|----------|------|
| `generate_shader_code` | Backend (LLM) | 生成 Shader 代码 |
| `compile_shader` | Unity | 编译 Shader 并返回结果 |
| `save_shader` | Unity | 保存 Shader 文件 |
| `read_shader` | Unity | 读取 Shader 文件 |

### 材质相关

| Tool | 执行位置 | 说明 |
|------|----------|------|
| `create_material` | Unity | 创建材质球 |
| `set_material_texture` | Unity | 设置材质纹理 |
| `apply_to_preview` | Unity | 应用材质到预览物体 |

### 预览场景相关

| Tool | 执行位置 | 说明 |
|------|----------|------|
| `list_preview_objects` | Unity | 列出可用预览物体 |
| `switch_preview_object` | Unity | 切换预览物体 |
| `set_background` | Unity | 设置背景 |
| `capture_screenshot` | Unity | 截图 |

### 图像分析相关

| Tool | 执行位置 | 说明 |
|------|----------|------|
| `analyze_image` | Backend (VL 模型) | 分析参考效果图 |

### 纹理生成相关

| Tool | 执行位置 | 说明 |
|------|----------|------|
| `generate_texture_comfyui` | Backend → ComfyUI | 调用 ComfyUI 生成纹理 |
| `generate_texture_procedural` | Backend | 程序化生成纹理 |
| `save_texture` | Unity | 保存纹理文件 |

### 工具/检测相关

| Tool | 执行位置 | 说明 |
|------|----------|------|
| `check_comfyui_available` | Backend | 检测 ComfyUI 是否可用 |
| `run_mali_compiler` | Backend | 调用 Mali Offline Compiler |

---

## Tool 调用流程

```
用户输入
    ↓
Router Agent (LLM) → 选择合适的 Graph
    ↓
Graph 内 Agent 决定调用哪些 Tools
    ↓
┌─────────────────────────────────────────┐
│ Backend Tool                            │
│ (generate_shader_code, analyze_image)   │
│ → 直接在后端执行                          │
└─────────────────────────────────────────┘
    或
┌─────────────────────────────────────────┐
│ Unity Tool                              │
│ (compile_shader, create_material, etc.) │
│ → 通过 WebSocket 发送到 Unity 执行       │
│ → Unity 返回执行结果                     │
└─────────────────────────────────────────┘
    ↓
Agent 根据结果决定下一步
```

---

## PoC 阶段 Tool 优先级

### 必须实现 (P1)

- `generate_shader_code`
- `compile_shader`
- `save_shader`
- `create_material`
- `apply_to_preview`
- `capture_screenshot`
- `analyze_image`

### 应该实现 (P2)

- `read_shader`
- `set_material_texture`
- `list_preview_objects`
- `switch_preview_object`
- `set_background`

### 可选实现 (P3)

- `generate_texture_comfyui`
- `generate_texture_procedural`
- `save_texture`
- `check_comfyui_available`
- `run_mali_compiler`
