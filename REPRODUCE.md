# 复现报告

两件事要分开看：

1. **论文里的数字**（GMV、ROAS、CV、品类/渠道表、插图、页面）——**可以 100% 复现**，因为随附了数据快照（`project\data\ecommerce_dashboard_data.csv`），从它复算得到的统计与插图与论文交付版逐字节一致。
2. **数据本身**——**不能用 `--seed 42` 逐行重放**。`data_generate.py` 复现的是生成规则（品类/渠道/天数的结构与各品类的 ROI、转化率、跳出率区间），随机流与当初产出那份 CSV 的版本不同，因此同 seed 得到的是**另一个同分布样本**，不是原文件。

先把边界说清楚，再给实测值。

## 路径 A：复现论文数字（推荐，必成）

数据快照：`project\data\ecommerce_dashboard_data.csv`

| 项 | 值 |
|---|---|
| SHA256 | `AAC0207CE38BD084484E0490B8831A4454A7302C8D74EE4F5C02C9CB369F92C7` |
| 大小 | 34,415 B |
| 行数 | 540（30 天 × 6 品类 × 3 渠道，表头另计） |
| 日期 | 2026-09-01 ~ 2026-09-30 |

把该文件放回 `<project>\data\ecommerce_dashboard_data.csv`，然后：

```powershell
python scripts\analyze.py            # -> analysis_stats.json
python scripts\figs.py               # -> figures\fig_*.png
python scripts\build_data_js.py      # -> dashboard\data.js
python scripts\build_data_js.py --check   # 一致时退出码 0
```

实测（DSH 自带 Python 3.12.14 + numpy 2.3.5 + pandas 3.0.1；matplotlib 3.11.2 经 `_tools` 挂 `PYTHONPATH`）：

| 产物 | 结果 | 校验值 |
|---|---|---|
| `analysis_stats.json` | 重跑**逐字节一致** | SHA256 `E9813487DBDC59C70D197D41A84D09578DFF08EC976439A5FDD5CF22EF78865D` |
| 11 张 PNG | **11/11 逐字节一致** | 例：`fig4_category.png` → `8369B9467023B4408C4CD0E5269E5332BABBA957CA929CE0E6583BFBD07D84D7` |
| `dashboard\data.js` | `--check` 通过，80,000 B | SHA256 `C77B9800A658B355EC3A43263155AF8114139A35428A778A92BEBA77BCF44CBB` |
| 关键统计 | `total_gmv = 14229224.94`、`roas = 3.0485`、`daily_cv = 0.0828`、最差环比 `2026-09-19 −20.42%` | 与论文正文、表 4、表 5、图 5–图 9 一致 |

注：PNG 的逐字节一致依赖同一套 matplotlib 版本与字体；换环境后像素可能有细微差异，但统计值与图注数字不受影响。

## 路径 B：换一份数据，全链路重算

```powershell
powershell -ExecutionPolicy Bypass -File scripts\resync.ps1 -Project "..\project" -Regenerate -Seed 7
```

实测（临时副本，未污染交付物）：

| 项 | seed 7 结果 |
|---|---|
| 行数 | 540（30 天 × 6 品类 × 3 渠道） |
| GMV / 花费 | 13,884,229.94（1388.42 万）/ 4,540,191.31（454.02 万） |
| ROAS | 3.0581 |
| 日度 CV / 最差环比 | 9.99% / 2026-09-22 −23.62% |
| `data.js` | 重写为 80,018 B |
| 插图 | 11 张全部重绘 |
| `smoke.ps1` | `PASS 12 WARN 1 FAIL 0`（唯一 WARN：该副本下没有 docx） |

注意：换 seed 后论文里的每个数字都要按 `resync.ps1` 打印的「数字看板」回填，否则图、页面与正文互相矛盾；这是流程的设计前提，不是缺陷。

## 为什么同 seed 得不到同一份 CSV

- `data_generate.py` 的规则等价于 `task6` 里的原始生成脚本（6 品类 × 3 渠道 × 30 天、`seed=42`、各品类 ROI/CVR/跳出率区间），但**随机流的调用顺序/版本不同**：同 seed=42 跑出 GMV 1401.76 万、ROAS 3.0696，而论文数据是 1422.92 万、3.0485。
- 排查时穷举过 seed 0–20000 × 24 种抽样顺序，均无法命中原文件首行 `5280.49, 19272.79, 0.1777, 0.2834`，可判定原 CSV 由早期版本产出、无法用当前脚本逐行回放。
- 处理方式：把原 CSV 作为**数据快照**随附件提交（`project\data\`），并让"可再生"与"可复算"分离——论文数字从快照复算，新样本用 `--seed` 生成。若要求严格"seed 可重放"，需要在论文中把数据声明改为"快照 + 生成规则同构"，或重做一份由当前脚本产出的数据集并同步所有数字。

## 环境要求

| 依赖 | 版本参考 | 用途 |
|---|---|---|
| Python 3.12 | 3.12.14（DSH 自带） | `analyze.py` / `figs.py` / `build_data_js.py` |
| numpy / pandas | 2.3.5 / 3.0.1 | 数据读写与统计 |
| matplotlib | 3.11.2（经 `_tools` 挂载） | 插图重绘 |
| Node.js | 20+（实测 24.15.0） | 仅大模型代理 `server.mjs` |

Windows PowerShell 5.1 即可运行两个 `.ps1`（文件为 UTF-8 with BOM；若另存为无 BOM 会报 ParserError）。
