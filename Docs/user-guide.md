# ShaderCopilot 用户指南

Unity 编辑器中 AI 驱动的 URP Shader 编写助手。

## 目录

1. [简介](#简介)
2. [安装](#安装)
3. [快速开始](#快速开始)
4. [功能介绍](#功能介绍)
5. [用户场景](#用户场景)
6. [设置](#设置)
7. [故障排除](#故障排除)

---

## 简介

ShaderCopilot 是一个 AI 驱动的工具，帮助你通过自然语言描述或参考图片创建 URP 着色器。只需描述你想要的效果或上传示例图片，ShaderCopilot 就会实时生成、编译和预览着色器。

### 核心功能

- **文本生成 Shader**：用自然语言描述你的着色器
- **图片生成 Shader**：上传参考图片来重现视觉风格
- **迭代优化**：通过对话来优化和修改生成的着色器
- **实时预览**：在 3D 物体上实时查看着色器效果
- **会话管理**：保存和恢复你的工作进度

---

## 安装

### 环境要求

- Unity 2021.3 或更高版本（需配置 URP）
- Python 3.11+
- LLM API 访问权限（OpenAI 兼容接口）

### 步骤 1：克隆仓库

```bash
git clone https://github.com/your-org/ShaderCopilot.git
```

### 步骤 2：配置 Python 后端

```bash
cd ShaderCopilot/Agent

# 使用 UV（推荐）
uv sync

# 或使用 pip
pip install -e .
```

### 步骤 3：配置 API 密钥

创建 `Agent/.env` 文件：

```env
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your-api-key-here
```

### 步骤 4：打开 Unity 项目

1. 打开 Unity Hub
2. 添加 `ShaderCopilot/UnityProject` 作为项目
3. 使用 Unity 2021.3+ 打开项目

---

## 快速开始

### 打开 ShaderCopilot

1. 在 Unity 中，进入 **Window → ShaderCopilot**
2. ShaderCopilot 窗口将会打开

### 启动后端服务

**方式 A：从 Unity 自动启动**
- 点击 ShaderCopilot 工具栏中的 **Start Server**

**方式 B：手动启动**
```bash
cd Agent
uv run python -m shader_copilot.server.websocket_server
```

### 创建你的第一个 Shader

1. 等待工具栏显示 "Connected" 状态
2. 在聊天框中输入："创建一个简单的卡通着色器，带有两个颜色色阶"
3. 等待着色器生成和编译完成
4. 在预览面板中查看结果

---

## 功能介绍

### 聊天面板

聊天面板是你与 ShaderCopilot 交互的主要界面。

**文本输入**
- 输入你的着色器描述或修改请求
- 按 Enter 或点击发送按钮

**图片上传**
- 点击 📷 按钮上传参考图片
- 支持格式：PNG、JPG、GIF
- AI 将分析图片并提取视觉风格信息

**流式响应**
- 响应会实时显示
- 代码块会进行语法高亮

### 预览面板

预览面板展示应用了着色器的 3D 物体效果。

**控制方式**
- **旋转**：拖拽来旋转物体
- **缩放**：滚动来放大/缩小
- **物体类型**：在球体、立方体、平面等之间切换
- **背景**：更改背景颜色

### 设置面板

点击 ⚙️ 图标进入设置。

**预览设置**
- 预览物体：球体、立方体、平面、圆柱体、胶囊体
- 背景：深色、浅色、黑色、白色、蓝色、灰色、绿色、自定义
- 自定义颜色：选择任意背景颜色

### 会话管理

**新建会话**
- 点击 "New Session" 开始新的工作
- 之前的会话会自动保存

**加载会话**
- 点击工具栏中的 "Sessions"
- 从列表中选择一个会话来继续之前的工作

---

## 用户场景

### 场景 1：文本描述生成 Shader

用自然语言描述你的着色器：

```
"创建一个全息效果，带有扫描线和边缘发光"
```

```
"制作一个溶解着色器，带有蓝色火焰边缘效果"
```

```
"我需要一个水面着色器，带有折射效果"
```

### 场景 2：图片参考生成 Shader

上传展示你想要视觉风格的参考图片：

1. 点击 📷 按钮
2. 选择一张图片（游戏截图、美术作品等）
3. 可选择添加说明："重现这个卡通渲染风格"
4. AI 会分析图片并生成匹配的着色器

### 场景 3：迭代优化

生成着色器后，通过对话来优化它：

```
你："创建一个基础卡通着色器"
AI：[生成着色器并显示预览]

你："添加青色的边缘光"
AI：[修改着色器，更新预览]

你："让阴影边缘更柔和"
AI：[调整着色器，更新预览]

你："效果不错，保存为 ToonCharacter.shader"
AI：[将着色器保存到 Assets/Shaders/ToonCharacter.shader]
```

### 场景 4：会话持久化

你的工作会自动保存：

- 对话历史
- 当前着色器代码
- 着色器版本
- 设置

随时可以从会话面板恢复工作。

### 场景 5：预览自定义

自定义你查看着色器的方式：

1. 切换预览物体来测试不同形状上的效果
2. 更改背景来查看着色器在不同光照下的表现
3. 自由旋转来从各个角度检查

---

## 设置

### Unity 设置

通过 **Edit → Preferences → ShaderCopilot** 访问

| 设置项 | 说明 | 默认值 |
|--------|------|--------|
| Server Host | WebSocket 服务器地址 | localhost |
| Server Port | WebSocket 服务器端口 | 8765 |
| Auto Connect | 打开窗口时自动连接 | true |
| Output Directory | 着色器保存位置 | Assets/Shaders/ShaderCopilot |

### 后端设置

在 `Agent/.env` 中配置：

| 设置项 | 说明 | 默认值 |
|--------|------|--------|
| LLM_API_BASE | API 端点 | https://api.openai.com/v1 |
| LLM_API_KEY | 你的 API 密钥 | （必填） |
| CODE_MODEL | 生成着色器的模型 | qwen-max |
| ROUTER_MODEL | 路由模型 | qwen-turbo |
| VL_MODEL | 图像分析模型 | qwen-vl-plus |
| LOG_LEVEL | 日志级别 | INFO |

---

## 故障排除

### 连接问题

**"Disconnected" 状态**
1. 确保 Python 后端正在运行
2. 检查端口 8765 没有被阻止
3. 尝试点击工具栏中的 "Connect"

**"Connection refused"**
- 手动启动后端：
  ```bash
  cd Agent
  uv run python -m shader_copilot.server.websocket_server
  ```

### Shader 编译错误

如果生成的着色器有错误：
1. AI 会自动尝试修复
2. 检查聊天中的错误信息
3. 提供更具体的需求

**常见修复方法**：
- "使用 URP 着色器格式"
- "目标 Unity 2021.3"
- "不要使用已弃用的函数"

### API 错误

**"Invalid API key"**
- 检查 `.env` 文件中的 API 密钥是否正确
- 确保密钥有足够的配额

**"Rate limit exceeded"**
- 稍等片刻后重试
- 考虑使用其他模型

### 性能问题

**响应缓慢**
- 较大的模型（qwen-max）更慢但更准确
- 尝试 `CODE_MODEL=qwen-plus` 以获得更快的结果

**预览卡顿**
- 在设置中降低预览分辨率
- 关闭其他占用资源的 Unity 窗口

---

## 技巧和最佳实践

### 编写好的提示

**要具体**
```
❌ "让它看起来更酷"
✅ "添加 2 像素宽度的蓝色边缘光"
```

**使用 URP/Shader 术语**
```
✅ "使用 Lambert 光照和菲涅尔效果"
✅ "支持 URP 中的主光源阴影"
```

**描述使用场景**
```
✅ "用于风格化手机游戏中的角色"
✅ "需要支持透明物体"
```

### 迭代工作流

1. 从简单开始："创建一个基础无光照着色器"
2. 一次添加一个功能
3. 在预览中测试每个更改
4. 满意后保存

### 使用参考图片

- 使用清晰、光线充足的图片
- 裁剪以聚焦于材质/效果
- 添加文字说明："关注金属表面"

---

## 键盘快捷键

| 快捷键 | 操作 |
|--------|------|
| Enter | 发送消息 |
| Ctrl+N | 新建会话 |
| Ctrl+S | 保存当前着色器 |
| Escape | 取消当前操作 |

---

## 获取帮助

- **问题反馈**：在 GitHub Issues 报告 bug
- **讨论交流**：在 GitHub Discussions 提问
- **日志调试**：查看 `Agent/shader_copilot.log` 进行调试

---

## 许可证

ShaderCopilot 项目的一部分。详情请参阅 LICENSE 文件。
