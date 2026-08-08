"""OS スレッドを作れなくなるところまで作る（第4節）。

    python3 limit.py

記事「「軽量プロセス」はどれくらい軽いのか」
https://blog.makoto-developer.net/articles/beam-lightweight-process-memory
"""

import resource
import threading

soft, hard = resource.getrlimit(resource.RLIMIT_NPROC)
print(f"RLIMIT_NPROC: soft={soft} / hard={hard}")

stop = threading.Event()
threads = []

try:
    while True:
        t = threading.Thread(target=stop.wait, daemon=True)
        t.start()
        threads.append(t)
except (RuntimeError, MemoryError) as e:
    print(f"{len(threads) + 1} 本目で失敗: {type(e).__name__}: {e}")

print(f"作れた本数: {len(threads):,}")
stop.set()
