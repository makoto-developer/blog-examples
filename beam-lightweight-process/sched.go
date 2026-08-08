// コンテナの CPU 制限を Go が認識するか（第7.1節）
package main

import (
	"fmt"
	"runtime"
)

func main() {
	fmt.Printf("GOMAXPROCS=%d NumCPU=%d %s\n",
		runtime.GOMAXPROCS(0), runtime.NumCPU(), runtime.Version())
}
