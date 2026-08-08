# メモリ制限のあるコンテナでプロセスを増やし続ける（第7.2節）
#
#   docker run --rm -m 512m --memory-swap=512m -v "$PWD":/w -w /w \
#     elixir:1.19-otp-28-slim sh -c 'elixir --erl "+P 2000000" oom.exs; echo "exit=$?"'
#
# BEAM は cgroup の memory.max を見ないので、上限を知らないまま確保し続けて
# OOM killer に殺される（終了コード 137）。

defmodule Oom do
  def idle do
    receive do
      :stop -> :ok
    end
  end

  def mb(b), do: :erlang.float_to_binary(b / 1_048_576, decimals: 1)
end

# cgroup の上限は読める。読めるのに使っていない、というのが第7.2節の趣旨
case File.read("/sys/fs/cgroup/memory.max") do
  {:ok, v} -> IO.puts("cgroup memory.max = #{String.trim(v)}")
  _ -> IO.puts("cgroup memory.max = (読めず)")
end

IO.puts("")
IO.puts("| プロセス数 | BEAM の総メモリ |")
IO.puts("|---:|---:|")

steps =
  case System.argv() do
    ["swap"] -> [50_000, 100_000, 200_000, 300_000, 350_000, 400_000, 450_000]
    _ -> [10_000, 50_000, 100_000, 150_000, 200_000, 250_000]
  end

Enum.reduce(steps, 0, fn target, made ->
  for _ <- 1..(target - made), do: spawn(&Oom.idle/0)
  IO.puts("| #{target} | #{Oom.mb(:erlang.memory(:total))} MB |")
  target
end)

IO.puts("ここまで来たら殺されていない")
