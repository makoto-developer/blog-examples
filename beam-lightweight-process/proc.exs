# BEAM のプロセスのメモリと生成時間を測る（第2・3・6節）
#
#   elixir --erl "+P 2000000" proc.exs
#
# 記事「「軽量プロセス」はどれくらい軽いのか」
# https://blog.makoto-developer.net/articles/beam-lightweight-process-memory

defmodule Bench do
  def idle do
    receive do
      :stop -> :ok
    end
  end

  # クロージャで状態を抱えたまま待つ
  def hold(state) do
    receive do
      :stop -> length(state)
    end
  end

  # プロセスを n 個作り、:erlang.memory(:processes) の増分を個数で割る
  def measure(n, spawn_fun) do
    :erlang.garbage_collect()
    Process.sleep(50)
    before = :erlang.memory(:processes)

    t0 = System.monotonic_time(:microsecond)
    pids = for _ <- 1..n, do: spawn_fun.()
    t1 = System.monotonic_time(:microsecond)

    used = :erlang.memory(:processes) - before
    Enum.each(pids, &send(&1, :stop))
    Process.sleep(200)
    :erlang.garbage_collect()

    {used, div(used, n), (t1 - t0) / n}
  end

  def mb(bytes), do: :erlang.float_to_binary(bytes / 1_048_576, decimals: 2)
  def f(x, d \\ 3), do: :erlang.float_to_binary(x / 1, decimals: d)

  # 3桁区切り
  def d(n) do
    n
    |> Integer.to_string()
    |> String.reverse()
    |> String.replace(~r/(\d{3})(?=\d)/, "\\1,")
    |> String.reverse()
  end
end

IO.puts("## 2. BEAM のプロセスを50万個作る\n")
IO.puts("| プロセス数 | 合計メモリ | 1個あたり | 生成時間 |")
IO.puts("|---:|---:|---:|---:|")

for n <- [1_000, 10_000, 100_000, 500_000] do
  {used, per, us} = Bench.measure(n, fn -> spawn(&Bench.idle/0) end)
  IO.puts("| #{Bench.d(n)} | #{Bench.mb(used)} MB | #{Bench.d(per)} B | #{Bench.f(us)} μs |")
end

IO.puts("\n単体のプロセスの内訳\n")
pid = spawn(&Bench.idle/0)
Process.sleep(10)

IO.puts("| 項目 | 値 |")
IO.puts("|---|---:|")

for {k, v} <- Process.info(pid, [:memory, :heap_size, :stack_size, :total_heap_size]) do
  unit =
    case k do
      :memory -> " B"
      :stack_size -> ""
      _ -> " words"
    end

  IO.puts("| #{k} | #{Bench.d(v)}#{unit} |")
end

send(pid, :stop)

IO.puts("\n## 3. 状態を持たせるとどうなるか\n")
IO.puts("| 状態のリスト長 | 1個あたり |")
IO.puts("|---:|---:|")

for len <- [0, 10, 100, 1_000] do
  state = Enum.to_list(1..len//1)
  {_used, per, _us} = Bench.measure(10_000, fn -> spawn(fn -> Bench.hold(state) end) end)
  IO.puts("| #{Bench.d(len)} | #{Bench.d(per)} B |")
end

IO.puts("\n## 6. メッセージ送受信のコスト\n")

n = 100_000
me = self()

pong =
  spawn(fn ->
    Enum.each(1..n, fn _ ->
      receive do
        {:ping, from} -> send(from, :pong)
      end
    end)
  end)

t0 = System.monotonic_time(:microsecond)

Enum.each(1..n, fn _ ->
  send(pong, {:ping, me})

  receive do
    :pong -> :ok
  end
end)

t1 = System.monotonic_time(:microsecond)

IO.puts("| 往復回数 | 合計 | 1往復あたり |")
IO.puts("|---:|---:|---:|")

IO.puts(
  "| #{Bench.d(n)} | #{Bench.f((t1 - t0) / 1000, 1)} ms | #{Bench.f((t1 - t0) / n)} μs |"
)

IO.puts("\nプロセス上限: #{Bench.d(:erlang.system_info(:process_limit))}")
IO.puts("スケジューラ数: #{:erlang.system_info(:schedulers_online)}")
