![rtcollector](https://github.com/user-attachments/assets/89bd14c2-62e0-4e52-aa3f-da44a6012d5a)


# rtcollector

> A modular, RedisTimeSeries-native observability agent.  
> Designed for developers, tinkerers, and infrastructure teams who want full control over metrics collection, without the bloat.

---

## 🧠 What is `rtcollector`?

`rtcollector` is a lightweight, plugin-based agent for collecting system and application metrics, and pushing them to [RedisTimeSeries](https://redis.io/timeseries/).

It works like [Telegraf](https://www.influxdata.com/time-series-platform/telegraf/), but is designed specifically for the Redis Stack ecosystem.

Think of it as your Redis-native observability layer: simple, fast, hackable.

---

## 🤔 Why does it exist?

Because most modern observability agents:
- Are too bloated or overkill for smaller projects or edge deployments
- Assume you're using Prometheus, InfluxDB, or Elastic
- Lack good support for RedisTimeSeries as a first-class output
- Why not?

`rtcollector` was born out of the need for:

✅ Something modular  
✅ Configurable with a YAML file  
✅ Built with RedisStack in mind  
✅ Small enough to embed anywhere (VMs, Docker, homelabs, edge devices)

---

## ✅ What it can do (today)

- ⏱️ Collect metrics at configurable intervals
- 📦 Modular input plugins (Linux CPU, Mem, Disk, etc.)
- 🚀 Push metrics to RedisTimeSeries (via `TS.ADD`)
- ⚙️ Fully YAML-configurable. No code changes needed to enable/disable plugins
- 📚 Built with Python and easy to extend
- 💻 Support for MacOS and Linux
- 🏷️ Label-based key creation with per-host and per-core tags
- 🐞 Debug logging and one-shot execution support
- 🐳 Docker metrics via container stats and engine info
- 📥 Receive and index logs via Syslog input (RFC5424/RFC3164) using RedisSearch
- 🕒 Per-plugin timing with slow detection and warning indicators
- 🐬 Collect metrics from MariaDB servers using `SHOW GLOBAL STATUS`, configurable and with authentication support

---

## 🔌 Inputs (WIP)

| Plugin         | Status | Notes |
|----------------|--------|-------|
| `linux_cpu`    | ✅     | per-core and total CPU usage  
| `linux_mem`    | ✅     | free/used/available RAM  
| `linux_disk`   | ✅     | disk usage by mount  
| `linux_net`    | ✅     | bytes in/out, packet errors  
| `linux_io`     | ✅     | read/write bytes and ops  
| `macos_cpu`    | ✅     | per-core and total CPU usage  
| `macos_mem`    | ✅     | memory usage via `vm_stat`  
| `macos_disk`   | ✅     | disk usage via `df`  
| `macos_io`     | ✅     | I/O stats via `iostat`  
| `macos_net`    | ✅     | net stats via `netstat`  
| `docker_stats` | ✅     | container CPU, memory, and network stats; Docker Swarm toggle via config; added logging improvements and plugin execution duration tracking  
| `syslog`       | ✅     | receive and parse RFC5424/RFC3164 logs over TCP/UDP; supports JSON output via RedisSearch |
| `mariadb`      | ✅     | collects server stats via `SHOW GLOBAL STATUS`; supports configurable metrics and basic auth  |
| `postgres`     | 🧪     | connections, xact commits  |
| `redis`        | ✅     | Collects server stats, memory usage, CPU, clients, persistence, replication, stats, keyspace, and latency via INFO; fully configurable metrics list |

---

## 📤 Outputs

| Plugin            | Notes |
|-------------------|-------|
| `redistimeseries` | ✅ Default and most stable output; supports automatic key creation with retention policies and labels; supports dynamic hostname tagging and duplicate policy handling |
| `redissearch`     | ✅ Used for structured log ingestion (e.g., syslog); stores JSON documents in Redis and indexes fields like severity, appname, and message for querying via RediSearch |
| (Planned) `stdout`| for testing/debugging locally |
| (Planned) `clickhouse` | push metrics to cold storage / analytics engine |
| (Planned) `mqtt` / `http_post` | to integrate with IoT or alerting systems |

---

## 🚀 Roadmap

- [x] Plugin-based architecture
- [x] YAML-based config loader
- [x] Add default input suite (system, docker, databases)
- [x] Add CLI (`rtcollector run --config config.yaml`)
- [x] Debug and once mode
- [x] macOS support
- [x] Docker Support
- [ ] Add plugin schema validation + logging
- [x] RedisJSON/RediSearch support for logs
- [ ] Redis Streams support for realtime events
- [ ] Grafana dashboard templates for RedisTimeSeries

---

## 📦 Example `config.yaml`

```yaml
interval: 5
hostname: atila
retention: 86400000
debug: true
once: false

inputs:
  - linux_cpu
  - linux_mem
  - docker:
      endpoint: "unix:///var/run/docker.sock"
      gather_services: false
  - syslog:
        server: "tcp://127.0.0.1:5514"
        tls_cert: ""
        tls_key: ""
        socket_mode: ""
        max_connections: 0
        read_timeout: 0
        read_buffer_size: "64KiB"
        keep_alive_period: "5m"
        content_encoding: "identity"
        max_decompression_size: "500MB"
        framing: "octet-counting"
        trailer: "LF"
        best_effort: false
        syslog_standard: "RFC5424"
        sdparam_separator: "_"
  - redis:
      host: "localhost"
      port: 6379
      db: 0
      metrics:
        - used_memory
        - total_system_memory
        - connected_clients
        - blocked_clients
        - total_commands_processed
        - expired_keys
        - evicted_keys
        - instantaneous_ops_per_sec
        - keyspace_hits
        - keyspace_misses
        - used_cpu_sys
        - used_cpu_user
        - mem_fragmentation_ratio
        - connected_slaves
        - aof_enabled
        - rdb_last_bgsave_status
        - role
        - uptime_in_seconds
        - total_connections_received
  - mariadb:
      host: "localhost"
      port: 3306
      auth:
        user: "monitor"
        password: "yourpassword"
      metrics:
        - Threads_connected
        - Connections
        - Uptime
        - Questions

outputs:
  - redistimeseries:
      host: localhost
      port: 6379
  - redissearch:
      host: localhost
      port: 6379
      index: "logs_idx"
      key_prefix: "log:"
```
---

## 👥 Who is this for?

- DevOps engineers running Redis Stack
- Homelab enthusiasts
- IoT builders using RedisTimeSeries
- Anyone who wants a custom, no-bloat collector for metrics

---

## ❤️ Contributing

This project is just getting started, contributions, ideas, and PRs are more than welcome!

To get started:

1. Fork this repo
2. Clone your fork
3. Create a branch (`git checkout -b my-feature`)
4. Commit your changes (`git commit -am 'Add feature'`)
5. Push to the branch (`git push origin my-feature`)
6. Open a pull request

---

## 📜 License

This project is licensed under the [GNU Affero General Public License v3.0 (AGPL-3.0)](https://www.gnu.org/licenses/agpl-3.0.html).

You are free to use, modify, and distribute this code , as long as you open source any changes and make your source code available if you deploy a modified version as a network service.
