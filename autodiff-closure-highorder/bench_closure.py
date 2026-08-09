"""テープ方式とクロージャ方式を比べ、高階微分の値段を測る。

    python3 bench_closure.py

前の記事の実装（../automatic-differentiation/ad.py）を読むので、
リポジトリを丸ごと clone した状態で実行する。
"""

import math
import os
import sys
import time
import tracemalloc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "automatic-differentiation"))

from ad import (Dual, d_sin, d_tanh, forward_grad, reverse_grad,  # noqa: E402
                r_sin, r_tanh)
from adc import (CVar, c_sin, c_tanh, closure_grad, j_exp, j_sin,  # noqa: E402
                 nth, seed)


def timeit(fn, repeat=5):
    best = float("inf")
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - t0)
    return best * 1000.0


def chain(vs, sin, tanh, n, depth=20):
    """前の記事と同じ形。n 入力・スカラー出力・深さ depth の非線形連鎖。"""
    acc = vs[0] * 1.0
    for j in range(1, n):
        acc = acc + vs[j] * (1.0 + 0.01 * j)
    for _ in range(depth):
        acc = tanh(acc * 0.5) + sin(acc) * 0.25
    return acc


def f_tape(vs):
    return [chain(vs, r_sin, r_tanh, len(vs))]


def f_clos(vs):
    return chain(vs, c_sin, c_tanh, len(vs))


def f_dual(vs):
    return [chain(vs, d_sin, d_tanh, len(vs))]


# ------------------------------------------------------- 1. 一致の確認

def section_agree():
    print("## 1. 三つの実装は一致するか\n")
    print("| n | テープ方式との最大差（クロージャ） | 同（forward） |")
    print("|---:|---:|---:|")
    for n in [3, 10, 50]:
        xs = [0.1 + 0.01 * i for i in range(n)]
        gt = reverse_grad(f_tape, xs)[0]
        gc = closure_grad(f_clos, xs)
        gf = forward_grad(f_dual, xs)[0]
        dc = max(abs(a - b) for a, b in zip(gt, gc))
        df = max(abs(a - b) for a, b in zip(gt, gf))
        print(f"| {n} | {dc:.2g} | {df:.2g} |")
    print()


# ------------------------------------------------------- 2. 速度

def section_speed():
    print("## 2. テープとクロージャ、どちらが速いか\n")
    print("| n | テープ [ms] | クロージャ [ms] | 比 |")
    print("|---:|---:|---:|---:|")
    for n in [10, 50, 100, 500, 1000]:
        xs = [0.1 + 0.001 * i for i in range(n)]
        tt = timeit(lambda: reverse_grad(f_tape, xs), 3)
        tc = timeit(lambda: closure_grad(f_clos, xs), 3)
        print(f"| {n} | {tt:.3f} | {tc:.3f} | {tc / tt:.2f} |")
    print()


# ------------------------------------------------------- 3. メモリ

def section_memory():
    print("## 3. 記録の大きさ\n")
    print("| 連鎖の深さ | テープ [KB] | クロージャ [KB] | 比 |")
    print("|---:|---:|---:|---:|")
    for depth in [10, 100, 1000]:
        xs = [0.3]

        def ft(vs):
            return [chain(vs, r_sin, r_tanh, 1, depth)]

        def fc(vs):
            return chain(vs, c_sin, c_tanh, 1, depth)

        tracemalloc.start()
        reverse_grad(ft, xs)
        _, peak_t = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        tracemalloc.start()
        closure_grad(fc, xs)
        _, peak_c = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"| {depth:,} | {peak_t/1024:.1f} | {peak_c/1024:.1f} | {peak_c/peak_t:.2f} |")
    print()


# ------------------------------------------------------- 4. 高階微分

def section_highorder():
    x0 = 0.7
    s, c, e = math.sin(x0), math.cos(x0), math.exp(x0)
    exact = [s * e, e * (s + c), 2 * e * c, 2 * e * (c - s)]

    print("## 4. 入れ子の二重数で高階微分\n")
    print("`f(x) = sin(x)·exp(x)` を x=0.7 で微分する。\n")
    print("| 階数 | 入れ子の二重数 | 解析解 | 差 |")
    print("|---:|---:|---:|---:|")
    j = (lambda x: j_sin(x) * j_exp(x))(seed(x0, 3))
    for k in range(4):
        got = nth(j, k)
        print(f"| {k} | {got:.12f} | {exact[k]:.12f} | {abs(got - exact[k]):.1g} |")
    print()

    print("| 階数 | 時間 [ms] | 1階に対する倍率 |")
    print("|---:|---:|---:|")
    base = None
    for order in [1, 2, 3, 4, 5]:
        t = timeit(lambda: nth((lambda x: j_sin(x) * j_exp(x))(seed(x0, order)), order), 200)
        base = base or t
        print(f"| {order} | {t:.4f} | {t/base:.1f}x |")
    print()


if __name__ == "__main__":
    section_agree()
    section_speed()
    section_memory()
    section_highorder()
