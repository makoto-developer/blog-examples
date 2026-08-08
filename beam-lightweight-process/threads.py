"""OS スレッドのメモリと生成時間を測る（第4節）。

    python3 threads.py

記事「「軽量プロセス」はどれくらい軽いのか」
https://blog.makoto-developer.net/articles/beam-lightweight-process-memory

CPython の threading は 1 スレッド = 1 OS スレッド（pthread）である。
ただし Thread オブジェクトの分も乗るので、生の pthread より大きく出る。
"""

import gc
import resource
import sys
import threading
import time

# macOS の ru_maxrss はバイト、Linux は KB
SCALE = 1 if sys.platform == "darwin" else 1024


def rss():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * SCALE


def measure(n):
    gc.collect()
    time.sleep(0.05)
    before = rss()

    stop = threading.Event()
    ready = threading.Semaphore(0)

    def idle():
        ready.release()
        stop.wait()

    t0 = time.perf_counter()
    ts = [threading.Thread(target=idle, daemon=True) for _ in range(n)]
    for t in ts:
        t.start()
    elapsed = time.perf_counter() - t0

    for _ in range(n):          # 全部が走り出すまで待つ
        ready.acquire()
    total = rss() - before

    stop.set()
    for t in ts:
        t.join()
    gc.collect()

    return total, total // n, elapsed / n * 1e6


print("## 4. OS スレッド（Python、RSS の増分）")
print()
print("| 本数 | 合計 | 1本あたり | 生成時間 |")
print("|---:|---:|---:|---:|")
for n in (100, 500, 1000, 2000):
    total, per, us = measure(n)
    print(f"| {n:,} | {total/1048576:.2f} MB | {per:,} B | {us:.2f} μs |")

print()
print(f"Python {sys.version.split()[0]} / {sys.platform}")
