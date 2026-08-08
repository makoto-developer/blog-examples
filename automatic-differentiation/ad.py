"""自動微分の forward モードと reverse モード。外部ライブラリなし。

記事「自動微分を実装する —— forward と reverse はどこで逆転するか」の実装。
https://blog.makoto-developer.net/articles/automatic-differentiation-forward-reverse
"""

import math

# ---------------------------------------------------------------- forward


class Dual:
    """値と微分の組。演算子を定義するだけで連鎖律が伝播する。"""

    __slots__ = ("v", "d")

    def __init__(self, v, d=0.0):
        self.v = v
        self.d = d

    def __add__(self, o):
        o = o if isinstance(o, Dual) else Dual(o)
        return Dual(self.v + o.v, self.d + o.d)

    def __sub__(self, o):
        o = o if isinstance(o, Dual) else Dual(o)
        return Dual(self.v - o.v, self.d - o.d)

    def __mul__(self, o):
        o = o if isinstance(o, Dual) else Dual(o)
        return Dual(self.v * o.v, self.d * o.v + self.v * o.d)

    def __truediv__(self, o):
        o = o if isinstance(o, Dual) else Dual(o)
        return Dual(self.v / o.v, (self.d * o.v - self.v * o.d) / (o.v * o.v))

    __radd__ = __add__
    __rmul__ = __mul__

    def __rsub__(self, o):
        return Dual(o) - self

    def __rtruediv__(self, o):
        return Dual(o) / self


def d_sin(x):
    return Dual(math.sin(x.v), math.cos(x.v) * x.d)


def d_cos(x):
    return Dual(math.cos(x.v), -math.sin(x.v) * x.d)


def d_exp(x):
    e = math.exp(x.v)
    return Dual(e, e * x.d)


def d_tanh(x):
    t = math.tanh(x.v)
    return Dual(t, (1.0 - t * t) * x.d)


def forward_grad(f, xs):
    """ヤコビアンを返す。入力が n 個なら f を n 回実行する。"""
    n = len(xs)
    cols = []
    for i in range(n):
        duals = [Dual(x, 1.0 if j == i else 0.0) for j, x in enumerate(xs)]
        out = f(duals)
        cols.append([o.d for o in out] if isinstance(out, list) else [out.d])
    m = len(cols[0])
    return [[cols[i][k] for i in range(n)] for k in range(m)]


# ---------------------------------------------------------------- reverse


class Tape:
    """演算の記録。各ノードは (親のindex, 局所微分) の並び。"""

    __slots__ = ("nodes",)

    def __init__(self):
        self.nodes = []

    def push(self, deps):
        self.nodes.append(deps)
        return len(self.nodes) - 1


class Var:
    __slots__ = ("v", "i", "tape")

    def __init__(self, v, tape, i=None):
        self.v = v
        self.tape = tape
        self.i = tape.push([]) if i is None else i

    def _bin(self, o, val, dself, do):
        if isinstance(o, Var):
            i = self.tape.push([(self.i, dself), (o.i, do)])
        else:
            i = self.tape.push([(self.i, dself)])
        return Var(val, self.tape, i)

    def _un(self, val, dself):
        return Var(val, self.tape, self.tape.push([(self.i, dself)]))

    def __add__(self, o):
        ov = o.v if isinstance(o, Var) else o
        return self._bin(o, self.v + ov, 1.0, 1.0)

    def __sub__(self, o):
        ov = o.v if isinstance(o, Var) else o
        return self._bin(o, self.v - ov, 1.0, -1.0)

    def __mul__(self, o):
        ov = o.v if isinstance(o, Var) else o
        return self._bin(o, self.v * ov, ov, self.v)

    def __truediv__(self, o):
        ov = o.v if isinstance(o, Var) else o
        return self._bin(o, self.v / ov, 1.0 / ov, -self.v / (ov * ov))

    __radd__ = __add__
    __rmul__ = __mul__

    def __rsub__(self, o):
        return Var(o, self.tape) - self

    def __rtruediv__(self, o):
        return Var(o, self.tape) / self


def r_sin(x):
    return x._un(math.sin(x.v), math.cos(x.v))


def r_cos(x):
    return x._un(math.cos(x.v), -math.sin(x.v))


def r_exp(x):
    e = math.exp(x.v)
    return x._un(e, e)


def r_tanh(x):
    t = math.tanh(x.v)
    return x._un(t, 1.0 - t * t)


def reverse_grad(f, xs, return_tape=False):
    """ヤコビアンを返す。前向きの実行は1回、逆伝播を出力の数だけ行う。"""
    tape = Tape()
    vs = [Var(x, tape) for x in xs]
    outs = f(vs)
    if not isinstance(outs, list):
        outs = [outs]

    J = []
    for k in range(len(outs)):
        adj = [0.0] * len(tape.nodes)
        adj[outs[k].i] = 1.0
        for i in range(len(tape.nodes) - 1, -1, -1):
            a = adj[i]
            if a == 0.0:
                continue
            # 代入ではなく加算。同じ変数が複数回使われると寄与が複数経路から集まる
            for (p, dl) in tape.nodes[i]:
                adj[p] += a * dl
        J.append([adj[v.i] for v in vs])

    return (J, tape) if return_tape else J


# ------------------------------------------------- ベンチ用のテスト関数


def make_bench_fn(n, m, depth=20):
    """n 入力 m 出力。各出力は全入力に依存し、その後 depth 段の非線形連鎖を通す。"""

    def f(xs, sin=None, tanh=None):
        sin = sin or (d_sin if isinstance(xs[0], Dual) else r_sin)
        tanh = tanh or (d_tanh if isinstance(xs[0], Dual) else r_tanh)
        outs = []
        for k in range(m):
            acc = xs[0] * (1.0 + 0.1 * k)
            for j in range(1, n):
                acc = acc + xs[j] * (1.0 + 0.01 * (j + k))
            for _ in range(depth):
                acc = tanh(acc * 0.5) + sin(acc) * 0.25
            outs.append(acc)
        return outs

    return f
