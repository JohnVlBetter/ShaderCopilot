# ShaderCopilot 工具参考文档

> **版本**: 1.0.0 | **最后更新**: 2025-12-28

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

- `generate_shader_code` - 核心功能，生成着色器代码
- `compile_shader` - 验证着色器是否有效
- `save_shader` - 保存生成的着色器
- `create_material` - 创建可使用的材质
- `apply_to_preview` - 预览效果
- `capture_screenshot` - 截图用于分析
- `analyze_image` - 分析参考图片

### 应该实现 (P2)

- `read_shader` - 读取已有着色器进行修改
- `set_material_texture` - 设置材质纹理属性
- `list_preview_objects` - 获取可用预览物体列表
- `switch_preview_object` - 切换不同形状的预览物体
- `set_background` - 自定义预览背景

### 可选实现 (P3)

- `generate_texture_comfyui` - AI 生成纹理（需要 ComfyUI）
- `generate_texture_procedural` - 程序化生成纹理
- `save_texture` - 保存生成的纹理
- `check_comfyui_available` - 检测 ComfyUI 服务
- `run_mali_compiler` - 移动端性能分析

---

## Tool 详细说明

### generate_shader_code

**说明**: 使用 LLM 根据用户需求生成 HLSL/ShaderLab 代码

**输入参数**:
- `requirement`: 用户需求描述
- `existing_code`: 现有代码（可选，用于修改）
- `image_analysis`: 图片分析结果（可选）

**输出**:
- `shader_code`: 生成的着色器代码

### compile_shader

**说明**: 在 Unity 中编译着色器并返回编译结果

**输入参数**:
- `shader_code`: 着色器源代码

**输出**:
- `success`: 是否编译成功
- `errors`: 错误列表（如果有）
- `warnings`: 警告列表（如果有）

### save_shader

**说明**: 将着色器保存到 Unity 项目中

**输入参数**:
- `shader_code`: 着色器源代码
- `shader_name`: 着色器名称
- `path`: 保存路径（可选）

**输出**:
- `file_path`: 保存的文件路径

### analyze_image

**说明**: 使用视觉语言模型分析参考图片

**输入参数**:
- `image_data`: Base64 编码的图片数据
- `mime_type`: 图片 MIME 类型

**输出**:
- `analysis`: 视觉风格分析结果
- `suggested_techniques`: 建议的着色器技术
