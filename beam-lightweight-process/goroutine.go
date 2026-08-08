// goroutine のメモリと生成時間を測る（第4節）
//
//	go run goroutine.go
//
// 記事「「軽量プロセス」はどれくらい軽いのか」
// https://blog.makoto-developer.net/articles/beam-lightweight-process-memory
package main

import (
	"fmt"
	"runtime"
	"sync"
	"time"
)

// BEAM 側の :erlang.memory(:processes) に対応させるため、
// ヒープとスタックの増分の合計を「1個あたり」とみなす。
func used() uint64 {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	return m.HeapAlloc + m.StackInuse
}

func delim(n uint64) string {
	s := fmt.Sprintf("%d", n)
	out := ""
	for i, c := range s {
		if i > 0 && (len(s)-i)%3 == 0 {
			out += ","
		}
		out += string(c)
	}
	return out
}

func measure(n int) (uint64, uint64, float64) {
	runtime.GC()
	time.Sleep(50 * time.Millisecond)
	before := used()

	stop := make(chan struct{})
	var wg sync.WaitGroup
	wg.Add(n)

	t0 := time.Now()
	for i := 0; i < n; i++ {
		go func() {
			defer wg.Done()
			<-stop // BEAM の receive 待ちに相当
		}()
	}
	elapsed := time.Since(t0)

	// 全部が走り出してから測る
	for runtime.NumGoroutine() < n {
		time.Sleep(time.Millisecond)
	}
	total := used() - before

	close(stop)
	wg.Wait()
	runtime.GC()

	return total, total / uint64(n), float64(elapsed.Nanoseconds()) / float64(n) / 1000.0
}

func main() {
	fmt.Println("## 4. goroutine（HeapAlloc と StackInuse の増分の合計）")
	fmt.Println()
	fmt.Println("| 個数 | 合計 | 1個あたり | 生成時間 |")
	fmt.Println("|---:|---:|---:|---:|")

	for _, n := range []int{1000, 10000, 100000, 500000} {
		total, per, us := measure(n)
		fmt.Printf("| %s | %.2f MB | %s B | %.3f μs |\n",
			delim(uint64(n)), float64(total)/1048576.0, delim(per), us)
	}

	fmt.Printf("\nGOMAXPROCS: %d / NumCPU: %d / %s\n",
		runtime.GOMAXPROCS(0), runtime.NumCPU(), runtime.Version())
}
