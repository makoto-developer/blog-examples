"""勾配は関数評価の何回分か（第6節）と、reverse の代償＝テープの大きさ（第7節）。"""

import time

from ad import (Tape, Var, forward_grad, make_bench_fn, r_sin, r_tanh,
                reverse_grad)


def timeit(fn, repeat=5):
    best = float("inf")
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - t0)
    return best * 1000.0


# ------------------------------------- 第6節: 勾配は関数評価の何回分か

def section6():
    print("## 6. 勾配は関数評価の何回分か（m=1）")
    print()
    print("| n | f(x) [ms] | reverse [ms] | 倍率 | forward [ms] | 倍率 |")
    print("|---:|---:|---:|---:|---:|---:|")
    for n in [10, 50, 100, 500, 1000]:
        f = make_bench_fn(n, 1)
        xs = [0.1 + 0.001 * i for i in range(n)]

        # 素の関数評価（微分なし）: float のまま同じ演算をたどる
        import math

        def plain():
            acc = xs[0]
            for j in range(1, n):
                acc = acc + xs[j] * (1.0 + 0.01 * j)
            for _ in range(20):
                acc = math.tanh(acc * 0.5) + math.sin(acc) * 0.25
            return acc

        tp = timeit(plain, 7)
        tr = timeit(lambda: reverse_grad(f, xs), 3)
        tf = timeit(lambda: forward_grad(f, xs), 3)
        print(f"| {n} | {tp:.3f} | {tr:.3f} | {tr / tp:.1f}x | {tf:.1f} | {tf / tp:,.0f}x |")
    print()


# ------------------------------------- 第7節: reverse の代償（テープ）

def section7():
    print("## 7. reverse の代償：テープのノード数")
    print()
    print("| 連鎖の深さ | テープのノード数 |")
    print("|---:|---:|")
    for depth in [10, 100, 1000]:
        f = make_bench_fn(1, 1, depth=depth)
        _, tape = reverse_grad(f, [0.3], return_tape=True)
        print(f"| {depth:,} | {len(tape.nodes):,} |")
    print()


if __name__ == "__main__":
    section6()
    section7()
