<h1 align="center">🧠 Memory Reach</h1>

<p align="center">
  <strong>给你的 AI Agent 一键装上长期记忆、项目记忆和可检索记忆能力</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-green.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"></a>
</p>

<p align="center">
  <a href="#快速上手">快速上手</a> · <a href="#它会做什么">它会做什么</a> · <a href="#doctor">Doctor</a> · <a href="#设计理念">设计理念</a>
</p>

---

## 为什么需要 Memory Reach？

AI Agent 已经能聊天、写代码、查资料——但你让它**长期记住项目和人**，它就开始混乱：

- "记住我的偏好" → **下次忘了**，新会话直接断片
- "记住这个项目背景" → **记错地方**，临时内容混进长期记忆
- "你是怎么知道这个的？" → **说不清来源**，记忆不可验证
- "帮我延续上次的工作" → **找不到上下文**，只能重头再说
- "别把敏感信息记进去" → **没有规则**，token/cookie 可能被误写入日志

**这些不是大模型不够聪明，而是缺少一层记忆基建。**

Memory Reach 做的事情很简单：

- 帮你建立标准记忆目录结构
- 区分长期记忆 / 项目记忆 / 每日日志 / 会话归档
- 提供一套基础 doctor，检查“记忆是否可用、可写、可检索、是否混乱”
- 给 Agent 一份统一的记忆使用规范

**一句话安装：**

```text
帮我安装 Memory Reach：https://raw.githubusercontent.com/YOUR_NAME/memory-reach/main/docs/install.md
```

安装完之后，Agent 就不再只是“当前会话聪明”，而是开始具备**项目级连续性**。

---

## 快速上手

复制这句话给你的 AI Agent（OpenClaw、Claude Code、Cursor 等）：

```text
帮我安装 Memory Reach：https://raw.githubusercontent.com/YOUR_NAME/memory-reach/main/docs/install.md
```

已安装过？更新也是一句话：

```text
帮我更新 Memory Reach：https://raw.githubusercontent.com/YOUR_NAME/memory-reach/main/docs/update.md
```

---

## 它会做什么？

1. **初始化标准记忆目录**
   - `MEMORY.md`：长期记忆
   - `projects/`：项目记忆
   - `daily/`：每日日志
   - `sessions/`：会话归档
   - `rules/`：记忆规则

2. **安装一个轻量 CLI**
   - `memory-reach init` 初始化目录
   - `memory-reach doctor` 做健康检查

3. **写入默认规则模板**
   - 什么应该记
   - 什么不该记
   - 敏感信息不要怎么落盘

4. **给 Agent 一份记忆使用规范**
   - 什么时候写长期记忆
   - 什么时候写 daily
   - 什么时候只保留在会话里

---

## 目录结构

```text
memory-reach/
├── MEMORY.md
├── projects/
│   └── example-project.md
├── daily/
│   └── 2026-01-01.md
├── sessions/
│   ├── active/
│   └── archive/
├── rules/
│   ├── memory-rules.md
│   ├── privacy-rules.md
│   └── retention.md
└── .memory-reach.json
```

---

## Doctor

运行：

```bash
memory-reach doctor
```

示例输出：

```text
✅ MEMORY.md exists
✅ projects/ exists
✅ daily/ exists
✅ sessions/archive/ exists
✅ rules/memory-rules.md exists
⚠️ Potential sensitive keys not detected (good)
✅ basic structure healthy
```

Doctor 第一版检查：

- 必需目录是否存在
- 核心模板是否存在
- 目录是否可写
- 是否检测到明显敏感字段（如 `sk-`, `xoxb-`, `ghp_`）

---

## 设计理念

**Memory Reach 是脚手架，不是记忆平台。**

它不负责替你的 Agent “聪明地决定一切”，它只负责把记忆这件事从混乱状态，变成一套：

- 可初始化
- 可分类
- 可检索
- 可检查
- 可演进

也就是说，它卖的不是“更多记忆”，而是：

> **让 Agent 记得更对。**

---

## 开发路线图

### v0.1
- [x] 标准目录初始化
- [x] doctor 基础检查
- [x] 默认规则模板
- [x] CLI 脚手架

### v0.2
- [ ] 敏感信息扫描增强
- [ ] 项目模板生成
- [ ] session 摘要模板

### v1.0
- [ ] 检索接口对接
- [ ] 多 Agent 兼容模板
- [ ] 更细的记忆质量检查

---

## License

MIT
