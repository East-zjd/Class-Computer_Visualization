# 项目说明：电商经营数据的交互式可视分析与智能问答

本目录是期末论文《从数据到决策：面向模拟经营数据的交互式可视分析与智能问答系统》的配套工程，包含数据生成、统计复算、插图绘制与前端驾驶舱四部分。

> **数据声明**：`data/` 下的经营数据由 `scripts/data_generate.py` 以固定随机种子（42）程序生成，**并非真实经营数据**，仅用于演示数据处理流程与可视化方法，不能作为任何商业判断的依据。论文中的全部数字均可由本目录脚本复算得到。

## 目录结构

```
project/
├─ README.md                     本文件
├─ analysis_stats.json           analyze.py 的输出：论文表 4/表 5 与正文数字的来源
├─ dashboard/                    前端驾驶舱（纯静态，可离线运行）
│  ├─ index.html                 页面结构：筛选栏、指标卡、趋势、品类、渠道、明细表、AI 助手
│  ├─ app.js                     聚合、渲染、SVG 绘图、本地规则问答、导出
│  ├─ data.js                    数据快照（与 data/*.csv 同源）
│  ├─ server.mjs                 可选的大模型代理服务（Node 20+，零依赖；GET /api/health、POST /api/chat、--check 自检）
│  └─ README.md                  驾驶舱的详细使用说明
├─ data/                         数据集
│  ├─ ecommerce_dashboard_data.csv   主数据集：540 条（30 天 × 6 品类 × 3 渠道）
│  ├─ visualization_business_data.csv 辅助数据集：300 家企业经营指标（用于跨域气泡图）
│  ├─ study_performance_adv.csv      课程作业数据：学习时长与成绩（20 条，取自 task3）
│  └─ course_metrics.csv             课程作业数据：提交设备与成绩（18 条，取自 task2）
├─ scripts/
│  ├─ data_generate.py           生成数据集（--seed/--days/--start/--out/--force，默认 seed=42）
│  ├─ analyze.py                 统计复算，输出 analysis_stats.json
│  └─ figs.py                    绘制论文插图，输出到 figures/
├─ ai-log/
│  └─ conversation-export.md     与 AI 助手的完整对话记录（论文附录 B 的全文出处）
└─ figures/                      脚本产出的插图（PNG，300 dpi 左右）
```

## 复现步骤

1. **准备数据（用现成样本，或换一份）**

   `data/ecommerce_dashboard_data.csv` 是当前论文引用的那份样本，**统计、插图、页面都以它为准**。它是生成的，可以换：

   ```bash
   python scripts/data_generate.py                    # 只看规模与合计，不写盘
   python scripts/data_generate.py --seed 7 --force    # 生成另一份样本（也支持 --days 60 / --start 2026-10-01）
   python scripts/data_generate.py --out ../data/demo.csv --seed 7 --force   # 写到别的文件，不动主数据
   ```

   生成规则（论文 2.1 节）：6 品类 × 3 渠道 × N 天，各品类有独立的 ROI / 转化率 / 跳出率区间，随机流由 `--seed` 决定。

   **换完数据必须重算下游**——统计、插图、`data.js`、以及论文里的每一个数字都依赖它：

   ```powershell
   powershell -ExecutionPolicy Bypass -File ..\project_skill\scripts\resync.ps1 -Regenerate -Seed 7
   ```

   它会依次跑 生成 → `analyze.py` → `figs.py` → `build_data_js.py`，最后打印「论文数字看板」（总量、ROAS、CV、最差环比、品类/渠道表）。不想重绘插图时加 `-NoFigures`；换的是自己的 CSV 时去掉 `-Regenerate`。

   > **改了 `seed` 页面却没变化？** 因为 `index.html` 只加载 `dashboard/data.js`（`window.DATA` 的静态快照），**从不读 CSV**。链路是：CSV → `build_data_js.py` → `dashboard/data.js` → 浏览器 **Ctrl+F5**（`data.js` 会被缓存，普通 F5 常常还是旧图）。是否已同步用 `python scripts/build_data_js.py --check` 判断（一致返回 0）。

2. **复算统计口径**
   ```bash
   python scripts/analyze.py
   ```

   输出 `analysis_stats.json`，其中 `total_gmv`、`total_spend`、`roas`、`avg_cvr`、`avg_bounce` 与各品类、各渠道指标即论文表 4、表 5 的来源。

3. **重绘插图**

   ```bash
   python scripts/figs.py
   ```

   输出到 `figures/`。脚本使用中文字体 `Microsoft YaHei`，如系统缺失需在脚本开头替换 `font.family`。

4. **运行驾驶舱**

   直接双击 `dashboard/index.html` 即可离线使用：筛选、联动、悬停提示、明细表与本地规则问答均由前端完成，不依赖网络。

   要启用大模型问答，先确认端点可用，再启动本地代理（零依赖，无需 `npm install`）：

   ```powershell
   cd dashboard

   # 云端：写明服务商即可，端点与默认模型自动带出
   $env:AI_PROVIDER = 'deepseek'      # deepseek / openai / siliconflow / dashscope
   $env:AI_API_KEY  = '<你的密钥>'

   # 或本地模型（不出网、无需密钥）
   # $env:AI_PROVIDER = 'ollama'      # 需先 ollama serve 且已 pull 模型

   node server.mjs --check            # 先自检：配置 → /models → 一次补全
   node server.mjs                    # 再启动 http://127.0.0.1:8000
   ```

   也可以把 `AI_PROVIDER`/`AI_API_KEY`/`AI_MODEL` 写进 `dashboard/.ai-config.local.json`（环境变量优先）。密钥只保存在 Node 进程里，页面与静态路由都接触不到；没有密钥时，界面自动退回可核验的本地规则分析。浏览器打开 `http://127.0.0.1:8000/api/health` 可看到 `ok`、`upstreamReachable`、`models` 等字段。

   完整的配置项、预设表、排错表与验证记录见 `dashboard/README.md`。

## 配套流程 skill：`..\project_skill\`

本目录（`result\project\`）是**可直接运行、可复现论文数据与图表**的系统；与它同级的 `result\project_skill\` 是把这套做法抽象出来的流程 skill（`SKILL.md` + 脚本），回答"换一份数据、换一个选题，同样的方法论怎么再走一遍"。两者合起来构成论文的成果附件。

两个脚本（都支持 `-Project` 指定目标目录；不带参数时会自己找到同级/上级的 `result\project`）：

```powershell
# 1) 换数据后一键重算，并打印「论文数字看板」
powershell -ExecutionPolicy Bypass -File ..\project_skill\scripts\resync.ps1 -Regenerate -Seed 7

# 2) 结构体检（只查一致性，不写死任何统计值，换 seed 后不会误报）
powershell -ExecutionPolicy Bypass -File ..\project_skill\scripts\smoke.ps1
```

`smoke.ps1` 检查：必需文件、CSV 必需列与行数、`analysis_stats.json` 是否比 CSV 旧、9 张论文插图是否存在且不早于 CSV、`data.js` 是否与 CSV 一致（调 `build_data_js.py --check`）、三个 JS 的 `node --check`、docx 是否存在；最后打印当前关键数字供人工对照。有 FAIL 时退出码为 1。想把 skill 装进 DSH 会话的 skill 目录，跑 `..\project_skill\scripts\install.ps1`。

## 环境依赖

- Python 3.12：`pandas`、`numpy`、`matplotlib`（`pip install -r requirements.txt`）
- Node.js 20+：仅在启用大模型代理时需要
- 浏览器：Chrome / Edge 等现代浏览器（使用原生 SVG 与 ES 模块，无构建步骤）

> 换一台机器复现时，最容易踩的坑是**终端里的 `python` 指向另一个解释器**（例如只装了 Flask/requests 的那个），于是报 `ModuleNotFoundError: No module named 'numpy'`。先跑 `python -c "import numpy, pandas, matplotlib; print('ok')"` 确认，再执行下面三步。

## 环境自检：`scripts/check_env.py`

`ModuleNotFoundError: No module named 'numpy'` 有两种成因，必须分清：一是真的没装，二是**标准库被改坏**（例如 `Lib\json\__init__.py` 被别的脚本覆盖），后者会让 `pip` 自己都启动不了，装包永远失败。`check_env.py` 只用标准库实现（顶层仅 `import os/re/sys`），所以**即使解释器已经坏了，它也能跑出诊断**：

```bat
python scripts\check_env.py            :: 六节体检：解释器 / 61 个核心标准库 / json 专项 / 标准库全量扫描 / 依赖 / 项目文件
python scripts\check_env.py --snapshot :: 体检通过后，为当前解释器记录标准库哈希基线
python scripts\check_env.py --verify   :: 与基线逐文件比对，秒级查出新增、缺失、被改
```

退出码 0 = 可用于本项目，1 = 存在 FAIL。检出问题时它会直接点名文件，例如：

```
[FAIL] json\__init__.py  3032 B  ← 过小，疑似被覆盖
       命中特征：from transformers
```

### venv 的坑：它不隔离标准库

`venv` 只复制解释器与 `Scripts\`，标准库仍由 `pyvenv.cfg` 里的 `home` 指向**基座安装目录**。因此：

- 基座的 `Lib` 一旦被污染，**同一机器上所有 venv 一起坏**（本次 py 3.12.9 下的 4 个 venv 全部在 `import json` 处崩溃，修复基座后无需重建即自动恢复）；
- 反过来，`pip install` 装进 venv 的第三方包彼此隔离，这部分 `venv` 是有效的；
- 想要**标准库级隔离**，只能用 **conda**（每个环境自带一份完整标准库），或再装一份独立的官方 Python（不同大版本目录天然分开）。

日常防护最小成本方案：装包或跑脚本前先 `python scripts\check_env.py`，标准库有改动时用 `--verify` 定位到具体文件。

## 插图与论文图号的对应

`scripts/figs.py` 一次产出 11 张图，论文按出现顺序引用其中 9 张：

| 文件 | 论文图号 | 内容 |
| --- | --- | --- |
| `fig2_pipeline.png` | 图 1 | 数据预处理与特征工程流水线 |
| `fig9_color.png` | 图 2 | 反例色板与三级色彩体系 |
| `fig1_arch.png` | 图 3 | 驾驶舱的五层架构 |
| `fig10_agent.png` | 图 4 | 五步工作流与护栏 |
| `fig5_trend.png` | 图 5 | 日度 GMV 与广告花费 |
| `fig4_category.png` | 图 6 | 品类 GMV 贡献与投放效率 |
| `fig8_cvr_bounce.png` | 图 7 | 转化率与跳出率的负相关 |
| `fig6_scatter.png` | 图 8 | 花费—GMV 多维散点 |
| `fig7_heatmap.png` | 图 9 | 品类 × 渠道投放效率矩阵 |
| `fig3_evolution.png` | 未收入 | 课程任务能力演进（正文删除该小节） |
| `fig11_biz.png` | 未收入 | 跨域气泡图（正文删除该小节） |

## 指标口径

- 金额：`GMV` 与 `Ad_Spend` 均为区间内求和；`ROAS = ΣGMV / ΣAd_Spend`，**不等于利润 ROI**。
- 比率：`Conversion_Rate` 与 `Bounce_Rate` 为「记录级算术均值」。原始数据没有访客数、会话数、订单数等分母，因此不能计算加权总转化率，也不能由比率反推订单量。
- 环比：`Δ(t) = [G(t) − G(t−1)] / G(t−1)`，仅在相邻两天都有数据时成立；单日筛选无法计算环比。缺失日期时界面显式说明间隔。
- 异常：本地问答中的“异常”指相邻有数据日期之间的最大环比下降，属于描述性信号，不做显著性检验，也不构成因果结论。

## 已知边界

- 默认样本覆盖 2026-09-01 至 2026-09-30，无实时接入；换数据靠 `data_generate.py --seed N --force`（或直接替换 CSV），刷新页面不会产生新数据。
- 数据是**可换的输入**，但论文里的数字只认 `analysis_stats.json`：换数后必须跑 `resync.ps1` 重算统计、插图与 `data.js`，并按数字看板回填论文，否则图、页面与正文会互相矛盾。
- 驾驶舱是离线静态页：`index.html` 只读 `dashboard/data.js` 这份编译产物，不读 CSV；换数据必须重跑 `scripts/build_data_js.py` 并 Ctrl+F5。
- 前端未实现撤销、操作历史与可分享链接；导出的 CSV 为当前筛选结果。
- 大模型代理链路已用本地 OpenAI 兼容桩完成端到端验证（配置解析、`--check` 自检、`/api/health`、`/api/chat`、四类错误分支），但**真实厂商调用未在本机验证**，因为环境中没有可用密钥；配好密钥后请先跑 `node server.mjs --check`。
- 未做在线评测，论文不报告任何准确率、效率或收益指标。
