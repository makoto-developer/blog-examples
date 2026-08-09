# 他のプロセスの GC が自分を止めるかを測る（BEAM 側）
#
#   elixir gc.exs
#
# 記事「「軽量プロセス」はどれくらい軽いのか」の続き。
#
# 時刻を読み続けるループの「読みと読みの間隔」を測る。自分が止められた時間が
# そのまま出る。ゴミを作る隣人と、同じだけ CPU を使うがゴミを作らない隣人を
# 並べることで、CPU の取り合いと GC を切り分ける。

defmodule GcBench do
  @spin_ms 3_000
  @warmup 200_000

  # ゴミを作り続ける
  def allocator do
    _ = Enum.map(1..200, fn i -> {i, Integer.to_string(i)} end)
    allocator()
  end

  # 同じくらい CPU を使うが、ゴミをほとんど作らない（整数の畳み込みだけ）
  def spinner(acc) do
    spinner(Enum.reduce(1..200, acc, fn i, a -> rem(a + i * i, 1_000_003) end))
  end

  def spin(until, prev, acc) do
    now = System.monotonic_time(:microsecond)
    if now >= until, do: acc, else: spin(until, now, [now - prev | acc])
  end

  def pct(sorted, p), do: Enum.at(sorted, min(length(sorted) - 1, trunc(length(sorted) * p)))

  def gc_count do
    {n, _, _} = :erlang.statistics(:garbage_collection)
    n
  end

  def run(label, n, fun) do
    pids = for _ <- 1..n//1, do: spawn(fun)
    Process.sleep(300)

    # ウォームアップ分を捨ててから本測定
    t0 = System.monotonic_time(:microsecond)
    _ = spin(t0 + 200_000, t0, [])

    g0 = gc_count()
    t1 = System.monotonic_time(:microsecond)
    gaps = spin(t1 + @spin_ms * 1000, t1, [])
    g1 = gc_count()

    Enum.each(pids, &Process.exit(&1, :kill))
    Process.sleep(100)

    s = Enum.sort(gaps)
    over = fn th -> Enum.count(gaps, &(&1 > th)) end

    IO.puts(
      "| #{label} | #{pct(s, 0.999)} | #{pct(s, 0.99999)} | " <>
        "#{over.(100)} | #{over.(500)} | #{over.(1000)} | #{div(g1 - g0, 1000)}k |"
    )
  end
end

IO.puts("BEAM / スケジューラ #{:erlang.system_info(:schedulers_online)} / 各3秒スピン")
IO.puts("読み間隔（μs）。大きい値＝その間このプロセスは止められていた\n")
IO.puts("| 隣人 | p99.9 | p99.999 | >100μs | >500μs | >1ms | GC回数 |")
IO.puts("|---|---:|---:|---:|---:|---:|---:|")

GcBench.run("なし", 0, &GcBench.allocator/0)

for n <- [10, 100, 1000] do
  GcBench.run("ゴミを作らない #{n} 本", n, fn -> GcBench.spinner(0) end)
  GcBench.run("**ゴミを作る #{n} 本**", n, &GcBench.allocator/0)
end
