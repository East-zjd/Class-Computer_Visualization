#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_env.py —— 解释器体检 + 标准库完整性基线

用途
  1) 一条命令确认当前解释器能否跑通本项目（numpy / pandas / matplotlib 是否齐全）；
  2) 发现标准库被外来代码覆盖这类事故（2026-09-12 本机 json 包被一段大模型评测脚本覆盖）；
  3) 给标准库打一份哈希基线，之后 `--verify` 秒级查出任何改动。

用法
  python scripts/check_env.py               # 体检
  python scripts/check_env.py --snapshot    # 体检通过后，为当前解释器记录基线
  python scripts/check_env.py --verify      # 体检并与基线比对
  python scripts/check_env.py --snapshot --baseline D:\base.json

退出码：0 = 无 FAIL；1 = 存在 FAIL。
"""

import os
import re
import sys

try:  # 让中文在管道/重定向下也不乱码
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OK, WARN, FAIL = "PASS", "WARN", "FAIL"
RECORDS = []


def report(level, title, detail=""):
    RECORDS.append((level, title))
    tag = {OK: "[ OK ]", WARN: "[WARN]", FAIL: "[FAIL]"}[level]
    print(tag, title)
    if detail:
        for line in str(detail).splitlines():
            print("       " + line)


def head(title):
    print()
    print("=" * 64)
    print(title)
    print("=" * 64)


def stdlib_dir():
    import sysconfig
    return sysconfig.get_paths()["stdlib"]


# ---------------------------------------------------------------- 解释器信息
def interpreter_info():
    head("1. 解释器")
    ver = "%d.%d.%d" % sys.version_info[:3]
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    report(OK, "版本   %s  (%s)" % (ver, "64 位" if sys.maxsize > 2**32 else "32 位"))
    report(OK, "可执行 %s" % sys.executable)
    report(OK, "标准库 %s" % stdlib_dir())
    if in_venv:
        report(OK, "运行于虚拟环境 %s（基座 %s）" % (sys.prefix, sys.base_prefix))
    else:
        report(OK, "运行于全局解释器（未激活 venv）")


# ---------------------------------------------------------------- 核心模块
CORE_MODULES = [
    "json", "os", "sys", "re", "io", "typing", "collections", "functools",
    "itertools", "datetime", "decimal", "fractions", "statistics", "random",
    "math", "hashlib", "hmac", "base64", "struct", "socket", "ssl",
    "threading", "queue", "concurrent.futures", "subprocess", "tempfile",
    "shutil", "glob", "fnmatch", "logging", "csv", "argparse", "configparser",
    "sqlite3", "zipfile", "tarfile", "gzip", "pickle", "copy", "enum",
    "dataclasses", "unittest", "inspect", "importlib", "pkgutil", "platform",
    "time", "uuid", "secrets", "textwrap", "pprint", "traceback",
    "urllib.parse", "http.client", "email.parser", "html.parser",
    "xml.etree.ElementTree", "ctypes", "pathlib", "gettext", "warnings",
]


def check_core_modules():
    head("2. 核心标准库（%d 个）" % len(CORE_MODULES))
    broken = []
    for name in CORE_MODULES:
        try:
            __import__(name)
        except Exception as exc:  # noqa: BLE001
            broken.append((name, "%s: %s" % (type(exc).__name__, exc)))
    if not broken:
        report(OK, "全部 %d 个模块可正常导入" % len(CORE_MODULES))
        return
    report(FAIL, "%d 个模块导入失败" % len(broken))
    for name, err in broken:
        report(FAIL, "  import %s" % name, err)


# ---------------------------------------------------------------- json 专项
def check_json_package():
    head("3. json 包专项（本机曾在此处出事故）")
    root = os.path.join(stdlib_dir(), "json")
    init = os.path.join(root, "__init__.py")
    if not os.path.isfile(init):
        report(FAIL, "找不到 json/__init__.py：%s" % init)
        return
    size = os.path.getsize(init)
    try:
        with open(init, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        report(FAIL, "无法读取 %s（%s）" % (init, exc))
        return
    problems = []
    if size < 8000:
        problems.append("文件仅 %d 字节，正常的 CPython 3.12 该文件约 14 KB" % size)
    if "def dumps" not in text or "def loads" not in text:
        problems.append("未找到 dumps/loads 定义，内容不像 json 包本体")
    suspicious = re.findall(
        r"(from\s+transformers|import\s+torch|from\s+datasets|load_dataset\s*\(|/mnt/)",
        text,
    )
    if suspicious:
        problems.append("发现外来代码特征：%s" % ", ".join(sorted(set(suspicious))))
    if problems:
        report(FAIL, "json/__init__.py 已被污染（%s）" % init)
        for p in problems:
            report(FAIL, "  · " + p)
        return
    report(OK, "json/__init__.py 正常（%d 字节）" % size)
    try:
        import json  # noqa: F401
        for attr in ("dumps", "loads", "dump", "load", "JSONEncoder"):
            if not hasattr(json, attr):
                report(FAIL, "json 缺少属性 %s" % attr)
                return
        report(OK, "json.dumps / loads / dump / load / JSONEncoder 均可用")
    except Exception as exc:  # noqa: BLE001
        report(FAIL, "import json 失败", "%s: %s" % (type(exc).__name__, exc))


# ---------------------------------------------------------------- 全库扫描
SKIP_DIRS = {"site-packages", "__pycache__", "test", "tests", "idle_test",
             "lib2to3", "ensurepip", "pydoc_data"}

# 标准库里合法的"试探性 / 平台可选"导入，不能算污染
BENIGN_IMPORTS = frozenset({
    "test", "implementation", "system", "java", "vms_lib", "sitecustomize",
    "usercustomize", "win32evtlogutil", "win32evtlog", "macostools",
    "foo", "bar", "baz", "spam", "eggs", "idna", "distutils", "setuptools",
})
IMPORT_RE = re.compile(
    r"^[ \t]*(?:from[ \t]+([\w.]+)[ \t]+import|import[ \t]+([\w.]+))", re.M
)
TOKEN_RE = re.compile(r"(/mnt/|/home/[a-z_]+/|load_dataset\s*\(|from transformers)")


def scan_stdlib():
    head("4. 标准库全量扫描（排除 site-packages / 测试目录）")
    root = stdlib_dir()
    known = getattr(sys, "stdlib_module_names", None)
    if not known:
        report(WARN, "当前解释器无 sys.stdlib_module_names（需 3.10+），跳过第三方 import 检查")
        known = frozenset()
    suspicious_imports = []
    suspicious_tokens = []
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root)
            total += 1
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            for hit in TOKEN_RE.findall(text):
                suspicious_tokens.append((rel, hit))
            if not known:
                continue
            for m in IMPORT_RE.finditer(text):
                top = (m.group(1) or m.group(2)).split(".")[0]
                if (not top or top.startswith("_") or top in known
                        or top in BENIGN_IMPORTS):
                    continue
                # 同目录的兄弟模块 / 子包，属于合法的包内引用
                if (os.path.exists(os.path.join(dirpath, top + ".py"))
                        or os.path.isdir(os.path.join(dirpath, top))
                        or os.path.exists(os.path.join(root, top))):
                    continue
                suspicious_imports.append((rel, top))
    report(OK, "扫描 %d 个 .py 文件" % total)
    if suspicious_tokens:
        report(FAIL, "%d 处外来代码特征（疑似路径写错导致覆盖）" % len(suspicious_tokens))
        for rel, hit in suspicious_tokens[:10]:
            report(FAIL, "  %s  ←  %s" % (rel, hit.strip()))
    else:
        report(OK, "未发现 /mnt、load_dataset、transformers 等外来特征")
    if suspicious_imports:
        uniq = sorted(set(suspicious_imports))[:20]
        report(WARN, "%d 处标准库文件引用了非标准库模块（需人工确认）" % len(uniq))
        for rel, top in uniq:
            report(WARN, "  %s  ←  import %s" % (rel, top))
    elif known:
        report(OK, "标准库文件未引用第三方顶层模块")


# ---------------------------------------------------------------- 依赖
def check_packages():
    head("5. 项目依赖")
    need = {"numpy": "numpy", "pandas": "pandas", "matplotlib": "matplotlib"}
    missing = []
    for mod, pip_name in need.items():
        try:
            m = __import__(mod)
            report(OK, "%-10s %s" % (mod, getattr(m, "__version__", "?")))
        except Exception as exc:  # noqa: BLE001
            missing.append(pip_name)
            report(WARN, "%-10s 未安装（%s）" % (mod, type(exc).__name__))
    if missing:
        report(WARN, "补齐命令：python -m pip install %s -i https://pypi.tuna.tsinghua.edu.cn/simple"
               % " ".join(missing))
    return not missing


# ---------------------------------------------------------------- 项目文件
def check_project_files(script_dir):
    head("6. 项目文件")
    proj = os.path.abspath(os.path.join(script_dir, os.pardir))
    for rel in ("scripts/data_generate.py", "scripts/analyze.py", "scripts/figs.py",
                "data/ecommerce_dashboard_data.csv", "dashboard/index.html"):
        path = os.path.join(proj, rel.replace("/", os.sep))
        if os.path.exists(path):
            report(OK, "存在 %s (%d B)" % (rel, os.path.getsize(path)))
        else:
            report(WARN, "缺失 %s" % rel)
    csv_path = os.path.join(proj, "data", "ecommerce_dashboard_data.csv")
    if os.path.isfile(csv_path):
        with open(csv_path, "r", encoding="utf-8", errors="replace") as fh:
            rows = sum(1 for _ in fh) - 1
        report(OK if rows == 540 else WARN, "数据行数 %d（期望 540）" % rows)


# ---------------------------------------------------------------- 基线
def default_baseline():
    tag = "cp%d%d" % (sys.version_info[0], sys.version_info[1])
    return os.path.join(os.path.expanduser("~"), ".stdlib-baseline-%s.json" % tag)


def collect_hashes(root):
    import hashlib
    result = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, "rb") as fh:
                    data = fh.read()
            except OSError:
                continue
            result[os.path.relpath(path, root)] = [len(data), hashlib.sha256(data).hexdigest()]
    return result


def do_snapshot(path):
    head("记录标准库基线")
    if any(level == FAIL for level, _ in RECORDS):
        report(FAIL, "体检未通过，拒绝记录基线（先修好再打基线）")
        return
    import json
    hashes = collect_hashes(stdlib_dir())
    payload = {
        "created": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "python": "%d.%d.%d" % sys.version_info[:3],
        "executable": sys.executable,
        "stdlib": stdlib_dir(),
        "files": hashes,
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=0, sort_keys=True)
    report(OK, "已记录 %d 个文件 → %s" % (len(hashes), path))


def do_verify(path):
    head("与基线比对")
    if not os.path.isfile(path):
        report(WARN, "基线不存在，先执行 --snapshot：%s" % path)
        return
    import json
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    old = payload.get("files", {})
    new = collect_hashes(stdlib_dir())
    changed = [k for k in new if k in old and new[k][1] != old[k][1]]
    added = [k for k in new if k not in old]
    removed = [k for k in old if k not in new]
    report(OK, "基线时间 %s（Python %s，%d 个文件）"
           % (payload.get("created", "?"), payload.get("python", "?"), len(old)))
    if not (changed or added or removed):
        report(OK, "标准库与基线完全一致")
        return
    if changed:
        report(FAIL, "%d 个文件内容被改动" % len(changed))
        for k in sorted(changed)[:20]:
            report(FAIL, "  %s  %d B → %d B" % (k, old[k][0], new[k][0]))
    if added:
        report(WARN, "%d 个新增文件" % len(added))
        for k in sorted(added)[:10]:
            report(WARN, "  + " + k)
    if removed:
        report(WARN, "%d 个文件消失" % len(removed))
        for k in sorted(removed)[:10]:
            report(WARN, "  - " + k)


# ---------------------------------------------------------------- main
def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="解释器体检与标准库完整性基线")
    ap.add_argument("--snapshot", action="store_true", help="体检通过后记录基线")
    ap.add_argument("--verify", action="store_true", help="与既有基线比对")
    ap.add_argument("--baseline", default=None, help="基线文件路径")
    args = ap.parse_args(argv)
    base = args.baseline or default_baseline()

    interpreter_info()
    check_core_modules()
    check_json_package()
    scan_stdlib()
    check_packages()
    check_project_files(os.path.dirname(os.path.abspath(__file__)))

    if args.snapshot:
        do_snapshot(base)
    if args.verify:
        do_verify(base)

    head("小结")
    n_fail = sum(1 for level, _ in RECORDS if level == FAIL)
    n_warn = sum(1 for level, _ in RECORDS if level == WARN)
    n_ok = sum(1 for level, _ in RECORDS if level == OK)
    print("PASS %d   WARN %d   FAIL %d" % (n_ok, n_warn, n_fail))
    if base and (args.snapshot or args.verify):
        print("基线：%s" % base)
    if n_fail:
        print("结论：解释器异常，先修解释器再跑项目脚本。")
    else:
        print("结论：可以运行 scripts/data_generate.py / analyze.py / figs.py。")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
