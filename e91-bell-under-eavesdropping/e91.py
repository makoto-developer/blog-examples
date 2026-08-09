"""E91 を実装して、盗聴で Bell 不等式の破れがどう減るかを測る。

    python3 e91.py

記事「BB84 は何を根拠に安全なのか」の続き。
https://blog.makoto-developer.net/articles/bb84-eavesdropping-detection

外部ライブラリなし。乱数は seed 固定なので、記事の表と同じ数字が出る。

スピン1/2のシングレットで書く。角度 a, b で測ったときの相関は
    E(a,b) = -cos(a - b)
であり、同じ向きなら必ず逆（E=-1）になる。
"""

import math
import random

SEED = 20260810
N_PAIRS = 200_000

# E91 の測定角。Alice は 0, 45, 90 度、Bob は 45, 90, 135 度
A_ANGLES = [0.0, math.pi / 4, math.pi / 2]
B_ANGLES = [math.pi / 4, math.pi / 2, 3 * math.pi / 4]

# CHSH に使う組み合わせ: S = E(a1,b1) - E(a1,b3) + E(a3,b1) + E(a3,b3)
CHSH = [(0, 0, +1), (0, 2, -1), (2, 0, +1), (2, 2, +1)]

# 鍵に使う組み合わせ（角度が一致していて E=-1 になる対）
KEY_PAIRS = [(1, 0), (2, 1)]


def singlet(rng, a, b):
    """シングレットを角度 a, b で測る。E(a,b) = -cos(a-b)。"""
    x = 1 if rng.random() < 0.5 else -1
    e = -math.cos(a - b)
    y = x if rng.random() < (1 + e) / 2 else -x
    return x, y


def intercepted(rng, a, b):
    """Eve が両方の粒子を同じランダム軸で測り、測った積状態を作り直して送る。

    もつれは壊れ、Alice と Bob が受け取るのは相関のある「決まった状態」になる。
    """
    theta = rng.random() * math.pi
    ea = 1 if rng.random() < 0.5 else -1
    eb = -ea  # 同じ軸で測ればシングレットは必ず逆

    # 軸 theta に沿って値 e で用意された状態を角度 a で測る
    x = ea if rng.random() < (1 + math.cos(a - theta)) / 2 else -ea
    y = eb if rng.random() < (1 + math.cos(b - theta)) / 2 else -eb
    return x, y


def run(rng, n=N_PAIRS, eve_rate=0.0):
    """n ペア流して、CHSH の各相関と鍵の誤り率を返す。"""
    corr = {}  # (i, j) -> [一致した回数, 総数]
    key_err = key_tot = 0

    for _ in range(n):
        i = rng.randrange(3)
        j = rng.randrange(3)
        a, b = A_ANGLES[i], B_ANGLES[j]
        x, y = (intercepted if rng.random() < eve_rate else singlet)(rng, a, b)

        s = corr.setdefault((i, j), [0, 0])
        s[0] += x * y
        s[1] += 1

        if (i, j) in KEY_PAIRS:
            key_tot += 1
            # 角度が一致する対では必ず逆になるはず。同じなら誤り
            if x == y:
                key_err += 1

    def e(i, j):
        s = corr.get((i, j), [0, 1])
        return s[0] / s[1] if s[1] else 0.0

    s_val = sum(sign * e(i, j) for i, j, sign in CHSH)
    return abs(s_val), (key_err / key_tot if key_tot else 0.0)


def main():
    rng = random.Random(SEED)

    print("## 盗聴なしで Tsirelson 限界が出るか\n")
    s, q = run(rng)
    print(f"|S| = {s:.4f}（理論値 2√2 = {2 * math.sqrt(2):.4f}）")
    print(f"鍵の誤り率 = {q:.4f}\n")

    print("## 盗聴率を振る\n")
    print("| 盗聴率 | \\|S\\| | 古典限界 2 を超えるか | 鍵の誤り率 |")
    print("|---:|---:|---|---:|")
    for f in [0.00, 0.10, 0.25, 0.40, 0.50, 0.75, 1.00]:
        s, q = run(rng, eve_rate=f)
        print(f"| {f:.2f} | {s:.4f} | {'破れている' if s > 2 else '**破れない**'} | {q:.4f} |")
    print()

    crit = 2 - math.sqrt(2)
    print("## どこで古典限界を割るか\n")
    print(f"理論: |S(f)| = (1-f)·2√2 + f·√2 = 2√2 - √2·f、これが 2 になるのは f = 2-√2 = {crit:.4f}\n")
    print("| 盗聴率 | \\|S\\| | 理論 2√2-√2·f |")
    print("|---:|---:|---:|")
    for f in [0.52, 0.56, crit, 0.60, 0.64]:
        s, _ = run(rng, eve_rate=f)
        th = 2 * math.sqrt(2) - math.sqrt(2) * f
        mark = "**" if abs(f - crit) < 1e-9 else ""
        print(f"| {mark}{f:.4f}{mark} | {mark}{s:.4f}{mark} | {th:.4f} |")
    print()

    print("## BB84 と同じ量になっているか\n")
    print("| 盗聴率 | E91 の鍵の誤り率 | BB84 の QBER（前回） |")
    print("|---:|---:|---:|")
    for f in [0.10, 0.25, 0.50, 1.00]:
        _, q = run(rng, eve_rate=f)
        print(f"| {f:.2f} | {q:.4f} | {f / 4:.4f} |")


if __name__ == "__main__":
    main()
