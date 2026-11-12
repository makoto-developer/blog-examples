#!/usr/bin/env python3
"""Dias と Lima の note (arXiv:2611.00517v1) の数表を、式から再計算して note の値と突き合わせる。

読んだ版: note は arXiv v1 の PDF（SHA-256 の先頭 a0ee9531）、OpenAI の preprint は
github.com/openai/math のコミット 42907c9e の paper.pdf（同 5b1612dc、67 ページ）。
標準ライブラリだけで動く。乱数は seed 固定。1件でも食い違えば終了コード 1。
"""
import math
import random
import sys
import time
from fractions import Fraction
from itertools import product

LN2 = math.log(2)
LN10 = math.log(10)
failures = []


def check(label, got, published, source="note"):
    ok = got == published  # 表示する note の値と判定に使う値を同じにして、食い違ったまま通るのを防ぐ
    print(f"{'OK  ' if ok else 'NG  '}{label}: 再計算 {got}  /  {source} {published}")
    if not ok:
        failures.append(label)


# --- 1. 表1: 一般の上界 C·n·ln ln n/√(ln n) < n  ⇔  C·ln u < √u  (u = ln n) ---------

def last_root_general(c):
    """C·ln u = √u の最後の根。最小値の位置 u = 4C² より右にある。C=1 は根がない。"""
    f = lambda u: math.sqrt(u) - c * math.log(u)
    lo = 4.0 * c * c
    if f(lo) >= 0:
        return None
    hi = lo
    while f(hi) < 0:
        hi *= 2
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return hi


TABLE1_GENERAL = {2: 32.2, 3: 125.5, 5: 555.7, 10: 3517.4, 20: 20035.2, 50: 181955.6}
TABLE1_BOUNDED = {1: 0.4, 2: 1.7, 3: 3.9, 5: 10.9, 10: 43.4, 20: 173.7, 50: 1085.7}

print("== 表1（n > 10^x で 2^n を下回る。x を比べる）==")
check("一般 C=1（根なし。note は every n > e）", last_root_general(1), None)
for c, want in TABLE1_GENERAL.items():
    got = round(last_root_general(c) / LN10, 1)
    check(f"一般 C={c}", got, want)
for c, want in TABLE1_BOUNDED.items():
    got = round(c * c / LN10, 1)  # C·n/√(ln n) < n ⇔ ln n > C²
    check(f"密度有界 C={c}", got, want)


# --- 2. 命題4.1: 証明から取り出した定数 ------------------------------------------------

K0 = 2 * math.pi * math.sqrt(24 * 2**17) / LN2
ALL_LEVELS = 1 / (1 - 3 * math.sqrt(2) / 32)  # 段ごとに辺数が 3/32、u が 1/2 になる
DENSITY = 4.26
M0_PER_N = 12 * DENSITY - 6  # 各変数が3回以上現れる 3-CNF で M0 = 12m - 6n
S_PER_N = 1 + DENSITY  # 指数 (K0·M0 + s)/√λ の s（葉の費用）を n で割った値。s = n + m
coef = K0 * M0_PER_N + S_PER_N
coef_all = K0 * ALL_LEVELS * M0_PER_N + S_PER_N

print("\n== 命題4.1 と実験 E5 ==")
check("K0（根）", round(K0, 1), 16077.4)
check("K0（全段）", round(K0 * ALL_LEVELS, 1), 18534.8)
check("密度4.26の係数（根）", round(coef), 725416)
check("密度4.26の係数（全段）", round(coef_all), 836293)
check("(2·K0)² [bits]", f"{(2 * K0) ** 2:.4g}", "1.034e+09")
check("密度4.26 の log2 n の閾値", f"{coef ** 2:.3g}", "5.26e+11")
check("2^(C·n/√ln n) 形の C", round(coef * math.sqrt(LN2)), 603949)

# 閾値 (2·K0)² ビットの整数そのものは作れる。作れないのは、それだけの変数を持つ入力のほう
limit_bits = int((2 * K0) ** 2)
t0 = time.perf_counter()
big = 1 << limit_bits
elapsed = time.perf_counter() - t0
print(f"規模（参考。時間と大きさは環境で変わる）: 1 << {limit_bits:,} の bit_length = {big.bit_length():,}、"
      f"オブジェクトは {sys.getsizeof(big) / 1e6:.1f} MB、作成 {elapsed:.3f} 秒、10進で約 {limit_bits * math.log10(2):.3g} 桁")
del big


def count_tuples(n_vars, budget):
    """各重み w=1,2,… の変数が n_vars 個ずつあるとき、Σ w·β < budget を満たす β の個数。"""
    ways = [0] * budget
    ways[0] = 1
    for w in range(1, budget):
        for _ in range(n_vars):
            for k in range(w, budget):
                ways[k] += ways[k - w]
    return sum(ways)


for (n_vars, budget), want in {(2, 200): 0.866, (6, 300): 0.871, (6, 600): 0.901}.items():
    ratio = math.log(count_tuples(n_vars, budget)) / (2 * math.pi * math.sqrt(budget * n_vars / 6))
    check(f"E5 の個数/推定 (N,p)=({n_vars},{budget})", round(ratio, 3), want)
ratio = math.log(count_tuples(6, 1200)) / (2 * math.pi * math.sqrt(1200 * 6 / 6))
print(f"追加 (N,p)=(6,1200): 再計算 {ratio:.3f}  （note は「1 に近づく」と書くだけで値なし）")


# --- 3. 命題B.2: 指数 ρ(n) = n(ln ln n)²/√(ln n)（定数1）が 2^n を下回る位置 --------------

g = lambda u: u**0.25 - math.log(u)  # (ln u)² < √u ⇔ ln u < u^(1/4)
lo = 256.0  # g の最小値の位置
hi = lo
while g(hi) < 0:
    hi *= 2
for _ in range(200):
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if g(mid) < 0 else (lo, mid)

print("\n== 命題B.2 ==")
check("自然対数の交点 log10 n", round(hi / LN10, 1), 2390.2)

g2 = lambda big_l: math.sqrt(big_l) - math.log2(big_l) ** 2  # 底2: (log2 L)² < √L, L = log2 n
lo2 = hi2 = 16.0
while g2(hi2) < 0:
    hi2 *= 2
for _ in range(200):
    mid = (lo2 + hi2) / 2
    lo2, hi2 = (mid, hi2) if g2(mid) < 0 else (lo2, mid)
check("底2の交点 log2 n（note は 2^65536）", round(hi2, 3), 65536.0)


# --- 4. OpenAI preprint の (D.5): λ^(4/5) ≤ u（根では u = ⌊λ/2^17⌋）が成り立つ位置 --------

def d5_holds(lam):
    return lam**4 <= (lam >> 17) ** 5  # λ^(4/5) ≤ u を整数のまま判定する


rng = random.Random(2611)
below = [rng.randrange(2, 2**85) for _ in range(2000)] + [2**85 - 1, 2**84, 2**60]
print("\n== (D.5) ==")
# u ≤ λ/2^17 なので u^5 ≤ λ^5/2^85 で、λ < 2^85 のとき λ^4 より小さい
check("λ < 2^85 のとき成り立つ例の数（2003 個を試す）", sum(map(d5_holds, below)), 0, source="期待")
check("λ = 2^85（等号）", d5_holds(2**85), True, source="期待")
check("λ = 2^85 + 2^17", d5_holds(2**85 + 2**17), True, source="期待")
print(f"2^85 = {2**85:,}（⌈log2 s⌉ がこれ以上。つまり s > 2^(2^85 − 1)）")


# --- 5. 補間の恒等式: 3変数・2節の例（note §3.6）と、ランダムな式での確認 ----------------

def clause_value(lits, ys):
    """節の充足多項式 1 - Π(偽にする因子)。正リテラルは (1-y)、負リテラルは y。"""
    prod = Fraction(1)
    for positive, y in zip(lits, ys):
        prod *= (1 - y) if positive else y
    return 1 - prod


def h_value(n, clauses, readings, t):
    """H(t) = Σ_x Π_e φ_e(各リテラルの読み) と、節の値が 0/1 でなかった回数・節の評価回数を返す。"""
    vecs = [[reading(t) for reading in row] for row in readings]
    total, nonbool, evaluated = Fraction(0), 0, 0
    for x in product((0, 1), repeat=n):
        term = Fraction(1)
        for lits, row in zip(clauses, vecs):
            value = clause_value(lits, [sum(c * xi for c, xi in zip(v, x)) for v in row])
            term *= value
            evaluated += 1
            nonbool += value not in (0, 1)
        total += term
    return total, nonbool, evaluated


def unit(n, i):
    return [1 if k == i else 0 for k in range(n)]


# 節1: x1 ∨ x2、節2: x2 ∨ x3。節2 の x2 の読みだけ (1-T)·x2 + T·x3 に変える
example_clauses = [(True, True), (True, True)]
example_readings = [
    [lambda t: unit(3, 0), lambda t: unit(3, 1)],
    [lambda t: [0, 1 - t, t], lambda t: unit(3, 2)],
]
values = [h_value(3, example_clauses, example_readings, Fraction(t))[0] for t in range(4)]
print("\n== 3変数・2節の例 ==")
print("H(0..3) =", [str(v) for v in values], " note: 5-2T → [5, 3, 1, -1]")
check("H(T) = 5 - 2T", [str(v) for v in values], ["5", "3", "1", "-1"])
check("T=1 で 3×1 に割れる（チーム{1,2}の3通り × チーム{3}の1通り）", values[1], 3)


def lagrange_at_zero(points):
    total = Fraction(0)
    for i, (ti, hi_) in enumerate(points):
        w = Fraction(1)
        for j, (tj, _) in enumerate(points):
            if i != j:
                w *= Fraction(-tj, ti - tj)
        total += hi_ * w
    return total


rng = random.Random(2611)
matches = nonbool = evaluated = 0
for _ in range(30):
    n, m, deg = rng.randint(4, 7), rng.randint(2, 4), rng.choice((1, 2))
    clauses = [tuple(rng.random() < 0.5 for _ in range(3)) for _ in range(m)]
    scopes = [rng.sample(range(n), 3) for _ in range(m)]
    # 係数 c[r][u]: r 次の項。0 次は元の変数の単位ベクトル
    coef_tables = [
        [[unit(n, v)] + [[rng.randint(-2, 2) for _ in range(n)] for _ in range(deg)] for v in scope]
        for scope in scopes
    ]
    readings = [
        [(lambda t, tab=tab: [sum(tab[r][u] * t**r for r in range(deg + 1)) for u in range(n)]) for tab in tabs]
        for tabs in coef_tables
    ]
    pts = []
    for t in range(1, 3 * m * deg + 2):  # 次数は高々 (出現数 3m)·deg なので、その +1 点で決まる
        total, nb, ev = h_value(n, clauses, readings, Fraction(t))
        pts.append((Fraction(t), total))
        nonbool, evaluated = nonbool + nb, evaluated + ev
    truth = sum(
        all(any(x[v] == int(pos) for pos, v in zip(lits, scope)) for lits, scope in zip(clauses, scopes))
        for x in product((0, 1), repeat=n)
    )
    matches += lagrange_at_zero(pts) == truth
print("\n== ランダムな 3-CNF（4〜7変数・2〜4節・次数1か2）==")
check("H(0) が全数の数え上げと一致", f"{matches}/30", "30/30", source="期待（note の E1 と同じ形の別の実験）")
print(f"各点での節の値が 0/1 でなかった割合: {nonbool:,}/{evaluated:,}")

print()
if failures:
    print(f"食い違い {len(failures)} 件: {failures}")
    sys.exit(1)
print("すべて一致")
