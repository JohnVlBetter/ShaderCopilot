<!--
=============================================================================
SYNC IMPACT REPORT
=============================================================================
Version Change: 1.1.0 → 1.0.1 (Cleanup - move design content to spec)
Bump Rationale: PATCH - Remove feature-specific content from constitution

Modified Sections:
  - Project Structure: Simplified to high-level only
  - Technology Governance: Removed tech stack details (belongs to spec)
  - Removed: System Architecture section (moved to spec)
  - Removed: PoC Scope section (moved to spec)

Templates Requiring Updates: None

Follow-up TODOs:
  - Docs/glossary.md: 待创建术语表
=============================================================================
-->

# Unity Shader Copilot Constitution

> **项目定位**：为 Unity 开发人员（TA、程序、美术）提供 AI 驱动的 URP Shader 编写助手。  
> 用户只需描述需求或提供参考图，助手自动完成 Shader 生成、材质创建、纹理生成、效果验证等全流程工作。

## Project Structure

本项目分为两个核心模块：

| 目录 | 职责 |
|------|------|
| `UnityProject/` | Unity 工程，包含 Shader、材质、场景及 Editor 扩展 |
| `Agent/` | 后端代码，AI Agent 逻辑、服务接口及模型调用 |

文档存放于项目根目录 `Docs/` 下，MUST 及时维护。

---

## Core Principles

### I. Readability First（可读性优先）

- 可读性 **优先于** 技巧性
- 命名 MUST 表达业务或领域语义
- 一致性 **优先于** 个人风格
- 语义 **优先于** 实现细节

**Rationale**: 项目长期可维护性依赖于代码的可理解性，技巧性代码增加认知负担并降低团队协作效率。

### II. System Consistency（系统一致性）

- 局部实现 MUST NOT 破坏整体体系一致性
- 禁止引入"只有作者能理解"的隐式约定
- 所有约定 MUST 显式声明于文档或代码注释

**Rationale**: 隐式约定是技术债务的主要来源，系统一致性是可扩展性的基础。

### III. Stability First（稳定性优先）

- 系统稳定性 **优先于** 功能完整性
- 用户可理解性 **优先于** 技术精确性
- 单点错误 MUST NOT 导致系统级崩溃
- 系统 MUST NOT 以"静默失败"作为默认策略

**Rationale**: 面向终端用户（美术、TA）的工具，稳定性和易用性是首要需求。

### IV. Error Handling（错误处理）

- 错误 MUST 被分层捕获与处理
- 每一层 MUST 提供有意义的错误上下文
- 错误信息 MUST 对用户可理解、对开发者可调试
- 关键操作 MUST 有超时与重试机制

**Rationale**: 良好的错误处理是用户体验和系统可维护性的核心保障。

### V. Single Source of Truth（数据唯一来源）

- 状态集中管理，数据来源唯一
- 派生而非复制，MUST NOT 多个权威来源描述同一事实
- 表现层 MUST NOT 成为事实裁决者
- 所有状态变化 MUST 可追踪、可审计

**Rationale**: 数据一致性是系统正确性的基础，多权威来源必然导致状态漂移。

### VI. Separation of Concerns（关注点分离）

- 每一层只解决一个问题
- 层与层通过明确契约协作
- 领域逻辑 MUST NOT 渗透进展示或交互层
- 基础设施、业务规则、表现逻辑 MUST NOT 混杂

**层次划分参考**：
| 层次 | 职责 | 示例 |
|------|------|------|
| Presentation | 用户交互、UI 渲染 | Unity Editor UI、对话界面 |
| Application | 用例编排、流程控制 | Agent 调度、Shader 生成流程 |
| Domain | 业务规则、领域模型 | Shader 模板、材质规范 |
| Infrastructure | 外部服务、持久化 | LLM API、文件系统、Unity API |

**Rationale**: 关注点分离是复杂系统可维护的必要条件。

### VII. Testability（可验证性）

- 可验证性是设计质量的一部分
- 不可测试的实现视为不完整
- 单元测试覆盖率 MUST NOT 低于 **80%**
- 核心业务逻辑 MUST 可被自动化验证
- 关键用户路径 MUST 具备端到端验证能力
- Unity 中的自动化测试（Play Mode / Edit Mode Tests）MUST 完善

**测试分层**：
| 类型 | 范围 | 要求 |
|------|------|------|
| Unit Test | 单个函数/类 | 覆盖率 ≥ 80% |
| Integration Test | 模块间交互 | 关键路径覆盖 |
| E2E Test | 完整用户流程 | 主要场景覆盖 |
| Unity Play Mode Test | 运行时行为 | Shader/材质验证 |

**Rationale**: 测试是需求的可执行规格说明，是重构的安全网。

### VIII. Technology Governance（技术治理）

- 技术选择 MUST 服务于长期可维护性
- MUST NOT 引入平行技术体系制造分裂
- 项目级技术裁决 MUST 显式声明
- 未经治理流程，MUST NOT 随意替换核心技术路线

**Rationale**: 技术决策的随意性是项目熵增的主要来源。

### IX. Convention Clarity（约定清晰）

- 清晰理解 **优先于** 工具默认行为
- 团队共识 **优先于** 外部惯例
- 关键技术术语可保留原语言，但 MUST 提供语义说明

**术语表维护**：关键术语定义应收录于 `Docs/glossary.md`

**Rationale**: 显式约定降低沟通成本，减少因假设不一致导致的错误。

### X. Documentation Discipline（文档纪律）

- 及时维护文档存放于 `Docs/` 目录
- 代码变更涉及接口或行为变化时，MUST 同步更新文档
- 废弃功能 MUST 在文档中标注并说明替代方案

**Rationale**: 文档是知识传承的载体，过时文档比无文档更有害。



---

## Technology Governance

### 技术变更流程

1. 提议者提交技术变更申请，说明动机与影响范围
2. 评估对系统一致性与长期成本的影响
3. 由治理责任人裁决
4. 更新本宪法及相关配套规范
5. 必要时制定迁移方案

---

## AI/Agent Constraints

所有 AI / Agent：

- MUST 以本宪法作为最高约束
- MUST NOT 自动生成、修改或绕过宪法内容
- MUST 遵循本宪法定义的代码风格与架构原则
- 生成代码 MUST 可通过项目既定的测试与质量门禁

---

## Governance

### 最高治理协议

本宪法为项目最高治理协议，优先级高于所有 Rules、Guidelines 与工具约定。

### 修订流程

| 步骤 | 责任 | 产出 |
|------|------|------|
| 1. 提议 | 任何贡献者 | 动机说明与影响范围评估 |
| 2. 讨论 | 团队成员 | 对系统一致性与长期成本的影响分析 |
| 3. 审批 | 治理责任人 | 批准/驳回/修改意见 |
| 4. 实施 | 提议者 | 更新宪法与相关配套规范 |
| 5. 迁移 | 相关方 | 必要时制定并执行迁移方案 |

### 版本控制

采用语义化版本：`MAJOR.MINOR.PATCH`

- **MAJOR**: 原则移除/重新定义等不兼容变更
- **MINOR**: 新增原则/章节或重大扩展
- **PATCH**: 澄清、措辞修正、非语义性优化

### 合规审查

- 所有 PR/Review MUST 验证是否符合本宪法
- 复杂度增加 MUST 有正当理由
- 运行时开发指南参见 `Docs/` 目录

---

**Version**: 1.0.1 | **Ratified**: 2025-12-28 | **Last Amended**: 2025-12-28
