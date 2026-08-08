// 50万 goroutine の生成時間だけを繰り返し測る（第4節の確認用）
package main

import (
	"fmt"
	"runtime"
	"sync"
	"time"
)

func main() {
	const n = 500000
	for r := 0; r < 5; r++ {
		runtime.GC()
		time.Sleep(200 * time.Millisecond)
		stop := make(chan struct{})
		var wg sync.WaitGroup
		wg.Add(n)
		t0 := time.Now()
		for i := 0; i < n; i++ {
			go func() { defer wg.Done(); <-stop }()
		}
		el := time.Since(t0)
		for runtime.NumGoroutine() < n {
			time.Sleep(time.Millisecond)
		}
		fmt.Printf("%.3f ", float64(el.Nanoseconds())/n/1000.0)
		close(stop)
		wg.Wait()
	}
	fmt.Printf("μs  (GOMAXPROCS=%d)\n", runtime.GOMAXPROCS(0))
}
