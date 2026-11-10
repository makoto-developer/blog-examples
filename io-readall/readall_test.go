package readall

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"runtime"
	"testing"
)

type impl struct {
	name string
	fn   func(io.Reader) ([]byte, error)
}

// std は走らせているツールチェーンの io.ReadAll。v125 / v126 はどのツールチェーンでも同じソース。
var impls = []impl{
	{"std", io.ReadAll},
	{"v125", ReadAll125},
	{"v126", ReadAll126},
}

var sizes = []int{512, 4 << 10, 64 << 10, 1 << 20, 16 << 20, 100 << 20}

// 0 は「渡された空きを埋められるだけ返す」。*os.File の Read に近い振る舞い。
var chunks = []int{512, 4 << 10, 64 << 10, 0}

func sizeName(n int) string {
	switch {
	case n >= 1<<20 && n%(1<<20) == 0:
		return fmt.Sprintf("%dMB", n>>20)
	case n >= 1<<10 && n%(1<<10) == 0:
		return fmt.Sprintf("%dKB", n>>10)
	}
	return fmt.Sprintf("%dB", n)
}

func chunkName(c int) string {
	if c == 0 {
		return "fill"
	}
	return sizeName(c)
}

func payload(n int) []byte {
	b := make([]byte, n)
	for i := range b {
		b[i] = byte(i * 31)
	}
	return b
}

func TestCopiesMatchStd(t *testing.T) {
	for _, n := range []int{0, 1, 480, 481, 511, 512, 513, 4095, 4096, 70000, 1 << 20} {
		data := payload(n)
		for _, c := range chunks {
			for _, im := range impls {
				got, err := im.fn(&ChunkReader{Buf: data, Chunk: c})
				if err != nil || !bytes.Equal(got, data) {
					t.Fatalf("%s size=%d chunk=%d: err=%v equal=%v", im.name, n, c, err, bytes.Equal(got, data))
				}
			}
		}
	}
}

// 返却粒度（Chunk）だけを変える。システムコールは含まない。
func BenchmarkChunk(b *testing.B) {
	for _, n := range sizes {
		data := payload(n)
		for _, c := range chunks {
			for _, im := range impls {
				b.Run(fmt.Sprintf("size=%s/chunk=%s/impl=%s", sizeName(n), chunkName(c), im.name), func(b *testing.B) {
					b.SetBytes(int64(n))
					b.ReportAllocs()
					for b.Loop() {
						if _, err := im.fn(&ChunkReader{Buf: data, Chunk: c}); err != nil {
							b.Fatal(err)
						}
					}
				})
			}
		}
	}
}

// 1バイト刻みで崖を探す。1回の Read で入力を全部返すので、効くのは切り替え条件だけ。
func BenchmarkCliff(b *testing.B) {
	for n := 476; n <= 516; n++ {
		data := payload(n)
		for _, im := range impls {
			b.Run(fmt.Sprintf("size=%dB/impl=%s", n, im.name), func(b *testing.B) {
				b.ReportAllocs()
				for b.Loop() {
					if _, err := im.fn(&ChunkReader{Buf: data}); err != nil {
						b.Fatal(err)
					}
				}
			})
		}
	}
}

// 毎回 Open → ReadAll → Close する。ファイルは b.TempDir() に置き、測定前に1回読んでページキャッシュに載せる。
func BenchmarkFile(b *testing.B) {
	dir := b.TempDir()
	for _, n := range sizes {
		path := filepath.Join(dir, sizeName(n))
		if err := os.WriteFile(path, payload(n), 0o600); err != nil {
			b.Fatal(err)
		}
		if _, err := os.ReadFile(path); err != nil {
			b.Fatal(err)
		}
		for _, im := range impls {
			b.Run(fmt.Sprintf("size=%s/impl=%s", sizeName(n), im.name), func(b *testing.B) {
				b.SetBytes(int64(n))
				b.ReportAllocs()
				for b.Loop() {
					f, err := os.Open(path)
					if err != nil {
						b.Fatal(err)
					}
					if _, err := im.fn(f); err != nil {
						b.Fatal(err)
					}
					f.Close()
				}
			})
		}
	}
}

// Open と Close だけ。File の小さいサイズで、どこまでがシステムコールの代金かを引くために使う。
func BenchmarkOpenClose(b *testing.B) {
	path := filepath.Join(b.TempDir(), "f")
	if err := os.WriteFile(path, payload(512), 0o600); err != nil {
		b.Fatal(err)
	}
	b.ReportAllocs()
	for b.Loop() {
		f, err := os.Open(path)
		if err != nil {
			b.Fatal(err)
		}
		f.Close()
	}
}

func TestMain(m *testing.M) {
	fmt.Printf("env: %s GOMAXPROCS=%d GOGC=%q GOMEMLIMIT=%q NumCPU=%d\n",
		runtime.Version(), runtime.GOMAXPROCS(0), os.Getenv("GOGC"), os.Getenv("GOMEMLIMIT"), runtime.NumCPU())
	os.Exit(m.Run())
}
