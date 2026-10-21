#!/bin/sh
# 記事の数字を出したコマンド。benchsweep と同じ制約をかけ、コンテナは1本ずつ順番に走らせる。
# 1.25 と 1.26 を1回ずつ交互に回す（片方を全部測ってから他方を測ると、時間帯のずれがバージョン差に見える）。
# 使い方: ./run.sh [count]   出力は results/<image>-<bench>.txt
set -eu
cd "$(dirname "$0")"
COUNT=${1:-10}
mkdir -p results
rm -f results/*.txt

bench() { # image regex benchtime
  out="results/$(echo "$1" | tr ':' '-')-$2.txt"
  docker run --rm --cpus 4 --cpuset-cpus 0-3 -m 4g --network none \
    -e GOMAXPROCS=4 -e GOFLAGS=-buildvcs=false \
    -v "$PWD":/m:ro -w /m "$1" \
    go test -run '^$' -bench "^Benchmark$2\$" -benchmem -benchtime "$3" -count 1 . >> "$out"
}

i=1
while [ "$i" -le "$COUNT" ]; do
  for img in golang:1.25 golang:1.26; do
    bench "$img" Cliff 200000x
    bench "$img" Chunk 0.5s
    bench "$img" File 0.5s
    bench "$img" OpenClose 0.5s
  done
  echo "round $i done"
  i=$((i + 1))
done
