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
