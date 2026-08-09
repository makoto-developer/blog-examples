"""テープを持たない reverse（クロージャ方式）と、二重数を入れ子にした高階微分。

記事「自動微分を実装する」の続き。
https://blog.makoto-developer.net/articles/automatic-differentiation-forward-reverse

前の記事の reverse はテープ（Wengert list）に (親, 局所微分) を積んでいた。
ここでは記録の代わりに **逆伝播そのものをクロージャとして持つ**。
"""

import math

# ---------------------------------------------------------- クロージャ方式


class CVar:
    """逆伝播をクロージャで持つ変数。テープを作らない。

    各ノードは「自分の随伴を受け取って、親の随伴に足す」関数を1つ持つ。
    グラフは Python のクロージャの参照だけで表現される。
    """

    __slots__ = ("v", "grad", "_back", "_parents")

    def __init__(self, v, parents=(), back=None):
        self.v = v
        self.grad = 0.0
        self._parents = parents
        self._back = back  # 自分の grad を親の grad へ配る

    def backward(self):
        # 逆順に一度ずつ回すためのトポロジカル順。
        # 素直に再帰で書くと連鎖が1000段あたりで Python の再帰上限に当たるので、
        # 明示スタックで回す（テープ方式は平らな配列なのでこの問題が起きない）。
        order, seen, stack = [], set(), [(self, False)]
        while stack:
            node, expanded = stack.pop()
            if expanded:
                order.append(node)
                continue
            if id(node) in seen:
                continue
            seen.add(id(node))
            stack.append((node, True))
            for p in node._parents:
                if id(p) not in seen:
                    stack.append((p, False))

        self.grad = 1.0
        for node in reversed(order):
            if node._back is not None:
                node._back(node.grad)

    def __add__(self, o):
        o = o if isinstance(o, CVar) else CVar(o)

        def back(g):
            self.grad += g
            o.grad += g

        return CVar(self.v + o.v, (self, o), back)

    def __sub__(self, o):
        o = o if isinstance(o, CVar) else CVar(o)

        def back(g):
            self.grad += g
            o.grad -= g

        return CVar(self.v - o.v, (self, o), back)

    def __mul__(self, o):
        o = o if isinstance(o, CVar) else CVar(o)

        def back(g):
            self.grad += g * o.v
            o.grad += g * self.v

        return CVar(self.v * o.v, (self, o), back)

    def __truediv__(self, o):
        o = o if isinstance(o, CVar) else CVar(o)

        def back(g):
            self.grad += g / o.v
            o.grad -= g * self.v / (o.v * o.v)

        return CVar(self.v / o.v, (self, o), back)

    __radd__ = __add__
    __rmul__ = __mul__

    def __rsub__(self, o):
        return CVar(o) - self

    def __rtruediv__(self, o):
        return CVar(o) / self


def c_sin(x):
    c = math.cos(x.v)

    def back(g):
        x.grad += g * c

    return CVar(math.sin(x.v), (x,), back)


def c_tanh(x):
    t = math.tanh(x.v)

    def back(g):
        x.grad += g * (1.0 - t * t)

    return CVar(t, (x,), back)


def c_exp(x):
    e = math.exp(x.v)

    def back(g):
        x.grad += g * e

    return CVar(e, (x,), back)


def closure_grad(f, xs):
    """スカラー出力の勾配。前向き1回＋逆伝播1回。"""
    vs = [CVar(x) for x in xs]
    out = f(vs)
    out = out[0] if isinstance(out, list) else out
    out.backward()
    return [v.grad for v in vs]


# ------------------------------------------------ 入れ子の二重数（高階微分）


class Jet:
    """二重数。係数体に Jet 自身を入れられるので、入れ子にすると高階が取れる。

    Jet(v, d) の v と d に float ではなく Jet を入れると、
    「微分の微分」がそのまま計算される。
    """

    __slots__ = ("v", "d")

    def __init__(self, v, d=0.0):
        self.v = v
        self.d = d

    def _lift(self, o):
        return o if isinstance(o, Jet) else Jet(o, zero_like(self.d))

    def __add__(self, o):
        o = self._lift(o)
        return Jet(self.v + o.v, self.d + o.d)

    def __sub__(self, o):
        o = self._lift(o)
        return Jet(self.v - o.v, self.d - o.d)

    def __mul__(self, o):
        o = self._lift(o)
        return Jet(self.v * o.v, self.d * o.v + self.v * o.d)

    def __truediv__(self, o):
        o = self._lift(o)
        return Jet(self.v / o.v, (self.d * o.v - self.v * o.d) / (o.v * o.v))

    __radd__ = __add__
    __rmul__ = __mul__

    def __rsub__(self, o):
        return self._lift(o) - self

    def __rtruediv__(self, o):
        return self._lift(o) / self


def zero_like(x):
    return Jet(zero_like(x.v), zero_like(x.d)) if isinstance(x, Jet) else 0.0


def j_sin(x):
    return Jet(j_sin(x.v), j_cos(x.v) * x.d) if isinstance(x, Jet) else math.sin(x)


def j_cos(x):
    return Jet(j_cos(x.v), Jet(0.0) - j_sin(x.v) * x.d) if isinstance(x, Jet) else math.cos(x)


def j_exp(x):
    if not isinstance(x, Jet):
        return math.exp(x)
    e = j_exp(x.v)
    return Jet(e, e * x.d)


def seed(x, order):
    """order 階まで取れるように x を入れ子にする。"""
    j = x
    for _ in range(order):
        j = Jet(j, 1.0 if not isinstance(j, Jet) else one_like(j))
    return j


def one_like(x):
    return Jet(one_like(x.v), zero_like(x.d)) if isinstance(x, Jet) else 1.0


def nth(j, k):
    """k 階微分の値を取り出す（テイラー係数ではなく微分係数）。"""
    for _ in range(k):
        j = j.d
    while isinstance(j, Jet):
        j = j.v
    return j
