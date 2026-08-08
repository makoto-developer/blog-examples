# コンテナの CPU 制限を BEAM が認識するか（第7.1節）
IO.puts("schedulers_online=#{:erlang.system_info(:schedulers_online)} " <>
        "schedulers=#{:erlang.system_info(:schedulers)} " <>
        "logical_processors=#{:erlang.system_info(:logical_processors)}")
