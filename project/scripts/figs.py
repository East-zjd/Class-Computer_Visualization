# -*- coding: utf-8 -*-
"""生成论文插图（基于真实 CSV 数据，matplotlib 输出 PNG）。"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.ticker as mtick
import matplotlib.dates as mdates
from datetime import timedelta

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(WS, "figures")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.family": "Microsoft YaHei",
    "font.size": 10.5,
    "axes.unicode_minus": False,
    "axes.edgecolor": "#B9C2CE",
    "axes.labelcolor": "#243447",
    "text.color": "#1B2430",
    "xtick.color": "#52606D",
    "ytick.color": "#52606D",
    "axes.grid": True,
    "grid.color": "#E6EAF0",
    "grid.linewidth": 0.8,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

NAVY = "#243447"
INK = "#1B2430"
MUTED = "#52606D"
BLUE = "#2E6BE6"
TEAL = "#2A9D8F"
ORANGE = "#E4703F"
GREY = "#8C9AA8"

CAT_COLORS = {
    "3C数码": "#2E6BE6",
    "美妆个护": "#E4703F",
    "智能家居": "#2A9D8F",
    "户外运动": "#8E6CBF",
    "运动服饰": "#E0A526",
    "数码配件": "#5FA8D3",
}

df = pd.read_csv(os.path.join(WS, "data", "ecommerce_dashboard_data.csv"), encoding="utf-8-sig")
df["Date"] = pd.to_datetime(df["Date"])

def save(fig, name, dpi=220):
    fig.savefig(os.path.join(OUT, name), dpi=dpi, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print("saved", name)

def box(ax, x, y, w, h, text, fc="#F4F7FC", ec="#B9C2CE", fs=9.5, bold=False, tc=INK, r=0.02):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.004,rounding_size={r}",
                                linewidth=1.0, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=tc, fontweight="bold" if bold else "normal", zorder=3, linespacing=1.5)

def arrow(ax, x1, y1, x2, y2, color=MUTED, lw=1.2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13,
                                 color=color, linewidth=lw, zorder=4, shrinkA=0, shrinkB=0))

# ---------------- 图1 系统架构（自下而上） ----------------
fig, ax = plt.subplots(figsize=(11.0, 6.2))
ax.set_xlim(0, 10.4); ax.set_ylim(0.2, 9.9); ax.axis("off")
layers = [
    (7.85, "智能层", "本地规则分析器（可核验口径）· 服务端大模型代理 · 系统提示词护栏 · 问答上下文快照", "#EAF1FD"),
    (6.20, "交互层", "日期 / 品类 / 渠道筛选 · 图—表双向联动 · 悬停提示 · 当前视图导出 · 状态记忆", "#EFF6F4"),
    (4.55, "表达层", "KPI 指标卡 · 趋势折线 · 品类贡献条 · 渠道效率条 · 明细表 · 叙事型短片", "#FBF3EC"),
    (2.90, "数据层", "data.js 本地快照 · 类型与范围校验 · 派生指标 · 指标口径字典", "#F4F7FC"),
    (1.25, "数据源层", "电商经营台账（540 条）· 校园学习行为 · 企业 SaaS 经营指标", "#F2F4F7"),
]
for y, name, desc, fc in layers:
    box(ax, 0.3, y, 1.7, 1.15, name, fc=NAVY, ec=NAVY, fs=11.5, bold=True, tc="white")
    box(ax, 2.25, y, 7.55, 1.15, desc, fc=fc, fs=9.4)

for ylow, yhigh in [(1.25, 2.90), (2.90, 4.55), (4.55, 6.20), (6.20, 7.85)]:
    arrow(ax, 6.0, ylow + 1.17, 6.0, yhigh - 0.02, color=BLUE)

ax.text(0.3, 9.55, "电商经营智能可视化驾驶舱的分层架构", fontsize=11.5, color=NAVY, fontweight="bold")
save(fig, "fig1_arch.png")

# ---------------- 图2 数据流水线 ----------------
fig, ax = plt.subplots(figsize=(11.0, 3.4))
ax.set_xlim(0, 10); ax.set_ylim(1.0, 3.55); ax.axis("off")
stages = [
    ("① 原始台账", "540 行 × 7 列\n2026-09-01—09-30", "540"),
    ("② 结构校验", "字段类型、取值范围\n日期连续性", "0 缺陷"),
    ("③ 清洗修补", "重复值、缺失值\n异常值标记", "540 保留"),
    ("④ 派生特征", "ROAS、份额\n环比、交叉维度", "+4 指标"),
    ("⑤ 维度规约", "日 / 品类 / 渠道\n6×3×30 立方", "18 组"),
    ("⑥ 视图数据", "6 图 1 表\n问答上下文", "7 视图"),
]
w, gap = 1.40, 0.26
for i, (title, desc, badge) in enumerate(stages):
    x = 0.14 + i * (w + gap)
    box(ax, x, 1.55, w, 1.75, "", fc="#F4F7FC", ec="#B9C2CE")
    ax.text(x + w / 2, 2.98, title, ha="center", va="center", fontsize=9.3, fontweight="bold", color=NAVY)
    ax.text(x + w / 2, 2.36, desc, ha="center", va="center", fontsize=8.2, color=MUTED, linespacing=1.55)
    ax.text(x + w / 2, 1.80, badge, ha="center", va="center", fontsize=8.2, color=BLUE, fontweight="bold")
    if i < len(stages) - 1:
        arrow(ax, x + w + 0.01, 2.42, x + w + gap - 0.01, 2.42, color=BLUE)
ax.text(0.14, 1.18, "质量闸门：日期唯一性、金额与比率为负值的拦截、品类×渠道×日期组合完备（6×3×30=540）",
        fontsize=8.6, color=MUTED)
save(fig, "fig2_pipeline.png")

# ---------------- 图3 课程任务演进 ----------------
fig, ax = plt.subplots(figsize=(11.0, 3.9))
ax.set_xlim(0, 10); ax.set_ylim(0.2, 5.0); ax.axis("off")
ax.plot([0.45, 9.55], [2.95, 2.95], color="#D5DCE6", lw=3.2, solid_capstyle="round", zorder=1)
tasks = [
    ("T1", "温度与天气\n静态图表", "静态编码"),
    ("T2", "设备分布\nKDE + 散点", "统计图形"),
    ("T3", "离群点与\n回归解释", "统计推断"),
    ("T4", "上座率热力图\n交互联动", "交互探索"),
    ("T5", "三维场景\nBlender", "空间隐喻"),
    ("T6", "数据短片\n叙事分镜", "叙事可视化"),
    ("T7", "色彩工程\n配色规范", "视觉设计"),
    ("T8", "AI 驾驶舱\n智能问答", "智能交互"),
]
xs = np.linspace(0.9, 9.1, len(tasks))
for (tag, title, cap), x in zip(tasks, xs):
    up = int(tag[1]) % 2 == 1
    ax.add_patch(Circle((x, 2.95), 0.11, color=BLUE if up else TEAL, zorder=4))
    if up:
        ax.plot([x, x], [3.06, 3.62], color="#C9D2DE", lw=1, zorder=1)
        ax.text(x, 4.52, tag, ha="center", fontsize=9.6, fontweight="bold", color=BLUE)
        ax.text(x, 4.02, title, ha="center", va="center", fontsize=8.6, color=INK, linespacing=1.5)
        ax.text(x, 3.40, cap, ha="center", fontsize=8.0, color=MUTED)
    else:
        ax.plot([x, x], [2.84, 2.28], color="#C9D2DE", lw=1, zorder=1)
        ax.text(x, 1.42, tag, ha="center", fontsize=9.6, fontweight="bold", color=TEAL)
        ax.text(x, 1.92, title, ha="center", va="center", fontsize=8.6, color=INK, linespacing=1.5)
        ax.text(x, 2.54, cap, ha="center", fontsize=8.0, color=MUTED)
ax.text(0.45, 0.72, "能力演进：静态编码 → 统计表达 → 交互探索 → 空间隐喻 → 叙事 → 设计规范 → 智能决策",
        fontsize=8.8, color=MUTED)
save(fig, "fig3_evolution.png")

# ---------------- 图4 品类贡献与 ROAS ----------------
cat = df.groupby("Category").agg(GMV=("GMV", "sum"), Spend=("Ad_Spend", "sum")).reset_index()
cat["ROAS"] = cat.GMV / cat.Spend
cat = cat.sort_values("GMV", ascending=False)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.2, 5.8), sharex=True,
                               gridspec_kw={"height_ratios": [2.3, 1.0], "hspace": 0.12})
x = np.arange(len(cat))
ax1.bar(x, cat.GMV / 1e4, width=0.56, color=[CAT_COLORS[c] for c in cat.Category], alpha=0.92, zorder=3)
ax1.set_ylabel("GMV（万元）", fontsize=10)
ax1.set_ylim(0, 380)
ax1.grid(axis="x", visible=False)
for xi, v in zip(x, cat.GMV / 1e4):
    ax1.text(xi, v + 7, f"{v:.0f}", ha="center", va="bottom", fontsize=9.2, color=INK, fontweight="bold")
ax1.set_title("品类 GMV 贡献与投放效率（2026-09）", fontsize=11.5, color=NAVY, pad=12)

ax2.axhline(3.0485, color=GREY, lw=1.1, ls="--", zorder=2)
ax2.text(len(cat) - 0.45, 3.085, "整体 ROAS 3.05", ha="right", fontsize=8.4, color=GREY)
ax2.vlines(x, 2.2, cat.ROAS, color="#D5DCE6", lw=1.2, zorder=2)
ax2.scatter(x, cat.ROAS, s=70, color=NAVY, zorder=4)
for xi, v in zip(x, cat.ROAS):
    ax2.annotate(f"{v:.2f}×", (xi, v), textcoords="offset points", xytext=(10, -3),
                 fontsize=9, color=NAVY, va="center")
ax2.set_ylim(2.2, 4.75)
ax2.set_ylabel("ROAS（倍）", fontsize=10)
ax2.set_xticks(x); ax2.set_xticklabels(cat.Category, fontsize=10)
ax2.grid(axis="x", visible=False)
save(fig, "fig4_category.png")

# ---------------- 图5 日度趋势 ----------------
daily = df.groupby("Date").agg(GMV=("GMV", "sum"), Spend=("Ad_Spend", "sum")).reset_index()
fig, ax = plt.subplots(figsize=(10.4, 4.5))
ax.fill_between(daily.Date, daily.GMV / 1e4, color=BLUE, alpha=0.07)
ax.plot(daily.Date, daily.GMV / 1e4, color=BLUE, lw=2.0, marker="o", ms=3.2, label="GMV", zorder=4)
ax.plot(daily.Date, daily.Spend / 1e4, color=ORANGE, lw=1.8, marker="o", ms=3.0, label="广告花费", zorder=4)
ax.set_ylabel("金额（万元）", fontsize=10)
ax.set_ylim(0, 72)
ax.set_xlim(daily.Date.min() - timedelta(hours=12), daily.Date.max() + timedelta(hours=12))
ax.grid(axis="x", visible=False)
ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
peak = daily.loc[daily.GMV.idxmax()]
low = daily.loc[daily.GMV.idxmin()]
ax.annotate(f"峰值 {peak.GMV/1e4:.1f} 万（09-28）", xy=(peak.Date, peak.GMV / 1e4),
            xytext=(-108, 24), textcoords="offset points", fontsize=8.8, color=NAVY,
            arrowprops=dict(arrowstyle="-", color=GREY, lw=1))
ax.annotate(f"谷值 {low.GMV/1e4:.1f} 万（09-13）", xy=(low.Date, low.GMV / 1e4),
            xytext=(-30, -34), textcoords="offset points", fontsize=8.8, color=MUTED,
            arrowprops=dict(arrowstyle="-", color=GREY, lw=1))
d19 = daily[daily.Date == "2026-09-19"].iloc[0]
ax.scatter([d19.Date], [d19.GMV / 1e4], s=95, facecolor="white", edgecolor=ORANGE, lw=1.8, zorder=6)
ax.annotate("09-19 环比 −20.4%，全月唯一超过 15% 的单日回落", xy=(d19.Date, d19.GMV / 1e4),
            xytext=(-140, 96), textcoords="offset points", fontsize=8.8, color=ORANGE,
            arrowprops=dict(arrowstyle="-", color=ORANGE, lw=1))
ax.legend(loc="upper left", frameon=False, fontsize=9, ncol=2)
ax.set_title("日度 GMV 与广告花费（2026-09-01—09-30）", fontsize=11.5, color=NAVY, pad=12)
save(fig, "fig5_trend.png")

# ---------------- 图6 多维散点 ----------------
fig, ax = plt.subplots(figsize=(8.8, 5.2))
for c, color in CAT_COLORS.items():
    sub = df[df.Category == c]
    ax.scatter(sub.Ad_Spend, sub.GMV, s=30 + (sub.Conversion_Rate * 100 - 5) ** 2 * 1.2,
               color=color, alpha=0.6, edgecolor="white", linewidth=0.5, label=c, zorder=3)
ax.set_xlabel("单日单渠道广告花费（元）", fontsize=10)
ax.set_ylabel("单日单渠道 GMV（元）", fontsize=10)
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, p: f"{v/1e4:.1f}万"))
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, p: f"{v/1e4:.1f}万"))
xs = np.linspace(df.Ad_Spend.min(), df.Ad_Spend.max(), 50)
ys = xs * (df.GMV.sum() / df.Ad_Spend.sum())
ax.plot(xs, ys, color=NAVY, lw=1.4, ls="--", zorder=4)
ax.annotate("整体 ROAS = 3.05", xy=(xs[-6], ys[-6]), xytext=(-18, 16), textcoords="offset points",
            fontsize=8.8, color=NAVY, ha="right")
leg = ax.legend(frameon=False, fontsize=8.6, loc="upper left", ncol=2, markerscale=0.55,
                handletextpad=0.4, columnspacing=1.2)
ax.set_title("花费—GMV 多维散点（颜色＝品类，面积＝转化率）", fontsize=11.3, color=NAVY, pad=10)
save(fig, "fig6_scatter.png")

# ---------------- 图7 热力图 ----------------
pairs = df.groupby(["Category", "Channel"]).agg(GMV=("GMV", "sum"), Spend=("Ad_Spend", "sum")).reset_index()
pairs["ROAS"] = pairs.GMV / pairs.Spend
mat = pairs.pivot(index="Category", columns="Channel", values="ROAS")
mat = mat.loc[["3C数码", "美妆个护", "智能家居", "数码配件", "运动服饰", "户外运动"], ["App端", "小程序", "网页端"]]
fig, ax = plt.subplots(figsize=(6.4, 4.4))
cmap = LinearSegmentedColormap.from_list("seq", ["#F2F7F6", "#CDE8E2", "#9ED3C8", "#2A9D8F", "#1F7A70"])
im = ax.imshow(mat.values, cmap=cmap, aspect="auto", vmin=2.2, vmax=4.5)
ax.set_xticks(np.arange(mat.shape[1])); ax.set_xticklabels(mat.columns, fontsize=10)
ax.set_yticks(np.arange(mat.shape[0])); ax.set_yticklabels(mat.index, fontsize=10)
ax.grid(False)
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        v = mat.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=9.5,
                color="white" if v > 3.4 else INK, fontweight="bold")
cb = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
cb.set_label("ROAS（倍）", fontsize=9)
cb.outline.set_visible(False)
ax.set_title("品类 × 渠道 投放效率矩阵", fontsize=11.3, color=NAVY, pad=10)
save(fig, "fig7_heatmap.png")

# ---------------- 图8 CVR vs Bounce ----------------
fig, ax = plt.subplots(figsize=(8.2, 4.8))
for c, color in CAT_COLORS.items():
    sub = df[df.Category == c]
    ax.scatter(sub.Bounce_Rate * 100, sub.Conversion_Rate * 100, s=26, color=color,
               alpha=0.65, edgecolor="white", linewidth=0.4, label=c, zorder=3)
z = np.polyfit(df.Bounce_Rate * 100, df.Conversion_Rate * 100, 1)
xs = np.linspace(18, 72, 60)
ax.plot(xs, np.polyval(z, xs), color=NAVY, lw=1.6, ls="--", zorder=4)
r = df.Conversion_Rate.corr(df.Bounce_Rate)
ax.text(0.03, 0.95, f"Pearson r = {r:.3f}（n = 540）\n拟合斜率 {z[0]:.3f} 个百分点 / 个百分点",
        transform=ax.transAxes, fontsize=9, color=NAVY, va="top")
ax.set_xlabel("跳出率（%）", fontsize=10)
ax.set_ylabel("转化率（%）", fontsize=10)
ax.set_ylim(0, 32)
ax.legend(frameon=False, fontsize=8.4, ncol=3, loc="lower left")
ax.set_title("转化率与跳出率的强负相关", fontsize=11.3, color=NAVY, pad=10)
save(fig, "fig8_cvr_bounce.png")

# ---------------- 图9 色彩方案 ----------------
def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def contrast(hex1, hex2="#FFFFFF"):
    a = tuple(_lin(int(hex1[i:i+2], 16)) for i in (1, 3, 5))
    b = tuple(_lin(int(hex2[i:i+2], 16)) for i in (1, 3, 5))
    la = 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]
    lb = 0.2126 * b[0] + 0.7152 * b[1] + 0.0722 * b[2]
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

cr = contrast("#1B2430")
fig = plt.figure(figsize=(10.2, 4.9))
gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.22], wspace=0.16)
axl = fig.add_subplot(gs[0]); axl.axis("off"); axl.set_xlim(0, 10); axl.set_ylim(0, 10)
axl.set_title("（a）反例：彩虹色阶与红绿同现", fontsize=10.5, color="#B03A2E", pad=8)
bad = ["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#00BFFF", "#4B0082", "#FF00FF"]
for i, c in enumerate(bad):
    axl.add_patch(Rectangle((0.3 + i * 1.38, 7.4), 1.24, 1.3, facecolor=c, edgecolor="white"))
axl.text(0.3, 6.7, "① 7 类数据共用高饱和彩虹色：相邻类别难以区分；\n"
                   "② 红绿同时出现：红绿色盲者（约 8% 男性）无法辨读；\n"
                   "③ 明度不均：黄色区块在浅色背景上几乎消失。",
         fontsize=8.5, color=MUTED, linespacing=1.9, va="top")
axr = fig.add_subplot(gs[1]); axr.axis("off"); axr.set_xlim(0, 10); axr.set_ylim(0, 10)
axr.set_title("（b）本文规范：定性 × 顺序 × 语义三级色彩体系", fontsize=10.5, color=NAVY, pad=8)
qual = ["#2E6BE6", "#E4703F", "#2A9D8F", "#8E6CBF", "#E0A526", "#5FA8D3"]
axr.text(0.15, 9.15, "定性（品类身份，6 色）", fontsize=8.8, color=NAVY, fontweight="bold")
for i, c in enumerate(qual):
    axr.add_patch(Rectangle((0.15 + i * 1.55, 7.55), 1.35, 1.25, facecolor=c, edgecolor="white"))
    axr.text(0.15 + i * 1.55 + 0.675, 7.20, c.upper(), ha="center", fontsize=6.6, color=MUTED)
seq = ["#F2F7F6", "#CDE8E2", "#9ED3C8", "#5CBBA9", "#2A9D8F", "#1F7A70", "#17554E"]
axr.text(0.15, 6.25, "顺序（ROAS 高低，单色相＋明度梯度）", fontsize=8.8, color=NAVY, fontweight="bold")
for i, c in enumerate(seq):
    axr.add_patch(Rectangle((0.15 + i * 1.33, 4.75), 1.2, 1.0, facecolor=c, edgecolor="white"))
sem = [("#2A9D8F", "正向 / 达标"), ("#E0A526", "警示 / 临界"), ("#E4703F", "异常 / 下降")]
axr.text(0.15, 3.85, "语义（固定含义，全站复用）", fontsize=8.8, color=NAVY, fontweight="bold")
for i, (c, lab) in enumerate(sem):
    axr.add_patch(Rectangle((0.15 + i * 3.25, 2.45), 0.85, 0.72, facecolor=c, edgecolor="white"))
    axr.text(0.15 + i * 3.25 + 1.0, 2.81, lab, fontsize=8.6, color=INK, va="center")
axr.text(0.15, 1.55, f"正文色 #1B2430 于白底对比度 {cr:.1f}:1（WCAG AA 需 ≥4.5:1）；\n"
                     "分类色在色相环上彼此远离，顺序色阶明度单调递减，\n"
                     "可在灰度打印与红色盲模拟下保持可辨识。",
         fontsize=8.3, color=MUTED, linespacing=1.8, va="top")
save(fig, "fig9_color.png")

# ---------------- 图10 AI 工作流 ----------------
fig, ax = plt.subplots(figsize=(9.6, 5.2))
ax.set_xlim(0, 10); ax.set_ylim(0, 6.05); ax.axis("off")
ax.text(0.25, 5.72, "从“被动呈现”到“智能决策”的五步工作流", fontsize=11.3, color=NAVY, fontweight="bold")
steps = [
    ("看", "视图呈现\n发现变化"),
    ("问", "自然语言\n意图识别"),
    ("分析", "口径注入\n规则 / 模型"),
    ("验证", "事实分层\n可核验数字"),
    ("行动", "建议动作\n联动筛选"),
]
w, gap = 1.62, 0.31
for i, (t, d) in enumerate(steps):
    x = 0.25 + i * (w + gap)
    box(ax, x, 2.95, w, 1.55, "", fc="#EFF6F4" if t == "验证" else "#EAF1FD", ec="#B9C2CE")
    ax.text(x + w / 2, 4.08, t, ha="center", fontsize=12.5, fontweight="bold", color=NAVY)
    ax.text(x + w / 2, 3.42, d, ha="center", fontsize=8.4, color=MUTED, linespacing=1.5)
    if i < 4:
        arrow(ax, x + w + 0.02, 3.72, x + w + gap - 0.02, 3.72, color=BLUE)
ax.plot([9.2, 9.2, 1.19], [4.5, 5.20, 5.20], color=GREY, lw=1.1, zorder=1)
arrow(ax, 1.19, 5.20, 1.19, 4.62, color=GREY)
ax.text(5.2, 5.20, "反馈回路：行动结果回写视图与筛选状态", ha="center", va="center", fontsize=8.6,
        color=GREY, bbox=dict(facecolor="white", edgecolor="none", pad=2.0), zorder=3)
box(ax, 0.25, 0.35, 9.35, 2.05, "", fc="#FBF3EC", ec="#E4C9B4")
ax.text(0.5, 2.06, "护栏（Guardrails）", fontsize=9.2, fontweight="bold", color="#9A5B33")
ax.text(0.5, 1.66, "① 只依据当前筛选快照作答，禁止编造数据；无密钥时自动降级为可核验的规则分析。", fontsize=8.3, color=MUTED)
ax.text(0.5, 1.16, "② 输出区分事实 / 假设 / 建议；固化口径：ROAS ≠ 利润 ROI，比率为算术均值。", fontsize=8.3, color=MUTED)
ax.text(0.5, 0.66, "③ 相关不等于因果；数据内容不得改写系统指令（提示注入防护）。", fontsize=8.3, color=MUTED)
save(fig, "fig10_agent.png")

# ---------------- 图11 企业 SaaS 数据复现 ----------------
b = pd.read_csv(os.path.join(WS, "data", "visualization_business_data.csv"))
b["RD_int"] = b.R_and_D_Spend_M / b.Annual_Revenue_M * 100
fig, ax = plt.subplots(figsize=(8.6, 5.0))
sector_colors = {"Enterprise AI": "#2E6BE6", "SaaS & DevTools": "#E4703F",
                 "Cloud Infra": "#2A9D8F", "Hardware & Edge": "#8E6CBF"}
for s, color in sector_colors.items():
    sub = b[b.Sector == s]
    ax.scatter(sub.Annual_Revenue_M, sub.RD_int, s=sub.Employees_K * 3.2 + 12, color=color,
               alpha=0.55, edgecolor="white", linewidth=0.5, label=s, zorder=3)
ax.set_xlabel("年营收（百万美元）", fontsize=10)
ax.set_ylabel("研发强度（研发支出 / 营收，%）", fontsize=10)
ax.legend(frameon=False, fontsize=8.4, loc="upper right", title="行业", title_fontsize=8.4)
ax.set_title("同一编码框架复用于企业 SaaS 经营数据（n = 300）", fontsize=11.3, color=NAVY, pad=10)
save(fig, "fig11_biz.png")

print("ALL DONE ->", OUT)
