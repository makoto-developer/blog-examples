// Package readall は Go 1.25 と 1.26 の io.ReadAll を写したもの。
// 同じツールチェーンで両方を走らせ、ソースの差とツールチェーンの差を分けるために置いている。
package readall

import "io"

// ReadAll125 は Go 1.25.13 の src/io/io.go の ReadAll をそのまま写したもの。
func ReadAll125(r io.Reader) ([]byte, error) {
	b := make([]byte, 0, 512)
	for {
		n, err := r.Read(b[len(b):cap(b)])
		b = b[:len(b)+n]
		if err != nil {
			if err == io.EOF {
				err = nil
			}
			return b, err
		}

		if len(b) == cap(b) {
			// Add more capacity (let append pick how much).
			b = append(b, 0)[:len(b)]
		}
	}
}

// ReadAll126 は Go 1.26.5 の src/io/io.go の ReadAll をそのまま写したもの。
func ReadAll126(r io.Reader) ([]byte, error) {
	// Build slices of exponentially growing size,
	// then copy into a perfectly-sized slice at the end.
	b := make([]byte, 0, 512)
	// Starting with next equal to 256 (instead of say 512 or 1024)
	// allows less memory usage for small inputs that finish in the
	// early growth stages, but we grow the read sizes quickly such that
	// it does not materially impact medium or large inputs.
	next := 256
	chunks := make([][]byte, 0, 4)
	// Invariant: finalSize = sum(len(c) for c in chunks)
	var finalSize int
	for {
		n, err := r.Read(b[len(b):cap(b)])
		b = b[:len(b)+n]
		if err != nil {
			if err == io.EOF {
				err = nil
			}
			if len(chunks) == 0 {
				return b, err
			}

			// Build our final right-sized slice.
			finalSize += len(b)
			final := append([]byte(nil), make([]byte, finalSize)...)[:0]
			for _, chunk := range chunks {
				final = append(final, chunk...)
			}
			final = append(final, b...)
			return final, err
		}

		if cap(b)-len(b) < cap(b)/16 {
			// Move to the next intermediate slice.
			chunks = append(chunks, b)
			finalSize += len(b)
			b = append([]byte(nil), make([]byte, next)...)[:0]
			next += next / 2
		}
	}
}

// ChunkReader は最大 Chunk バイトずつ返すメモリ上の Reader。
// Chunk が 0 なら、渡されたスライスの空きを埋められるだけ返す。
// システムコールもファイルシステムも通らないので、返却粒度だけを変えて比べられる。
type ChunkReader struct {
	Buf   []byte
	Chunk int
}

func (c *ChunkReader) Read(p []byte) (int, error) {
	if len(c.Buf) == 0 {
		return 0, io.EOF
	}
	n := min(len(p), len(c.Buf))
	if c.Chunk > 0 {
		n = min(n, c.Chunk)
	}
	copy(p, c.Buf[:n])
	c.Buf = c.Buf[n:]
	return n, nil
}
