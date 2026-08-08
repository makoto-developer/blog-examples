"""BB84 の盗聴検知を外部ライブラリなしで実装して測る。

記事「BB84 は何を根拠に安全なのか —— 盗聴検知を実装して測る」の実装。
https://blog.makoto-developer.net/articles/bb84-eavesdropping-detection

乱数は seed 固定なので、同じ数字が出る。
"""

import random

SEED = 20260805
N_BITS = 2000       # 1セッションの送信ビット数
N_SESSIONS = 200    # 平均を取るセッション数


def measure(bit, prep_basis, meas_basis, rng):
    """prep_basis で用意した bit を meas_basis で測る。
    基底が一致すれば決定的に bit、違えば 1/2 でランダム。"""
    if prep_basis == meas_basis:
        return bit
    return rng.randint(0, 1)


def session(rng, n=N_BITS, eve_rate=0.0):
    """1セッション分の BB84。ふるい鍵 [(alice_bit, bob_bit), ...] を返す。"""
    a_bits = [rng.randint(0, 1) for _ in range(n)]
    a_base = [rng.randint(0, 1) for _ in range(n)]

    sent_bits, sent_base = list(a_bits), list(a_base)

    # Eve: intercept-resend。測って作り直して転送する
    for i in range(n):
        if rng.random() < eve_rate:
            e_base = rng.randint(0, 1)
            e_bit = measure(a_bits[i], a_base[i], e_base, rng)
            sent_bits[i], sent_base[i] = e_bit, e_base

    b_base = [rng.randint(0, 1) for _ in range(n)]
    b_bits = [measure(sent_bits[i], sent_base[i], b_base[i], rng) for i in range(n)]

    # 基底照合（ふるい分け）。基底そのものは公開してよい
    return [(a_bits[i], b_bits[i]) for i in range(n) if a_base[i] == b_base[i]]


# ------------------------------------------------ 第4節: ふるい鍵の残り方

def section4(rng):
    sent = sifted = 0
    for _ in range(N_SESSIONS):
        s = session(rng)
        sent += N_BITS
        sifted += len(s)
    print("## 4. ふるい鍵はどれだけ残るか")
    print()
    print(f"基底一致率 = {sifted / sent:.4f}（理論値 0.5）")
    print()

    s = session(rng)
    check = len(s) // 2
    final = len(s) - check
    print("| 段階 | ビット数 |")
    print("|---|---:|")
    print(f"| 送信 | {N_BITS:,} |")
    print(f"| ふるい鍵（基底一致） | {len(s):,} |")
    print(f"| 照合に消費 | {check:,} |")
    print(f"| 最終鍵 | {final:,} |")
    print()
    print(f"送信の {final / N_BITS * 100:.1f}% が鍵として残る。")
    print()


# ------------------------------------------------ 第5節: 盗聴率と誤り率

def section5(rng):
    print("## 5. 盗聴率と誤り率")
    print()
    print("| 盗聴率 | QBER 平均 | 最小 | 最大 | 鍵一致率 | 理論値 |")
    print("|---:|---:|---:|---:|---:|---:|")
    for f in [0.00, 0.10, 0.25, 0.50, 0.75, 1.00]:
        qbers, agree = [], 0
        for _ in range(N_SESSIONS):
            s = session(rng, eve_rate=f)
            if not s:
                continue
            half = len(s) // 2
            check, keep = s[:half], s[half:]
            qbers.append(sum(1 for a, b in check if a != b) / max(1, len(check)))
            if keep and all(a == b for a, b in keep):
                agree += 1
        print(f"| {f:.2f} | {sum(qbers)/len(qbers):.4f} | {min(qbers):.4f} | "
              f"{max(qbers):.4f} | {agree/N_SESSIONS:.2f} | {f/4:.4f} |")
    print()


# ------------------------------------------------ 第6節: 検知に要る照合ビット数

def section6(rng, trials=3000):
    print("## 6. 検知にはどれだけ照合すればよいか（全面盗聴）")
    print()
    print("| 照合ビット数 m | 理論 0.75^m | 実測 |")
    print("|---:|---:|---|")
    for m in [10, 20, 30, 50, 100]:
        miss = 0
        for _ in range(trials):
            s = session(rng, n=4 * m + 40, eve_rate=1.0)
            if len(s) >= m and all(a == b for a, b in s[:m]):
                miss += 1
        print(f"| {m} | {0.75 ** m:.2e} | {miss/trials:.2e}（{miss}回） |")
    print()


# ------------------------------------------------ 第7節: 薄く盗めば隠れられるか

def section7(rng):
    print("## 7. 薄く盗めば隠れられるのか")
    print()
    print("| 盗聴率 | QBER | 照合100ビットで見逃す確率 |")
    print("|---:|---:|---:|")
    for f in [0.02, 0.05, 0.10, 0.20]:
        err = tot = 0
        for _ in range(N_SESSIONS):
            s = session(rng, eve_rate=f)
            err += sum(1 for a, b in s if a != b)
            tot += len(s)
        q = err / tot
        print(f"| {f:.2f} | {q:.4f} | {(1 - q) ** 100:.2e} |")
    print()


if __name__ == "__main__":
    rng = random.Random(SEED)
    section4(rng)
    section5(rng)
    section6(rng)
    section7(rng)
