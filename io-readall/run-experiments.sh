#!/bin/sh
# Go 1.26 が小さい入力で遅い理由を探すため、1.26 で既定オンになった実験を1つずつ切って比べる。
# 使い方: ./run-experiments.sh [count]   出力は results-exp/<label>.txt
set -eu
cd "$(dirname "$0")"
COUNT=${1:-5}
mkdir -p results-exp
rm -f results-exp/*.txt

run() { # label GOEXPERIMENT
  docker run --rm --cpus 4 --cpuset-cpus 0-3 -m 4g --network none \
    -e GOMAXPROCS=4 -e GOFLAGS=-buildvcs=false -e GOEXPERIMENT="$2" \
    -v "$PWD":/m:ro -w /m golang:1.26 \
    go test -run '^$' -bench '^BenchmarkCliff$/size=(480|512)B/impl=v125$' -benchmem -benchtime 200000x -count 1 . \
    >> "results-exp/$1.txt"
}

i=1
while [ "$i" -le "$COUNT" ]; do
  run default ""
  run nogreenteagc nogreenteagc
  run norandomizedheapbase64 norandomizedheapbase64
  run both-off nogreenteagc,norandomizedheapbase64
  i=$((i + 1))
done
