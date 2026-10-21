#!/bin/sh
# 同じベンチを Docker を通さずホスト（macOS）で回す。倍率が環境でどれだけ動くかを見るための参考値。
# 使い方: ./run-host.sh [count]   出力は results-host/<toolchain>-Chunk.txt
set -eu
cd "$(dirname "$0")"
COUNT=${1:-5}
mkdir -p results-host
rm -f results-host/*.txt

i=1
while [ "$i" -le "$COUNT" ]; do
  for v in go1.25.13 go1.26.5; do
    GOTOOLCHAIN=$v go test -run '^$' -bench '^BenchmarkChunk$/size=.*/chunk=4KB/impl=std$' \
      -benchmem -benchtime 0.5s -count 1 . >> "results-host/$v-Chunk.txt"
  done
  i=$((i + 1))
done
