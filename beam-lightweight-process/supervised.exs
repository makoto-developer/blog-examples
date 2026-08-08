# 暴走するワーカーを監視ツリーの下に置く（第7.5節）
#
#   docker run --rm -m 512m --memory-swap=512m -v "$PWD":/w -w /w \
#     elixir:1.19-otp-28-slim sh -c 'elixir supervised.exs; echo "exit=$?"'
#
# max_heap_size でワーカーだけが死に、隣の heartbeat は動き続ける。
# ただし原因が続くと再起動枠を使い切って Supervisor が VM を終了させる。

defmodule Hog do
  def start_link(_) do
    {:ok, spawn_link(&run/0)}
  end

  def child_spec(_) do
    %{id: __MODULE__, start: {__MODULE__, :start_link, [[]]}, restart: :permanent}
  end

  def run do
    Process.flag(:max_heap_size, %{size: 25_000_000, kill: true, error_logger: false})
    IO.puts("[hog] 起動 pid=#{inspect(self())}")
    grow([])
  end

  defp grow(acc), do: grow([Enum.to_list(1..50_000) | acc])
end

defmodule Heartbeat do
  def start_link(_), do: {:ok, spawn_link(fn -> beat(0) end)}

  def child_spec(_) do
    %{id: __MODULE__, start: {__MODULE__, :start_link, [[]]}, restart: :permanent}
  end

  defp beat(i) do
    mb = :erlang.float_to_binary(:erlang.memory(:total) / 1_048_576, decimals: 0)
    IO.puts("[heartbeat] #{i} 回目 / VM total=#{mb} MB")
    Process.sleep(50)
    beat(i + 1)
  end
end

children = [Hog, Heartbeat]
{:ok, sup} = Supervisor.start_link(children, strategy: :one_for_one, max_restarts: 3, max_seconds: 60)
Process.sleep(60_000)
IO.puts("60秒たっても Supervisor は生きていた: #{inspect(sup)}")
