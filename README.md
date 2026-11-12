# blog-examples

[blog.makoto-developer.net](https://blog.makoto-developer.net) の記事に載せた数字を再現するためのコード置き場。

各ディレクトリが記事1本に対応する。外部ライブラリは使わない方針で、
`python3 <file>` だけで動くようにしてある。

| ディレクトリ | 記事 |
|---|---|
| [`automatic-differentiation/`](automatic-differentiation/) | [自動微分を実装する —— forward と reverse はどこで逆転するか](https://blog.makoto-developer.net/articles/automatic-differentiation-forward-reverse) |
| [`bb84/`](bb84/) | [BB84 は何を根拠に安全なのか —— 盗聴検知を実装して測る](https://blog.makoto-developer.net/articles/bb84-eavesdropping-detection) |
| [`beam-lightweight-process/`](beam-lightweight-process/) | [「軽量プロセス」はどれくらい軽いのか —— BEAM・goroutine・OSスレッドを実測する](https://blog.makoto-developer.net/articles/beam-lightweight-process-memory) |
| [`autodiff-closure-highorder/`](autodiff-closure-highorder/) | テープを捨てたら2.2倍遅くなった —— クロージャ方式の自動微分と高階微分（下書き） |
| [`e91-bell-under-eavesdropping/`](e91-bell-under-eavesdropping/) | Bell の破れは盗聴検知としては鈍い —— E91 を実装して測る（下書き） |
| [`gc-pause-beam-vs-go/`](gc-pause-beam-vs-go/) | 560万回GCしても止まらない、けれど遅い —— BEAM と Go の停止時間を測る（下書き） |
| [`io-readall/`](io-readall/) | io.ReadAll が速くなった —— ただし 481〜511バイトでは遅くなる（下書き） |
| [`eth-claim-constants/`](eth-claim-constants/) | OpenAI の ETH 反証主張に定数を入れると —— Dias と Lima の note を読み、数表を式から再計算した（下書き） |

## 数字の再現について

- **BB84** は乱数の seed を固定しているので、記事の表と同じ数字が出る
- **自動微分** は時間の測定を含むので、絶対値は環境で変わる。モード間の比と、
  どこで forward と reverse が逆転するかも、この実装・対象関数・測定環境で得た値である。
  環境によらないのは、実行回数（forward は入力次元の回数、reverse の逆伝播は出力次元の回数）と、
  勾配の倍率が入力次元に依存するかどうかである
- **軽量プロセス** も時間は環境で変わる。1プロセスあたりのバイト数、BEAM が CPU 制限だけを
  認識してメモリ制限を認識しないこと、`max_heap_size` が参照カウント方式のバイナリを
  素通りすること（`include_shared_binaries` を有効にしない既定のとき）の3つは、
  記事に書いた環境（OTP 28、64bit）で確かめたもので、ほかの OTP の版では確かめていない。
  第7節は Docker が要る（`elixir:1.19-otp-28-slim` / `golang:1.25-alpine` / `golang:1.24-alpine`）
- **io.ReadAll** は Go のベンチなので `python3` だけでは動かない（Docker が要る）。
  `B/op` と `allocs/op` は、確かめた2つの環境（arm64 の Linux と macOS）でほぼ同じ値になった。
  481〜511B の崖の位置は、Go 1.26 の `io.ReadAll` の切り替え条件から決まる。崖が出るのは、
  エラーを返さない `Read` のあとで、最初の 512B のバッファに 481〜511B がたまったときである
- **eth-claim-constants** は乱数の seed を固定しているので、`expected-output.txt` と同じ数字が出る。
  環境で変わるのは、`規模` の行の時間とオブジェクトの大きさだけである。
  検査するのは「note の式から note の数字が出ること」で、論文の定理の正しさは検査していない
