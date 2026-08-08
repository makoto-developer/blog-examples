# 50万プロセスの生成時間だけを繰り返し測る（第7.3節の確認用）
defmodule G do
  def idle, do: (receive do: (:stop -> :ok))
end

n = 500_000

for _ <- 1..5 do
  :erlang.garbage_collect(); Process.sleep(200)
  t0 = System.monotonic_time(:microsecond)
  pids = for _ <- 1..n, do: spawn(&G.idle/0)
  t1 = System.monotonic_time(:microsecond)
  IO.write("#{:erlang.float_to_binary((t1 - t0) / n, decimals: 3)} ")
  Enum.each(pids, &send(&1, :stop)); Process.sleep(400)
end
IO.puts("μs  (schedulers=#{:erlang.system_info(:schedulers_online)})")
