# -*- coding: utf-8 -*-
"""把 data/ecommerce_dashboard_data.csv 编译成 dashboard/data.js（供 index.html 直接加载）。

为什么需要这一步：index.html 只加载 `data.js`（`window.DATA=[...]` 的静态快照），
并不会去读 CSV。改了种子或换了数据文件后，必须重跑本脚本，页面才会变；
另外浏览器会缓存 data.js，刷新时请用 Ctrl+F5（或在 DevTools 里禁用缓存）。

只用标准库，不需要装 numpy/pandas，坏环境里也能跑。

用法：
    python scripts/build_data_js.py            # 从 ../data 读 CSV，写 ../dashboard/data.js
    python scripts/build_data_js.py --check    # 只比对不写盘：退出码 0 表示 data.js 已是最新
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "..", "data", "ecommerce_dashboard_data.csv")
JS_PATH = os.path.join(HERE, "..", "dashboard", "data.js")

NUMERIC = ("Ad_Spend", "GMV", "Conversion_Rate", "Bounce_Rate")


def load_rows(path):
    import csv

    with io.open(path, "r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        rows = []
        for raw in reader:
            row = {}
            for key in ("Date", "Category", "Channel"):
                row[key] = raw[key]
            for key in NUMERIC:
                row[key] = float(raw[key])
            rows.append(row)
    return rows


def js_num(x):
    """按 JS 的写法输出数字：整数值不带小数点（与 JSON.stringify 一致）。"""
    x = float(x)
    if x.is_integer():
        return str(int(x))
    return repr(x)


def render(rows):
    items = []
    for r in rows:
        items.append(
            '{"Date":%s,"Category":%s,"Channel":%s,"Ad_Spend":%s,"GMV":%s,'
            '"Conversion_Rate":%s,"Bounce_Rate":%s}'
            % (
                json.dumps(r["Date"], ensure_ascii=False),
                json.dumps(r["Category"], ensure_ascii=False),
                json.dumps(r["Channel"], ensure_ascii=False),
                js_num(r["Ad_Spend"]),
                js_num(r["GMV"]),
                js_num(r["Conversion_Rate"]),
                js_num(r["Bounce_Rate"]),
            )
        )
    return "window.DATA=[%s];" % ",".join(items)


def main(argv):
    if not os.path.exists(CSV_PATH):
        print("[FAIL] 找不到数据文件：%s" % os.path.normpath(CSV_PATH))
        return 1

    rows = load_rows(CSV_PATH)
    expected = render(rows)
    current = None
    if os.path.exists(JS_PATH):
        with io.open(JS_PATH, "r", encoding="utf-8") as fp:
            current = fp.read()

    g = sum(r["GMV"] for r in rows)
    a = sum(r["Ad_Spend"] for r in rows)
    print("CSV : %s" % os.path.normpath(CSV_PATH))
    print("      %d 行，GMV 合计 %.2f（%.2f 万），花费合计 %.2f（%.2f 万），ROAS %.4f"
          % (len(rows), g, g / 1e4, a, a / 1e4, g / a if a else 0))

    if "--check" in argv:
        if current is None:
            print("[FAIL] data.js 不存在")
            return 1
        if current == expected:
            print("[ OK ] data.js 已是最新，与 CSV 一致")
            return 0
        print("[FAIL] data.js 与 CSV 不一致，请运行：python scripts/build_data_js.py")
        return 1

    with io.open(JS_PATH, "w", encoding="utf-8", newline="\n") as fp:
        fp.write(expected)
    print("      -> 已写入 %s（%d 字节）" % (os.path.normpath(JS_PATH), len(expected.encode("utf-8"))))
    print("")
    print("下一步：刷新页面用 Ctrl+F5（浏览器会缓存 data.js，普通刷新可能仍是旧图）。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
