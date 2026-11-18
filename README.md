# 成果附件：可视化驾驶舱系统 + 流程 skill

本目录是期末论文《从数据到决策：电商经营多维交互式可视化大屏的设计与实现》的成果附件，分两部分：

| 目录 | 是什么 | 给谁用 |
|---|---|---|
| `project\` | **可直接运行、可复现论文全部数据与图表的系统**：540 行数据、复算与绘图脚本、11 张插图、静态驾驶舱、零依赖 Node 代理（大模型问答） | 想复现、演示、修改这套系统 |
| `project_skill\` | **把做法抽象出的流程 skill**：`SKILL.md` + `resync.ps1` / `smoke.ps1` / `install.ps1` | 想把这套工序用到另一份数据、另一个选题 |

另有三份说明：

| 文件 | 内容 |
|---|---|
| `README.md` | 本文件：结构与上手路径 |
| `REPRODUCE.md` | 复现报告：论文数字怎么复算、换数据会怎样、哪些东西不能"重放"、实测校验值 |
| `CHECKSUMS.txt` | 本目录全部文件的 SHA256 与字节数 |

## 五分钟上手

1. **先确认能复现**：读 `REPRODUCE.md` 的「路径 A」，用 `project\data\ecommerce_dashboard_data.csv` 重跑 `analyze.py` 与 `figs.py`，统计与插图应与论文完全一致（实测逐字节一致）。
2. **跑一遍系统**：按 `project\README.md` 起静态页（`node project\dashboard\server.mjs`，浏览器开 `http://127.0.0.1:8000/`）。
3. **换一份数据重走全链路**：

   ```powershell
   powershell -ExecutionPolicy Bypass -File project_skill\scripts\resync.ps1 -Regenerate -Seed 7
   ```

   它会依次生成数据 → 统计 → 插图 → `data.js`，并打印需要回填论文的数字。
4. **装成 DSH 项目级 skill**（可选）：

   ```powershell
   powershell -ExecutionPolicy Bypass -File project_skill\scripts\install.ps1
   ```

## 两部分的分工

`project\` 回答「这篇论文的系统是什么样、能不能复现」；`project_skill\` 回答「换一份数据、换一个选题，这套做法还能不能走通」。

前者是一次性的交付物，后者是抽取出的工序：数据是输入而不是常量、数字只认一个来源（`analysis_stats.json`）、自检不写死业务值、大模型只解释既有视图。后三条在论文第 3、5 章是论点，在 `project_skill` 里是约束。

## 验证状态

| 检查 | 结果 |
|---|---|
| 论文数字复算（`analyze.py`） | `analysis_stats.json` 与交付版逐字节一致（SHA256 `E9813487…8865D`） |
| 插图重绘（`figs.py`） | 11 张 PNG 全部逐字节一致 |
| 页面数据（`build_data_js.py --check`） | 通过（80,000 B） |
| 结构体检（`smoke.ps1`） | `PASS 14 WARN 0 FAIL 0` |
| 换数闭环（临时副本 `-Seed 7`） | 1388.42 万 GMV / ROAS 3.0581 / CV 9.99%，图与 `data.js` 同步更新，体检 `PASS 12 WARN 1 FAIL 0` |
| skill 安装（`install.ps1`） | 正确生成 `.dsh\skills\ecom-viz-paper\{SKILL.md, scripts\*}`，安装后体检通过 |

未验证：换一份**字段完全不同**的 CSV（需手动改 `analyze.py` / `figs.py` / `app.js` 的列名，流程支持但未实测）。
