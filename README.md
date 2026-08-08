# blog-examples

[blog.makoto-developer.net](https://blog.makoto-developer.net) の記事に載せた数字を再現するためのコード置き場。

各ディレクトリが記事1本に対応する。外部ライブラリは使わない方針で、
`python3 <file>` だけで動くようにしてある。

| ディレクトリ | 記事 |
|---|---|
| [`automatic-differentiation/`](automatic-differentiation/) | [自動微分を実装する —— forward と reverse はどこで逆転するか](https://blog.makoto-developer.net/articles/automatic-differentiation-forward-reverse) |
| [`bb84/`](bb84/) | [BB84 は何を根拠に安全なのか —— 盗聴検知を実装して測る](https://blog.makoto-developer.net/articles/bb84-eavesdropping-detection) |
| [`beam-lightweight-process/`](beam-lightweight-process/) | [「軽量プロセス」はどれくらい軽いのか —— BEAM・goroutine・OSスレッドを実測する](https://blog.makoto-developer.net/articles/beam-lightweight-process-memory) |

## 数字の再現について

- **BB84** は乱数の seed を固定しているので、記事の表と同じ数字が出る
- **自動微分** は時間の測定を含むので、絶対値は環境で変わる。環境によらないのは
  モード間の比（どこで forward と reverse が逆転するか）と、勾配の倍率が
  入力次元に依存するかどうかである
- **軽量プロセス** も時間は環境で変わる。環境によらないのは 1プロセスあたりの
  バイト数、BEAM が CPU 制限だけを認識してメモリ制限を認識しないこと、
  `max_heap_size` が参照カウント方式のバイナリを素通りすることである。
  第7節は Docker が要る（`elixir:1.19-otp-28-slim` / `golang:1.25-alpine` / `golang:1.24-alpine`）
