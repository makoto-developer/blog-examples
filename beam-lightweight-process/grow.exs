# プロセス側にメモリ上限を置く（第7.4節）
#
#   docker run --rm -m 512m --memory-swap=512m -v "$PWD":/w -w /w \
#     elixir:1.19-otp-28-slim sh -c 'elixir grow.exs none; echo "exit=$?"'
#
# 引数: none | heap | binary | shared
#   none   上限なし・ヒープを積む        → VM ごと OOM killer に殺される
#   heap   200MB上限・ヒープを積む        → そのプロセスだけ死ぬ
#   binary 200MB上限・4MBバイナリを積む   → 素通りして VM ごと死ぬ
#   shared 上限に include_shared_binaries → そのプロセスだけ死ぬ

defmodule Grow do
  @limit_words 25_000_000  # ワード単位。64bit なので約 200MB

  # 報告の間隔。shared は止まる位置を細かく見たいので STEP=5 などで縮める
  defp step, do: String.to_integer(System.get_env("STEP") || "25")

  def run(mode) do
    parent = self()

    pid =
      spawn(fn ->
        case mode do
          "heap" ->
            Process.flag(:max_heap_size, %{size: @limit_words, kill: true, error_logger: true})

          "binary" ->
            Process.flag(:max_heap_size, %{size: @limit_words, kill: true, error_logger: true})

          "shared" ->
            Process.flag(:max_heap_size, %{
              size: @limit_words,
              kill: true,
              error_logger: true,
              include_shared_binaries: true
            })

          _ ->
            :ok
        end

        send(parent, :ready)
        loop(mode, [], 0)
      end)

    ref = Process.monitor(pid)
    receive do: (:ready -> :ok)

    receive do
      {:DOWN, ^ref, :process, _, reason} ->
        IO.puts("プロセスの終了理由: #{inspect(reason)}")
        Process.sleep(300)
        IO.puts("VM は生存。total=#{mb(:erlang.memory(:total))} MB")
    after
      60_000 -> IO.puts("60秒たっても死ななかった")
    end
  end

  # ヒープ側を積む: 大きなリストを持ち続ける
  defp loop("none", acc, i), do: grow_heap(acc, i, "none")
  defp loop("heap", acc, i), do: grow_heap(acc, i, "heap")
  # バイナリ側を積む: 64バイト超は参照カウント方式でヒープ外に置かれる
  defp loop(_, acc, i), do: grow_bin(acc, i)

  defp grow_heap(acc, i, mode) do
    acc = [Enum.to_list(1..50_000) | acc]
    if rem(i, step()) == 0, do: report(i, mode)
    grow_heap(acc, i + 1, mode)
  end

  defp grow_bin(acc, i) do
    acc = [:binary.copy(<<0>>, 4_000_000) | acc]
    if rem(i, step()) == 0, do: report(i, "binary")
    grow_bin(acc, i + 1)
  end

  defp report(i, _mode) do
    heap = Process.info(self(), :total_heap_size) |> elem(1)
    IO.puts("| #{i} | #{mb(:erlang.memory(:total))} MB | #{mb(heap * 8)} MB |")
  end

  def mb(b), do: :erlang.float_to_binary(b / 1_048_576, decimals: 0)
end

mode = List.first(System.argv()) || "none"
IO.puts("mode=#{mode}")
IO.puts("| 回数 | VM の総メモリ | そのプロセスのヒープ |")
IO.puts("|---:|---:|---:|")
Grow.run(mode)
