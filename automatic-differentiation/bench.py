"""正しさの確認（第4節）と、n×m のベンチ（第5節）。"""

import math
import time

from ad import (Dual, d_exp, d_sin, forward_grad, make_bench_fn, r_exp, r_sin,
                reverse_grad)


def timeit(fn, repeat=5):
    """3〜5回まわして最小値を取る。ms で返す。"""
    best = float("inf")
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - t0)
    return best * 1000.0


# ---------------------------------------------- 第4節: 正しさの確認

def section4():
    x0, y0 = 0.7, 1.3

    def f_dual(vs):
        x, y = vs
        return [d_sin(x * y) + d_exp(x) / (y + 2.0)]

    def f_var(vs):
        x, y = vs
        return [r_sin(x * y) + r_exp(x) / (y + 2.0)]

    # 解析解
    gx = y0 * math.cos(x0 * y0) + math.exp(x0) / (y0 + 2.0)
    gy = x0 * math.cos(x0 * y0) - math.exp(x0) / (y0 + 2.0) ** 2

    Jf = forward_grad(f_dual, [x0, y0])[0]
    Jr = reverse_grad(f_var, [x0, y0])[0]

    h = 1e-5

    def f_plain(x, y):
        return math.sin(x * y) + math.exp(x) / (y + 2.0)

    nx = (f_plain(x0 + h, y0) - f_plain(x0 - h, y0)) / (2 * h)
    ny = (f_plain(x0, y0 + h) - f_plain(x0, y0 - h)) / (2 * h)

    print("## 4. 正しさの確認")
    print()
    print("| 手法 | ∂f/∂x の誤差 | ∂f/∂y の誤差 |")
    print("|---|---|---|")
    for name, (a, b) in [("forward", Jf), ("reverse", Jr), ("中心差分 (h=1e-5)", (nx, ny))]:
        print(f"| {name} | {abs(a - gx):.3g} | {abs(b - gy):.3g} |")
    print()

    print("| 次元 | 両モードの最大差 |")
    print("|---|---|")
    for n, m in [(3, 4), (5, 5), (7, 2)]:
        f = make_bench_fn(n, m)
        xs = [0.1 + 0.03 * i for i in range(n)]
        A = forward_grad(f, xs)
        B = reverse_grad(f, xs)
        diff = max(abs(A[k][j] - B[k][j]) for k in range(m) for j in range(n))
        print(f"| n={n}, m={m} | {diff:.2g} |")
    print()


# ---------------------------------------------- 第5節: どこで逆転するか

def section5():
    print("## 5. どこで逆転するか")
    print()
    print("| n | m | forward [ms] | reverse [ms] | 比 | 速い方 |")
    print("|---:|---:|---:|---:|---:|---|")
    for n, m in [(1, 100), (2, 50), (5, 20), (10, 10), (20, 5), (50, 2), (100, 1), (500, 1)]:
        f = make_bench_fn(n, m)
        xs = [0.1 + 0.001 * i for i in range(n)]
        tf = timeit(lambda: forward_grad(f, xs), 3)
        tr = timeit(lambda: reverse_grad(f, xs), 3)
        print(f"| {n} | {m} | {tf:.2f} | {tr:.2f} | {tf / tr:.2f} | "
              f"{'reverse' if tr < tf else 'forward'} |")
    print()

    print("| n=m | forward [ms] | reverse [ms] | 比 |")
    print("|---:|---:|---:|---:|")
    for k in range(1, 7):
        f = make_bench_fn(k, k)
        xs = [0.1 + 0.001 * i for i in range(k)]
        tf = timeit(lambda: forward_grad(f, xs))
        tr = timeit(lambda: reverse_grad(f, xs))
        print(f"| {k} | {tf:.3f} | {tr:.3f} | {tf / tr:.2f} |")
    print()


if __name__ == "__main__":
    section4()
    section5()
