# blog-examples

[blog.makoto-developer.net](https://blog.makoto-developer.net) の記事に載せた数字を再現するためのコード置き場。

各ディレクトリが記事1本に対応する。外部ライブラリは使わない方針で、
`python3 <file>` だけで動くようにしてある。

| ディレクトリ | 記事 |
|---|---|
| [`automatic-differentiation/`](automatic-differentiation/) | [自動微分を実装する —— forward と reverse はどこで逆転するか](https://blog.makoto-developer.net/articles/automatic-differentiation-forward-reverse) |
| [`bb84/`](bb84/) | [BB84 は何を根拠に安全なのか —— 盗聴検知を実装して測る](https://blog.makoto-developer.net/articles/bb84-eavesdropping-detection) |

## 数字の再現について

- **BB84** は乱数の seed を固定しているので、記事の表と同じ数字が出る
- **自動微分** は時間の測定を含むので、絶対値は環境で変わる。環境によらないのは
  モード間の比（どこで forward と reverse が逆転するか）と、勾配の倍率が
  入力次元に依存するかどうかである
