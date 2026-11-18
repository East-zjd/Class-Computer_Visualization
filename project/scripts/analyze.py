import pandas as pd
import numpy as np
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
base = BASE
df = pd.read_csv(os.path.join(DATA, "ecommerce_dashboard_data.csv"), encoding="utf-8-sig")
out = {}

out["shape"] = list(df.shape)
out["cols"] = list(df.columns)
out["date_range"] = [df.Date.min(), df.Date.max()]
out["n_days"] = df.Date.nunique()
out["n_cat"] = df.Category.nunique()
out["n_ch"] = df.Channel.nunique()

g = df.GMV.sum()
a = df.Ad_Spend.sum()
out["total_gmv"] = round(g, 2)
out["total_spend"] = round(a, 2)
out["roas"] = round(g / a, 4)
out["avg_cvr"] = round(df.Conversion_Rate.mean() * 100, 2)
out["avg_bounce"] = round(df.Bounce_Rate.mean() * 100, 2)

cat = df.groupby("Category").agg(
    GMV=("GMV", "sum"), Spend=("Ad_Spend", "sum"),
    CVR=("Conversion_Rate", "mean"), Bounce=("Bounce_Rate", "mean"), n=("GMV", "size")
).reset_index()
cat["ROAS"] = cat.GMV / cat.Spend
cat["share"] = cat.GMV / g
cat = cat.sort_values("GMV", ascending=False)
out["category"] = [
    {"name": r.Category, "gmv": round(r.GMV, 2), "spend": round(r.Spend, 2), "roas": round(r.ROAS, 3),
     "cvr": round(r.CVR * 100, 2), "bounce": round(r.Bounce * 100, 2), "share": round(r.share * 100, 2), "n": int(r.n)}
    for r in cat.itertuples()
]

ch = df.groupby("Channel").agg(GMV=("GMV", "sum"), Spend=("Ad_Spend", "sum"),
                               CVR=("Conversion_Rate", "mean"), Bounce=("Bounce_Rate", "mean"), n=("GMV", "size")).reset_index()
ch["ROAS"] = ch.GMV / ch.Spend
ch = ch.sort_values("ROAS", ascending=False)
out["channel"] = [
    {"name": r.Channel, "gmv": round(r.GMV, 2), "spend": round(r.Spend, 2), "roas": round(r.ROAS, 3),
     "cvr": round(r.CVR * 100, 2), "bounce": round(r.Bounce * 100, 2), "share": round(r.GMV / g * 100, 2), "n": int(r.n)}
    for r in ch.itertuples()
]

daily = df.groupby("Date").agg(GMV=("GMV", "sum"), Spend=("Ad_Spend", "sum")).reset_index()
daily["ROAS"] = daily.GMV / daily.Spend
out["daily_first5"] = [{"date": r.Date, "gmv": round(r.GMV, 2), "spend": round(r.Spend, 2)} for r in daily.head(5).itertuples()]
out["daily_top"] = {"date": daily.loc[daily.GMV.idxmax(), "Date"], "gmv": round(daily.GMV.max(), 2)}
out["daily_low"] = {"date": daily.loc[daily.GMV.idxmin(), "Date"], "gmv": round(daily.GMV.min(), 2)}
out["daily_mean"] = round(daily.GMV.mean(), 2)
out["daily_std"] = round(daily.GMV.std(), 2)
out["daily_cv"] = round(daily.GMV.std() / daily.GMV.mean(), 4)
# weekday effect
daily["dow"] = pd.to_datetime(daily.Date).dt.dayofweek
out["weekday_gmv"] = {str(k): round(v, 2) for k, v in daily.groupby("dow").GMV.mean().items()}
# biggest day-over-day change
daily["chg"] = daily.GMV.pct_change()
worst = daily.loc[daily.chg.idxmin()]
out["worst_dod"] = {"date": worst.Date, "chg": round(worst.chg * 100, 2), "gmv": round(worst.GMV, 2)}

# 3C days above category mean
d3c = df[df.Category == "3C数码"].groupby("Date").GMV.sum()
out["3c_days_above_mean"] = int((d3c > d3c.mean()).sum())
out["3c_days_total"] = int(d3c.size)
out["3c_max_day"] = {"date": d3c.idxmax(), "gmv": round(d3c.max(), 2)}
# top2 share
out["top2_share"] = round(cat.share.head(2).sum() * 100, 2)
# category x channel
pairs = df.groupby(["Category", "Channel"]).agg(GMV=("GMV", "sum"), Spend=("Ad_Spend", "sum")).reset_index()
pairs["ROAS"] = pairs.GMV / pairs.Spend
pairs = pairs.sort_values("GMV", ascending=False)
out["pairs_top5"] = [{"name": r.Category + " / " + r.Channel, "gmv": round(r.GMV, 2), "spend": round(r.Spend, 2), "roas": round(r.ROAS, 3)} for r in pairs.head(5).itertuples()]
out["pairs_bottom3"] = [{"name": r.Category + " / " + r.Channel, "gmv": round(r.GMV, 2), "spend": round(r.Spend, 2), "roas": round(r.ROAS, 3)} for r in pairs.tail(3).itertuples()]

# correlations
out["corr_cvr_bounce"] = round(df.Conversion_Rate.corr(df.Bounce_Rate), 4)
out["corr_spend_gmv"] = round(df.Ad_Spend.corr(df.GMV), 4)
out["roas_ratio_best_worst_category"] = round(cat.ROAS.max() / cat.ROAS.min(), 3)
out["channel_roas_range"] = round(ch.ROAS.max() - ch.ROAS.min(), 4)

# spend weights
out["spend_share_by_category"] = {r.Category: round(r.Spend / a * 100, 2) for r in cat.itertuples()}
# cvr distribution ranges
out["cvr_range_by_cat"] = {c: [round(df[df.Category == c].Conversion_Rate.min() * 100, 2), round(df[df.Category == c].Conversion_Rate.max() * 100, 2)] for c in df.Category.unique()}

# task7 business data
b = pd.read_csv(os.path.join(DATA, "visualization_business_data.csv"))
out["biz_shape"] = list(b.shape)
out["biz_cols"] = list(b.columns)
out["biz_n_sector"] = b.Sector.nunique()
out["biz_n_region"] = b.Region.nunique()
out["biz_total_rev"] = round(b.Annual_Revenue_M.sum(), 2)
sec = b.groupby("Sector").agg(Rev=("Annual_Revenue_M", "sum"), Growth=("Growth_Rate_pct", "mean"),
                              RD=("R_and_D_Spend_M", "sum"), Profit=("Profit_M", "sum"), Funding=("Funding_M", "sum"), n=("Company_ID", "size")).reset_index()
sec["RD_intensity"] = sec.RD / sec.Rev * 100
sec["margin"] = sec.Profit / sec.Rev * 100
sec = sec.sort_values("Rev", ascending=False)
out["biz_sector_top"] = [{"sector": r.Sector, "rev": round(r.Rev, 2), "growth": round(r.Growth, 2), "rd_int": round(r.RD_intensity, 2), "margin": round(r.margin, 2), "n": int(r.n)} for r in sec.head(6).itertuples()]
reg = b.groupby("Region").agg(Rev=("Annual_Revenue_M", "sum"), Growth=("Growth_Rate_pct", "mean")).reset_index().sort_values("Rev", ascending=False)
out["biz_region"] = [{"region": r.Region, "rev": round(r.Rev, 2), "growth": round(r.Growth, 2)} for r in reg.itertuples()]
out["biz_corr_funding_rev"] = round(b.Funding_M.corr(b.Annual_Revenue_M), 4)
out["biz_corr_rd_rev"] = round(b.R_and_D_Spend_M.corr(b.Annual_Revenue_M), 4)
out["biz_corr_growth_profit"] = round(b.Growth_Rate_pct.corr(b.Profit_M), 4)
out["biz_emp_total"] = round(b.Employees_K.sum(), 2)

# task3 study data
try:
    s = pd.read_csv(os.path.join(DATA, "study_performance_adv.csv"))
    out["study"] = {"shape": list(s.shape), "cols": list(s.columns),
                    "corr": round(s["study_hours"].corr(s["score"]), 4) if "study_hours" in s else None}
    out["study_preview"] = s.head(3).to_dict("records")
except Exception as e:
    out["study_err"] = str(e)

# task2 data
try:
    c2 = pd.read_csv(os.path.join(DATA, "course_metrics.csv"))
    out["task2"] = {"shape": list(c2.shape), "cols": list(c2.columns), "mean_score": round(c2.score.mean(), 2), "n": int(len(c2))}
except Exception as e:
    out["task2_err"] = str(e)

with open(os.path.join(BASE, "analysis_stats.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(json.dumps(out, ensure_ascii=False, indent=2)[:6000])
