# io-readall

記事「io.ReadAll が速くなった —— ただし 481〜511バイトでは遅くなる」（下書き）の数字を出したコード。

Go 1.25 と 1.26 の `io.ReadAll` を比べる。ソースの差とツールチェーンの差を分けるため、
両バージョンの `ReadAll` を `readall.go` に写し、3実装（`std` / `v125` / `v126`）を両方のツールチェーンで走らせる。
写しは標準ライブラリと一字一句同じ（`EOF` を `io.EOF` にした以外）。

| ファイル | 中身 |
|---|---|
| `readall.go` | `ReadAll125` / `ReadAll126` の写しと、返す量を変えられるメモリ上の Reader |
| `readall_test.go` | ベンチ（`Chunk` / `Cliff` / `File` / `OpenClose`）と、写しが同じ結果を返すことのテスト |
| `run.sh` | Docker で 1.25 と 1.26 を1回ずつ交互に回す（記事の表はこれ） |
| `run-host.sh` | 同じベンチを macOS で直接回す（倍率が環境で動くことを見る参考値） |
| `run-experiments.sh` | 1.26 で `GOEXPERIMENT` を1つずつ切って比べる |
| `analyze.py` | `results/` から中央値と最小〜最大の表を作る |
| `results/` | `run.sh` の生の出力（記事の表の元） |
| `results-sequential/` | 1.25 を全部測ってから 1.26 を測った版。大きい入力の改善がソースの変更による、という結論は交互にした版と変わらなかった。ただし個々の比較の向きが変わるものはある（100MB の `v126` のツールチェーン比較は、交互で +1.8%、順番で −6.2%） |
| `results-host/` / `results-exp/` | `run-host.sh` / `run-experiments.sh` の生の出力 |

## 再現

```bash
./run.sh 10                          # 約30分。Docker が要る
python3 analyze.py Chunk chunk=4KB
python3 analyze.py Cliff
```

差の有無は `benchstat` で検定した。`results/*.txt` の先頭行 `env: go1.xx ...` を
`toolchain: go1.xx` に置き換えてから、`-col toolchain` で比べる。

記事の数字を出したイメージは次の2つ（タグは動くので、同じものを使うなら digest で指定する）。

- `golang:1.25` = `golang@sha256:d7ae6dbb143c4eb97788a53a2bfa879cdde91f793c1d44d9f3bc7cb0df2e4e5f`（go1.25.13）
- `golang:1.26` = `golang@sha256:2005724102f45917a63e9d092fc0e4ea56ea575048ce147caad5f5f61502c365`（go1.26.5）

## 数字の再現について

- `B/op` と `allocs/op` は、Linux（Docker）と macOS でほぼ同じ値になった。どちらも 1反復ごとに作る Reader の 32B・1回を含む
- `ns/op` は環境で動く。とくに 1MB 以上の倍率は、Docker（4.4〜5.0倍）と macOS 直（2.3〜3.1倍）で大きく違った
- File ベンチは `Close` のエラーを見ていない。記事の数字を出したコードをそのまま残しているためで、測定中に失敗した記録はない
