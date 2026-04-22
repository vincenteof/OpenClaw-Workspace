# MEMORY.md - Long-term Memory

## Obsidian Vault 结构

- `000 - Indexes`：主题索引
- `200 - Material`：收藏的有价值资料
- `300 - Daily Notes`：每日随想，人生/成长短思考，内容素材
- `400 - Zettelkasten`：灵感集和学习笔记，内容创作原材料
- `980 - Task Management`：todo 归集视图（Dataview 视图，不是存放 todo 的地方）
- `999 - Templates`：笔记模板

---

## Obsidian 操作规范

### 新建笔记
默认套用 `999 - Templates/General Note.md` 模板：
```
Date: <当天日期>
Tags: 

# <标题>

# References
```

### Todo 标签
- `#active` 等状态 tag 打在 **todo 行**上，不放进 frontmatter
- 正确：`- [ ] 做某件事 #active`
- 错误：frontmatter 里写 `tags: [active]`

---

## Paths & Environment

- **Obsidian vault:** `/Users/vincenteofchen/Documents/vincenteof-obsidian`
- **Workspace:** `/Users/vincenteofchen/OpenClaw-Workspace`

---

## 投资组合系统（Obsidian）

### 目录结构
```
970 - Investments/
├── 971 - Portfolio/
│   ├── Dashboard.md          # 日常查看入口（嵌入 Bases）
│   └── Portfolio.base        # Bases 数据库，含公式列和表格视图
├── 972 - Assets/             # 每个持仓资产一个笔记（SYMBOL.md）
├── 973 - Transactions/
│   └── Transaction-Log.md    # 交易流水日志（Markdown 表格）
└── Instructions.md           # OpenClaw 操作规范（必读）
```

### 收到交易指令时
**必须先读取** `970 - Investments/Instructions.md`，然后按规范执行：
1. 解析字段，有歧义先确认
2. 更新 `972 - Assets/<SYMBOL>.md` 的 YAML
3. 追加记录到 `973 - Transactions/Transaction-Log.md`
4. git commit & push
5. 回复变更摘要

### 关键规则
- avg_cost：买入用加权平均法，卖出不变，拆股按比例调整
- 新资产没有笔记时，先询问用户确认再创建
- 资产笔记文件名 = symbol 全大写（如 `AAPL.md`、`TSLA.md`）
- vault 是 git 仓库，每次操作后 commit & push
