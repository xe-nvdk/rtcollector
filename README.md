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

### Core Features
- ⏱️ Collect metrics at configurable intervals with flexible flush timing
- 📦 Modular plugin architecture with easy extension points
- 🚀 Push metrics to RedisTimeSeries with automatic key creation
- ⚙️ Fully YAML-configurable with no code changes needed
- 📚 Built with Python for easy customization and extension
- 💻 Cross-platform support for MacOS and Linux systems
- 🏷️ Label-based metrics with automatic host and component tagging
- 🐞 Debug logging and one-shot execution for testing
- 📦 Memory buffering during Redis downtime with automatic recovery
- 🕒 Per-plugin timing with slow detection and warning indicators

### System Monitoring
- 💻 CPU usage tracking (per-core and total)
- 🧠 Memory usage and availability metrics
- 💾 Disk usage and I/O performance statistics
- 🌐 Network traffic and error monitoring
- 🔄 System load and process statistics

### Application & Service Monitoring
- 🐳 Docker container metrics (CPU, memory, network)
- 🐘 PostgreSQL database statistics, background writer, and replication monitoring
- 🐬 MariaDB/MySQL server metrics with configurable metric selection
- 🔴 Redis server statistics, memory usage, and performance metrics
- 🌐 HTTP/HTTPS endpoint health with response time and certificate monitoring
- 🔌 External command execution for custom metric collection

### Log Collection
- 📥 Syslog server (RFC5424/RFC3164) with structured logging
- 🔍 Log indexing via RedisSearch for powerful querying

### Advanced Features
- ⏳ Human-readable retention settings (e.g., `1d`, `12h`, `1y`)
- 🌐 SOCKS4/SOCKS5 proxy support for Redis connections
- 🔒 Authentication support for database connections
- 📊 Custom query support for database plugins
- 🧩 Multiple output formats for the exec plugin (JSON, metrics)

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
| `postgres`     | ✅     | database stats, background writer metrics, replication lag monitoring  |
| `redis`        | ✅     | Collects server stats, memory usage, CPU, clients, persistence, replication, stats, keyspace, and latency via INFO; fully configurable metrics list |
| `exec`         | ✅     | run external scripts and collect metrics/logs via JSON or plaintext format (`metrics`) |
| `http_response` | ✅     | monitor HTTP/HTTPS endpoints with response time, status code, SSL cert validation |

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
- [x] RedisJSON/RediSearch support for logs
- [ ] Redis Streams support for realtime events
- [x] PostgreSQL input plugin with database stats, background writer metrics, and replication monitoring
- [x] HTTP/HTTPS check plugin for health monitoring
- [ ] Nginx / Apache metrics via status endpoint
- [ ] SNMP input plugin for networking devices
- [ ] JVM metrics via Jolokia
- [ ] Filebeat-compatible input for ingesting logs
- [ ] MQTT input plugin for IoT message ingestion
- [ ] Grafana dashboard templates for RedisTimeSeries

---

## 📦 Example `config.yaml`

```yaml
interval: 10    # Collecting every ten seconds
flush_interval: 60    # Flushing every minute
max_buffer_size: 5000    # Maximum number of entries to buffer if Redis is unavailable
warn_on_buffer: true
hostname: ''
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
  - postgres:
      host: "localhost"
      port: 5432
      user: "postgres"
      password: "yourpassword"
      dbname: "postgres"
      collect_bgwriter: true
      collect_replication: true
      queries:
        - name: "postgres_active_connections"
          sql: "SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active'"
  - exec:
      commands:
        - "python3 /opt/scripts/report_temp.py"
      data_format: "metrics"  # or "json"
      timeout: 5
      ignore_error: false
      working_dir: "/opt/scripts"  # optional working directory
      environment:
        - "ENV_VAR=value"
  - http_response:
      urls:
        - "https://api.example.com/health"
        - "http://localhost:8080/status"
      method: "GET"
      timeout: 5
      follow_redirects: true
      headers:
        User-Agent: "rtcollector"
        Authorization: "Bearer token123"
      response_status_code: 200
      response_string_match: "healthy"
      insecure_skip_verify: false

outputs:
  - redistimeseries:
      host: localhost
      port: 6379
      retention: 1y
  - redissearch:
      host: localhost
      port: 6379
      index: "logs_idx"
      key_prefix: "log:"
```
---

## ✍️ Exec Plugin Formats

The `exec` input plugin supports two output formats from your script:

### `json` format (structured logs + metrics):

```json
{
  "metrics": {
    "cpu_temp": 72.3,
    "disk_used": 81
  },
  "logs": [
    {
      "message": "CPU temp is normal",
      "level": "info"
    }
  ]
}
```

### `metrics` format (line-by-line for RedisTimeSeries):

```
cpu_temp 72.4 source=exec host=atila
disk_usage_percent 84.3 source=exec host=atila ts=1716734400123
```

- Each line includes a metric name, value, optional labels (`key=value`), and optional timestamp (`ts=...` in milliseconds).
---

## 🧰 Configuration Notes

### ⏱️ Collection and Flushing Intervals

- `interval`: Defines how often input plugins are executed (in seconds). Each plugin will collect new metrics on this interval.
- `flush_interval`: (optional) Defines how often buffered data is flushed to output plugins. If not set, it defaults to the same as `interval`.

### 🧵 Buffering Behavior

- If an output (e.g., Redis) becomes unavailable, `rtcollector` will buffer collected metrics and logs in memory.
- The buffer is size-limited via `max_buffer_size` (default: 5000).
- Once the output is available again, buffered data is flushed in the next cycle.
- Buffered metrics and logs are shown in the debug output with a progress bar.

### 🌐 Proxy Support

- Redis outputs support SOCKS5 and SOCKS4 proxying, useful in restricted networks or jump-box scenarios.
- Add a `socks5_proxy` or `socks4_proxy` field under any Redis-based output:

  ```yaml
  outputs:
    - redissearch:
        host: redis.example.com
        port: 6379
        index: "logs_idx"
        key_prefix: "log:"
        # Optional proxy with authentication
        # socks5_proxy: "socks5://user:pass@127.0.0.1:1080"
  ```

- Proxy support is optional and applied only if configured.

### 🌐 HTTP Response Plugin

The HTTP Response input plugin monitors HTTP/HTTPS endpoints and collects metrics about their health and performance:

- **Response Time**: Measures how long requests take to complete
- **Status Code**: Records the HTTP status code returned by the endpoint
- **Content Length**: Tracks the size of the response body
- **String Matching**: Checks if the response contains specific text patterns
- **SSL Certificate**: For HTTPS endpoints, monitors certificate expiration time

Configuration options:
- `urls`: List of URLs to monitor
- `method`: HTTP method to use (GET, POST, etc.)
- `timeout`: Request timeout in seconds
- `follow_redirects`: Whether to follow HTTP redirects
- `headers`: Custom HTTP headers to include in requests
- `body`: Request body for POST/PUT requests
- `response_status_code`: Expected status code to check for
- `response_string_match`: Regex pattern to search for in responses
- `insecure_skip_verify`: Whether to skip SSL certificate validation
- `response_body_field`: If set, stores response bodies in logs with this field name
- `response_body_max_size`: Maximum size of stored response bodies

Example metrics:
- `http_response_response_time`: Time taken to complete the request
- `http_response_status_code`: HTTP status code returned
- `http_response_content_length`: Size of the response in bytes
- `http_response_string_match`: Whether the response matched the expected pattern (1=yes, 0=no)
- `http_response_cert_expiry`: Time until SSL certificate expiration (in seconds)
- `http_response_result_code`: Error code (0=success, 1=timeout, 2=connection error, etc.)

### 🐘 PostgreSQL Plugin

The PostgreSQL input plugin collects metrics from PostgreSQL databases:

- **Database Statistics**: Collects metrics from `pg_stat_database` for each database (connections, transactions, blocks read/hit, etc.)
- **Background Writer**: Monitors checkpoint operations, buffer usage, and write operations from `pg_stat_bgwriter`
- **Replication**: Tracks replication lag in seconds from `pg_stat_replication`

Configuration options:
- `host`, `port`, `user`, `password`, `dbname`: Connection parameters
- `collect_bgwriter`: Enable/disable background writer metrics (default: true)
- `collect_replication`: Enable/disable replication metrics (default: true)
- `queries`: Custom SQL queries to collect additional metrics

Example metrics:
- `postgres_numbackends`: Number of active connections per database
- `postgres_xact_commit`: Committed transactions per database
- `postgres_bgwriter_checkpoints_timed`: Number of scheduled checkpoints
- `postgres_replication_lag_seconds`: Replication lag in seconds per replica

### 📅 Retention Policy

- You can configure the data retention period in a more human-readable format.
- The `retention` field in your config can now use:
  - `"7d"` for 7 days
  - `"12h"` for 12 hours
  - `"1y"` for 1 year
- These values are automatically converted into milliseconds for RedisTimeSeries.
- You can still use raw millisecond values if needed (e.g., `retention: 86400000`).

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
