// 他の goroutine の GC が自分を止めるかを測る（Go 側）
//
//	go run gc.go
//
// 記事「「軽量プロセス」はどれくらい軽いのか」の続き。BEAM 側の gc.exs と同じ設計。
package main

import (
	"fmt"
	"runtime"
	"runtime/debug"
	"sort"
	"time"
)

const spinMs = 3000

// ゴミを作り続ける
func allocator(stop chan struct{}) {
	for {
		select {
		case <-stop:
			return
		default:
		}
		s := make([]struct {
			i int
			s string
		}, 0, 200)
		for i := 0; i < 200; i++ {
			s = append(s, struct {
				i int
				s string
			}{i, fmt.Sprint(i)})
		}
		_ = s
	}
}

// 同じくらい CPU を使うが、ゴミを作らない
func spinner(stop chan struct{}) {
	acc := 0
	for {
		select {
		case <-stop:
			return
		default:
		}
		for i := 0; i < 200; i++ {
			acc = (acc + i*i) % 1000003
		}
	}
}

func spin(d time.Duration) []int64 {
	gaps := make([]int64, 0, 1<<22)
	start := time.Now()
	prev := start
	for {
		now := time.Now()
		gaps = append(gaps, now.Sub(prev).Microseconds())
		prev = now
		if now.Sub(start) >= d {
			return gaps
		}
	}
}

func pct(s []int64, p float64) int64 {
	i := int(float64(len(s)) * p)
	if i >= len(s) {
		i = len(s) - 1
	}
	return s[i]
}

func run(label string, n int, worker func(chan struct{})) {
	stop := make(chan struct{})
	for i := 0; i < n; i++ {
		go worker(stop)
	}
	time.Sleep(300 * time.Millisecond)
	spin(200 * time.Millisecond) // ウォームアップ

	var g0, g1 debug.GCStats
	debug.ReadGCStats(&g0)
	gaps := spin(spinMs * time.Millisecond)
	debug.ReadGCStats(&g1)

	close(stop)
	time.Sleep(100 * time.Millisecond)

	sort.Slice(gaps, func(i, j int) bool { return gaps[i] < gaps[j] })
	cycles := g1.NumGC - g0.NumGC
	stw := (g1.PauseTotal - g0.PauseTotal).Microseconds()

	over := func(th int64) int {
		i := sort.Search(len(gaps), func(k int) bool { return gaps[k] > th })
		return len(gaps) - i
	}

	fmt.Printf("| %s | %d | %d | %d | %d | %d | %d | %d μs |\n",
		label, pct(gaps, 0.999), pct(gaps, 0.99999),
		over(100), over(500), over(1000), cycles, stw)
}

func main() {
	fmt.Printf("Go %s / GOMAXPROCS %d / 各3秒スピン\n", runtime.Version(), runtime.GOMAXPROCS(0))
	fmt.Println("読み間隔（μs）。大きい値＝その間この goroutine は止められていた")
	fmt.Println()
	fmt.Println("| 隣人 | p99.9 | p99.999 | >100μs | >500μs | >1ms | GCサイクル | STW合計 |")
	fmt.Println("|---|---:|---:|---:|---:|---:|---:|---:|")

	run("なし", 0, allocator)
	for _, n := range []int{10, 100, 1000} {
		run(fmt.Sprintf("ゴミを作らない %d 本", n), n, spinner)
		run(fmt.Sprintf("**ゴミを作る %d 本**", n), n, allocator)
	}
}
