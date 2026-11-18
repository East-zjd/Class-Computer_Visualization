# -*- coding: utf-8 -*-
"""按规则生成模拟电商经营数据（可换种子，用于演示与换数据重算）。

用法：
    python data_generate.py                       预览：只打印规模与合计，不写盘
    python data_generate.py --force               用默认 seed=42 覆盖 ../data/ecommerce_dashboard_data.csv
    python data_generate.py --seed 7 --force      换一份新样本（0–2^31-1 任意整数）
    python data_generate.py --days 60 --force     改时间跨度（默认 30 天，起始 2026-09-01）
    python data_generate.py --out ../data/demo.csv --seed 7 --force   写到别的文件，不动主数据

生成规则（与论文 2.1 节一致）：6 品类 × 3 渠道 × N 天，品类设定不同的
投放规模、ROI、转化率与跳出率区间，再叠加日度噪声。数据全部合成，
不代表真实经营。

注意：换种子/换天数会得到一份**新的**样本，此后所有统计、插图、data.js
与论文里的数字都必须按新样本重算（见 scripts/resync.ps1），否则图与文不一致。
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

CATEGORIES = ["3C数码", "户外运动", "智能家居", "美妆个护", "数码配件", "运动服饰"]
CHANNELS = ["App端", "小程序", "网页端"]

# 每个品类的 (ROI 区间, 转化率区间, 跳出率区间)；未列出的品类用 default
PROFILE = {
    "3C数码":   ((3.5, 5.2), (0.12, 0.22), (0.25, 0.40)),
    "美妆个护": ((2.8, 4.5), (0.18, 0.28), (0.20, 0.35)),
    "智能家居": ((2.0, 3.8), (0.06, 0.14), (0.40, 0.55)),
}
DEFAULT_PROFILE = ((1.8, 3.2), (0.05, 0.12), (0.45, 0.65))


def generate(seed=42, days=30, start="2026-09-01"):
    """返回按规则生成的 DataFrame（纯函数，便于测试与换参重算）。"""
    rng = np.random.RandomState(seed)
    dates = pd.date_range(start=start, periods=days, freq="D")
    records = []
    for d in dates:
        for cat in CATEGORIES:
            roi_rng, cvr_rng, bounce_rng = PROFILE.get(cat, DEFAULT_PROFILE)
            for ch in CHANNELS:
                base_spend = rng.uniform(2000, 15000)
                roi = rng.uniform(*roi_rng)
                cvr = rng.uniform(*cvr_rng)
                bounce = rng.uniform(*bounce_rng)
                records.append({
                    "Date": d.strftime("%Y-%m-%d"), "Category": cat, "Channel": ch,
                    "Ad_Spend": round(base_spend, 2), "GMV": round(base_spend * roi, 2),
                    "Conversion_Rate": round(cvr, 4), "Bounce_Rate": round(bounce, 4),
                })
    return pd.DataFrame(records)


def main(argv=None):
    ap = argparse.ArgumentParser(description="生成模拟电商经营数据（默认只预览，不写盘）")
    ap.add_argument("--seed", type=int, default=42, help="随机种子，默认 42；换值即换一份新样本")
    ap.add_argument("--days", type=int, default=30, help="天数，默认 30")
    ap.add_argument("--start", default="2026-09-01", help="起始日期，默认 2026-09-01")
    ap.add_argument("--out", default=None, help="输出路径，默认 ../data/ecommerce_dashboard_data.csv")
    ap.add_argument("--force", action="store_true", help="确认覆盖已存在的目标文件")
    args = ap.parse_args(argv)

    df = generate(args.seed, args.days, args.start)
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    out_path = os.path.abspath(args.out) if args.out else os.path.join(out_dir, "ecommerce_dashboard_data.csv")

    gmv_total = float(df["GMV"].sum())
    spend_total = float(df["Ad_Spend"].sum())
    print("seed: %d   rows: %d   日期: %s ~ %s  品类: %d  渠道: %d"
          % (args.seed, len(df), df["Date"].min(), df["Date"].max(),
             df["Category"].nunique(), df["Channel"].nunique()))
    print("GMV 合计: %.2f（%.2f 万）  花费合计: %.2f（%.2f 万）  ROAS: %.4f"
          % (gmv_total, gmv_total / 1e4, spend_total, spend_total / 1e4, gmv_total / spend_total))

    if os.path.exists(out_path) and not args.force:
        print("\n[未写入] %s 已存在。" % out_path)
        print("         当前项目的数据是论文正文引用的那一份；直接覆盖会让图、data.js 与论文数字脱节。")
        print("         确认要换数据，请加 --force，然后必跑：scripts/resync.ps1")
        print("         （它会重算 analysis_stats.json、重绘插图、重建 data.js，并打印需要改的论文数字。）")
        return 0

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("\n已写入:", out_path)
    print("下一步：powershell -ExecutionPolicy Bypass -File scripts\\resync.ps1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
