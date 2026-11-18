# project_skill：可视化论文流程 skill

这是从 `..\project\` 那套系统里抽出来的**工序**，不绑定具体数据：换一份 CSV、换一个选题，按它走一遍，仍能得到「可交互驾驶舱 + 一篇自洽的论文」。

论文里的四条论点在这里是四条约束：

- **数据是输入，不是常量**——`data_generate.py --seed N` 是正当操作，不是"破坏交付物"。
- **数字只认一个来源**——论文每个数字都要能追到 `analysis_stats.json`。
- **自检不写死业务值**——`smoke.ps1` 只查结构与依赖关系，换 seed 不会误报。
- **大模型只解释既有视图**——代理只发聚合快照，不回写筛选、不自动出图，无密钥时降级为本地规则。

## 目录

| 路径 | 内容 |
|---|---|
| `SKILL.md` | skill 正文：产物清单、环境预检、拿数据三条路、换数闭环、统计口径、插图规范、驾驶舱契约、论文结构、验收、排错表、不变量 |
| `scripts\resync.ps1` | 换数后一键重算：生成 → `analyze.py` → `figs.py` → `build_data_js.py` → 打印「论文数字看板」 |
| `scripts\smoke.ps1` | 结构与一致性体检；打印当前关键数字，有 FAIL 时退出码 1 |
| `scripts\install.ps1` | 装进某个工作区的 `.dsh\skills\ecom-viz-paper` |

## 两种用法

**就地用**（推荐，脚本会自动找到同级 `..\project`）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\smoke.ps1
powershell -ExecutionPolicy Bypass -File scripts\resync.ps1 -Regenerate -Seed 7
```

**装进 DSH**（在会话里按名字引用本流程）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
# 装到别的工作区：-Workspace "D:\my-viz-paper" -Force
```

装好后在目标工作区里可以用 `-Root <工作区>` 调用，脚本会按 `<工作区>\final paper\result\project` 找工程；工程目录不在这个位置时，用 `-Project <路径>` 直接指定。

## 换数之后要做什么

1. 看 `resync.ps1` 打印的数字看板，逐项回填论文正文、表格与图注；
2. 若插图也变了，确认图号未错位（论文图 1–图 9 对应 `project\figures\` 的哪些文件，见 `SKILL.md` 的图号映射）；
3. 重导 docx，再跑一次 `smoke.ps1`。

跳过第 1 步的后果是"图新、数旧"，比不换更糟——这是 `SKILL.md` 里列为「不变量」的一条。

## 已知边界

- 换**字段完全不同**的 CSV：需手动改 `analyze.py` / `figs.py` / `app.js` 的列名，流程本身支持，但未实测。
- 论文所用 CSV 不能由 `--seed 42` 逐行重放（生成器随机流与早期版本不同），复现论文数字请直接用 `..\project\data\ecommerce_dashboard_data.csv`，细节见 `..\REPRODUCE.md`。
