#!/usr/bin/env python3
"""results/*.txt から、記事の表（中央値と、10回の最小〜最大）を作る。

使い方: python3 analyze.py <Chunk|Cliff|File|OpenClose> [key=value ...]
例:     python3 analyze.py Chunk chunk=4KB
差の有無の検定は benchstat に任せる（README 参照）。
"""
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

# サブベンチ名の無い BenchmarkOpenClose-4 も読めるよう、"/..." を省略可能にしている。
LINE = re.compile(r"^Benchmark(\w+?)(?:/(\S+?))?-\d+\s+\d+\s+([\d.]+) ns/op.*?(?:\s([\d.]+) B/op\s+(\d+) allocs/op)?$")


def load(bench):
    rows = defaultdict(lambda: defaultdict(list))
    for f in sorted(Path(__file__).parent.glob(f"results/*-{bench}.txt")):
        version = None
        for line in f.read_text().splitlines():
            if line.startswith("env: "):
                version = line.split()[1]
            m = LINE.match(line)
            if not m:
                continue
            name, ns, bop, allocs = m.group(2), float(m.group(3)), m.group(4), m.group(5)
            keys = dict(kv.split("=", 1) for kv in name.split("/")) if name else {"case": m.group(1)}
            rows[(version, tuple(sorted(keys.items())))]["ns"].append(ns)
            if bop is not None:
                rows[(version, tuple(sorted(keys.items())))]["B"].append(float(bop))
                rows[(version, tuple(sorted(keys.items())))]["allocs"].append(float(allocs))
    return rows


def fmt_ns(v):
    return f"{v:,.0f}" if v >= 1000 else f"{v:.1f}"


def main():
    bench, filters = sys.argv[1], dict(a.split("=", 1) for a in sys.argv[2:])
    rows = load(bench)
    print("| toolchain | " + " | ".join(filters) + " | case | ns/op 中央値 | 最小〜最大 | B/op | allocs/op |")
    print("|---|" + "---|" * len(filters) + "---|---:|---:|---:|---:|")
    for (version, keys), m in sorted(rows.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        k = dict(keys)
        if any(k.get(fk) != fv for fk, fv in filters.items()):
            continue
        case = "/".join(f"{a}={b}" for a, b in keys if a not in filters)
        ns = m["ns"]
        b = f"{statistics.median(m['B']):,.0f}" if m["B"] else "-"
        al = f"{statistics.median(m['allocs']):.0f}" if m["allocs"] else "-"
        print(f"| {version} | " + " | ".join(filters.values()) +
              f" | {case} | {fmt_ns(statistics.median(ns))} | {fmt_ns(min(ns))}〜{fmt_ns(max(ns))} | {b} | {al} |")


if __name__ == "__main__":
    main()
