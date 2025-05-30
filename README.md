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
- 💻 Cross-platform support for Windows, MacOS, and Linux systems
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
| `linux_net`    | ✅     | bytes in/out, packet errors, configurable interface filtering  
| `linux_io`     | ✅     | read/write bytes and ops  
| `macos_cpu`    | ✅     | per-core and total CPU usage  
| `macos_mem`    | ✅     | memory usage via `vm_stat`  
| `macos_disk`   | ✅     | disk usage via `df`  
| `macos_io`     | ✅     | I/O stats via `iostat`  
| `macos_net`    | ✅     | net stats via `netstat`  
| `docker_stats` | ✅     | container CPU, memory, and network stats; Docker Swarm toggle via config; added logging improvements and plugin execution duration tracking  
| `syslog`       | ✅     | receive and parse RFC5424/RFC3164 logs over TCP/UDP; supports JSON output via RedisSearch |
| `mariadb`      | ✅     | collects server stats via `SHOW GLOBAL STATUS`; supports configurable metrics with direct authentication parameters  |
| `postgres`     | ✅     | database stats, background writer metrics, replication lag monitoring  |
| `redis`        | ✅     | Collects server stats, memory usage, CPU, clients, persistence, replication, stats, keyspace, and latency via INFO; supports ACL user authentication, password authentication, and SSL/TLS encrypted connections |
| `exec`         | ✅     | run external scripts and collect metrics/logs via JSON or plaintext format (`metrics`) |
| `http_response` | ✅     | monitor HTTP/HTTPS endpoints with response time, status code, SSL cert validation |
| `windows_cpu`   | ✅     | CPU usage metrics for Windows systems |
| `windows_mem`   | ✅     | memory usage metrics for Windows systems |
| `windows_disk`  | ✅     | disk usage and I/O metrics for Windows systems |
| `windows_net`   | ✅     | network interface metrics for Windows systems |
| `nginx`        | ✅     | server connections, requests, and connection states |
| `apache`       | ✅     | server status, worker metrics, and request statistics |
| `system`       | ✅     | system load averages, uptime, number of users, and CPU count |
| `processes`    | ✅     | process counts, threads, and states (running, sleeping, zombie) |
| `kernel`      | ✅     | kernel metrics including boot time, context switches, interrupts, and pressure stall information |
| `netstat`     | ✅     | TCP connection states (established, time_wait, close_wait, etc.) for IPv4 and IPv6 |
| `nstat`       | ✅     | Network statistics from /proc/net/snmp including IP, TCP, UDP, and ICMP error counters |
| `linux_swap`   | ✅     | Swap usage and I/O metrics (total, free, used, in/out bytes) |
| `internal`     | ✅     | Internal metrics about rtcollector itself (memory usage, metrics gathered/written, plugin performance) |

---

## 📤 Outputs

| Plugin            | Notes |
|-------------------|-------|
| `redistimeseries` | ✅ Default and most stable output; supports automatic key creation with retention policies and labels; supports dynamic hostname tagging, duplicate policy handling, ACL user authentication, password authentication, and SSL/TLS encrypted connections |
| `redissearch`     | ✅ Used for structured log ingestion (e.g., syslog); stores JSON documents in Redis and indexes fields like severity, appname, and message for querying via RediSearch; supports ACL user authentication, password authentication, and SSL/TLS encrypted connections |
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
- [x] Windows support
- [x] Docker Support
- [x] RedisJSON/RediSearch support for logs
- [x] Standardized configuration for database plugins
- [ ] Redis Streams support for realtime events
- [x] PostgreSQL input plugin with database stats, background writer metrics, and replication monitoring
- [x] HTTP/HTTPS check plugin for health monitoring
- [x] Nginx / Apache metrics via status endpoint
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
  # Use appropriate system plugins based on your OS
  - system       # Cross-platform system metrics (load, uptime, users)
  - linux_cpu    # For Linux systems
  - linux_mem    # For Linux systems
  # - windows_cpu  # For Windows systems
  # - windows_mem  # For Windows systems
  # - windows_disk # For Windows systems
  # - windows_net  # For Windows systems
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
  - nginx:
      status_url: "http://localhost/nginx_status"
      timeout: 5  # seconds
  - apache:
      status_url: "http://localhost/server-status?auto"
      timeout: 5

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

## 🛠️ Utility Functions

rtcollector includes various utility functions to help with common tasks across plugins:

- **[Rate Calculation](utils/README.md)**: Automatically calculate per-second rates from counter metrics (compensating for Redis TimeSeries' lack of non_negative_derivative functionality)
- **System Information**: Get hostname and other system details
- **Metric Formatting**: Create consistent metric names and labels

See the [utils/README.md](utils/README.md) for more details on available utilities.

## 🧰 Configuration Notes

### 🔑 Authentication Parameters

- All input plugins requiring authentication (like `mariadb`, `redis`, `postgres`) now use direct authentication parameters at the root level of their configuration.
- For example, MariaDB and Redis use `user` and `password` directly in their configuration block, not in a nested `auth` object.
- This simplifies configuration and makes it more consistent across plugins.

### 🔒 Redis Authentication Options

rtcollector supports three authentication methods for Redis connections:

1. **Password Authentication**:
   ```yaml
   - redistimeseries:
       host: redis.example.com
       port: 6379
       password: "your-redis-password"
   ```

2. **ACL User Authentication** (Redis 6.0+):
   ```yaml
   - redistimeseries:
       host: redis.example.com
       port: 6379
       username: "metrics_user"
       password: "user-specific-password"
   ```

3. **SSL/TLS Authentication**:
   ```yaml
   - redistimeseries:
       host: redis.example.com
       port: 6379
       ssl: true
       ssl_ca_certs: "/path/to/ca.pem"
       ssl_certfile: "/path/to/cert.pem"
       ssl_keyfile: "/path/to/key.pem"
   ```

These methods can be combined for enhanced security. All Redis-related components (inputs and outputs) support these authentication options.

### 🔐 Secret Management

rtcollector supports secure credential management through secret providers. This allows you to keep sensitive information like passwords out of your configuration files.

#### Secret Reference Syntax

In your config.yml, you can reference secrets using the `secret:` prefix:

```yaml
outputs:
  - redistimeseries:
      host: redis.example.com
      port: 6379
      password: "secret:redis/password"  # Reference to a secret
```

#### Secret Providers

rtcollector supports multiple secret providers:

1. **Environment Variables** (default)
   ```yaml
   secret_store:
     type: env
     prefix: SECRET_  # Optional, default is SECRET_
   ```
   
   Secrets are stored in environment variables with the format `SECRET_REDIS_PASSWORD` (slashes in the secret ID are converted to underscores).

2. **HashiCorp Vault**
   ```yaml
   secret_store:
     type: vault
     url: http://vault:8200        # Optional, defaults to VAULT_ADDR env var
     path_prefix: rtcollector      # Optional, defaults to "rtcollector"
   ```
   
   Vault authentication uses the `VAULT_TOKEN` environment variable by default. Secrets are stored in Vault's KV store at `rtcollector/redis/password`.

#### Installation

For Vault support, install the optional dependency:
```
pip install hvac
```

### 🔧 Redis TimeSeries Configuration

When using Redis with authentication via a custom configuration file, make sure to set the appropriate duplicate policy for TimeSeries:

```
# TimeSeries configuration
ts-duplicate-policy LAST
```

This setting is crucial for rtcollector to function properly, as it allows updating existing time series data points. Without this setting, you may encounter errors like:

```
TSDB: Error at upsert, update is not supported when DUPLICATE_POLICY is set to BLOCK mode
```

Example redis.conf with authentication and proper TimeSeries configuration:

```
# Password authentication
requirepass your_password

# ACL configuration
user default off
user rtcollector on >your_password ~* +@all

# Load modules
loadmodule /usr/local/lib/redis/modules/redisearch.so
loadmodule /usr/local/lib/redis/modules/redistimeseries.so
loadmodule /usr/local/lib/redis/modules/rejson.so

# TimeSeries configuration
ts-duplicate-policy LAST
```

### 📊 Redis TimeSeries Data Format

rtcollector stores metrics in Redis TimeSeries using the following format:

```
metric_name timestamp value LABELS label1 value1 label2 value2
```

For example:
```
net_rx_bytes_eth0 1748552776684 1024.0 LABELS host atila iface eth0
```

Breaking it down:
```
net_rx_bytes_eth0 1748552776684 1024.0 LABELS host atila iface eth0
|---------------| |------------| |---| |-----||----||----||----||----|
      name         timestamp    value    label  val  label  val
```

This maps to the Redis TimeSeries command:
```
TS.ADD net_rx_bytes_eth0 1748552776684 1024.0 LABELS host atila iface eth0
```

When querying this data in Redis:
```
127.0.0.1:6379> TS.RANGE net_rx_bytes_eth0 1748552776684 1748552776684
1) 1) (integer) 1748552776684
   2) "1024"
```

The metadata (labels) can be viewed with:
```
127.0.0.1:6379> TS.INFO net_rx_bytes_eth0
```

This format differs from other time series databases like InfluxDB, which uses a line protocol format like:
```
measurement,tag1=value1,tag2=value2 field1=value1,field2=value2 timestamp
```

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

### 🌐 Linux Network Plugin

The Linux Network input plugin collects metrics about network interfaces:

- **Network Traffic**: Bytes and packets sent/received per interface
- **Network Errors**: Error and drop counts for each interface
- **Rate Metrics**: Per-second rates for all counter metrics
- **Bits/Second Metrics**: Network traffic in bits per second for bandwidth monitoring
- **Interface Discovery**: Automatic discovery of network interfaces for dashboard variables

Configuration options:
```yaml
inputs:
  - linux_net:
      exclude_patterns:
        - "veth"
        - "docker"
        - "^br-"
      include_patterns: []
      exclude_interfaces: []
      include_interfaces:
        - "wlp0s20f3"  # Always include this interface
```

- `exclude_patterns`: List of regex patterns for interfaces to exclude
- `include_patterns`: List of regex patterns for interfaces to include (overrides exclusions)
- `exclude_interfaces`: List of specific interface names to exclude
- `include_interfaces`: List of specific interface names to include (overrides exclusions)

Example metrics:
- `net_rx_bytes`: Total bytes received on an interface
- `net_tx_bytes`: Total bytes sent on an interface
- `net_rx_bytes_rate`: Bytes received per second
- `net_tx_bytes_rate`: Bytes sent per second
- `net_rx_bytes_bits_rate`: Bits received per second (for bandwidth monitoring)
- `net_tx_bytes_bits_rate`: Bits sent per second (for bandwidth monitoring)
- `net_rx_packets`: Total packets received
- `net_tx_packets`: Total packets sent
- `net_rx_errs`: Receive errors
- `net_tx_errs`: Transmit errors
- `net_rx_drop`: Dropped incoming packets
- `net_tx_drop`: Dropped outgoing packets

Interface-specific metrics are also available with the interface name in the key:
- `net_rx_bytes_rate_eth0`: Bytes received per second on eth0
- `net_tx_bytes_bits_rate_eth0`: Bits sent per second on eth0

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

### 🔄 Processes Plugin

The Processes input plugin collects metrics about system processes:

- **Process Counts**: Total number of processes on the system
- **Thread Counts**: Total number of threads across all processes
- **Process States**: Counts of processes in different states (running, sleeping, zombie, blocked, etc.)

Configuration options:
- Simply add the plugin to your config to enable it:
  ```yaml
  inputs:
    - processes
  ```

Example metrics:
- `processes_total`: Total number of processes
- `processes_total_threads`: Total number of threads
- `processes_running`: Number of running processes
- `processes_sleeping`: Number of sleeping processes
- `processes_zombie`: Number of zombie processes
- `processes_blocked`: Number of processes in uninterruptible sleep (Linux)
- `processes_stopped`: Number of stopped processes
- `processes_dead`: Number of dead processes (Linux)
- `processes_paging`: Number of paging processes (Linux)
- `processes_parked`: Number of parked processes (Linux 4+)
- `processes_idle`: Number of idle processes (BSD/Linux 4+)

Implementation:
- Uses native OS interfaces (/proc filesystem on Linux, ps command on macOS, wmic on Windows)
- No external dependencies required

### 📊 Network Statistics (nstat) Plugin

The Network Statistics input plugin collects metrics from `/proc/net/snmp` and `/proc/net/snmp6`:

- **IP Statistics**: IPv4 packet counts, errors, and discards
- **TCP Statistics**: Connection statistics, segment counts, and errors
- **UDP Statistics**: Datagram counts and errors
- **ICMP Statistics**: Message counts and errors

Configuration options:
- Simply add the plugin to your config to enable it:
  ```yaml
  inputs:
    - nstat
  ```

Example metrics:
- **IPv4 Metrics**:
  - `nstat_ip_InReceives`: Total number of received packets
  - `nstat_ip_InDiscards`: Number of received packets discarded
  - `nstat_ip_InHdrErrors`: Number of packets discarded due to header errors
  - `nstat_ip_InAddrErrors`: Number of packets discarded due to address errors
  - `nstat_ip_OutNoRoutes`: Number of packets discarded due to no route
  - `nstat_ip_InUnknownProtos`: Number of packets discarded due to unknown protocol
  - `nstat_ip_InDiscards_rate`: Rate of discarded packets per second
  - `nstat_ip_OutDiscards_rate`: Rate of outgoing discarded packets per second

- **IPv6 Metrics**:
  - `nstat_ip6_InReceives`: Total number of IPv6 packets received
  - `nstat_ip6_InDiscards`: Number of IPv6 packets discarded on input
  - `nstat_ip6_InHdrErrors`: Number of IPv6 packets with header errors
  - `nstat_ip6_InAddrErrors`: Number of IPv6 packets with address errors
  - `nstat_ip6_OutDiscards`: Number of IPv6 packets discarded on output
  - `nstat_ip6_InUnknownProtos`: Number of IPv6 packets with unknown protocol
  - `nstat_ip6_InDiscards_rate`: Rate of IPv6 discarded packets per second
  - `nstat_ip6_OutDiscards_rate`: Rate of IPv6 outgoing discarded packets per second

- **TCP Metrics**:
  - `nstat_tcp_ActiveOpens`: Number of active opens
  - `nstat_tcp_PassiveOpens`: Number of passive opens
  - `nstat_tcp_AttemptFails`: Number of failed connection attempts
  - `nstat_tcp_EstabResets`: Number of connection resets
  - `nstat_tcp_RetransSegs`: Number of retransmitted segments
  - `nstat_tcp_RetransSegs_rate`: Rate of retransmitted segments per second

- **UDP Metrics**:
  - `nstat_udp_InDatagrams`: Number of received datagrams
  - `nstat_udp_NoPorts`: Number of received datagrams with no application at the port
  - `nstat_udp_InErrors`: Number of received datagrams with errors
  - `nstat_udp_OutDatagrams`: Number of sent datagrams
  - `nstat_udp_InDatagrams_rate`: Rate of received datagrams per second
  - `nstat_udp_OutDatagrams_rate`: Rate of sent datagrams per second

- **ICMP Metrics**:
  - `nstat_icmp_InMsgs`: Number of received ICMP messages
  - `nstat_icmp_OutMsgs`: Number of sent ICMP messages
  - `nstat_icmp_InErrors`: Number of received ICMP messages with errors
  - `nstat_icmp_OutErrors`: Number of ICMP messages not sent due to errors
  - `nstat_icmp_InMsgs_rate`: Rate of received ICMP messages per second
  - `nstat_icmp_OutMsgs_rate`: Rate of sent ICMP messages per second

Requirements:
- Linux operating system with `/proc/net/snmp` and optionally `/proc/net/snmp6` files

### 🌐 Netstat Plugin

The Netstat input plugin collects TCP connection state metrics and TCP statistics:

- **TCP Connection States**: Counts of connections in each state (ESTABLISHED, TIME_WAIT, CLOSE_WAIT, etc.)
- **IPv4 and IPv6**: Collects metrics from both IPv4 and IPv6 connections
- **TCP Handshake Metrics**: Active/passive opens, connection failures, resets
- **TCP Performance Metrics**: Retransmissions, errors, and other TCP statistics
- **Rate Calculations**: Per-second rates for counter metrics (with `_rate` suffix)

Configuration options:
- Simply add the plugin to your config to enable it:
  ```yaml
  inputs:
    - netstat
  ```

Example metrics:
- **Connection States**:
  - `tcp_established`: Number of connections in ESTABLISHED state
  - `tcp_time_wait`: Number of connections in TIME_WAIT state
  - `tcp_close_wait`: Number of connections in CLOSE_WAIT state
  - `tcp_syn_sent`: Number of connections in SYN_SENT state
  - `tcp_syn_recv`: Number of connections in SYN_RECV state
  - `tcp_fin_wait1`: Number of connections in FIN_WAIT1 state
  - `tcp_fin_wait2`: Number of connections in FIN_WAIT2 state
  - `tcp_close`: Number of connections in CLOSE state
  - `tcp_last_ack`: Number of connections in LAST_ACK state
  - `tcp_listen`: Number of connections in LISTEN state
  - `tcp_closing`: Number of connections in CLOSING state

- **TCP Statistics**:
  - `tcp_active_opens`: Total number of active connection openings since boot
  - `tcp_active_opens_rate`: Active connection openings per second
  - `tcp_passive_opens`: Total number of passive connection openings since boot
  - `tcp_passive_opens_rate`: Passive connection openings per second
  - `tcp_attempt_fails`: Total number of failed connection attempts since boot
  - `tcp_attempt_fails_rate`: Failed connection attempts per second
  - `tcp_estab_resets`: Total number of connection resets received since boot
  - `tcp_estab_resets_rate`: Connection resets received per second
  - `tcp_curr_estab`: Current number of connections in ESTABLISHED or CLOSE_WAIT state
  - `tcp_in_segs`: Total number of segments received since boot
  - `tcp_in_segs_rate`: Segments received per second
  - `tcp_out_segs`: Total number of segments sent since boot
  - `tcp_out_segs_rate`: Segments sent per second
  - `tcp_retrans_segs`: Total number of segments retransmitted since boot
  - `tcp_retrans_segs_rate`: Segments retransmitted per second
  - `tcp_in_errs`: Total number of bad segments received since boot
  - `tcp_in_errs_rate`: Bad segments received per second
  - `tcp_out_rsts`: Total number of resets sent since boot
  - `tcp_out_rsts_rate`: Resets sent per second
  - `tcp_syn_retrans`: Total number of SYN retransmissions since boot
  - `tcp_syn_retrans_rate`: SYN retransmissions per second

- **TCP Handshake and Advanced Metrics**:
  - `tcp_syncookies_sent`: Number of SYN cookies sent
  - `tcp_syncookies_recv`: Number of SYN cookies received
  - `tcp_syncookies_failed`: Number of invalid SYN cookies received
  - `tcp_embryonic_rsts`: Number of resets received for embryonic SYN_RECV sockets
  - `tcp_listen_overflows`: Number of times the listen queue overflowed
  - `tcp_listen_drops`: Number of SYNs to LISTEN sockets dropped
  - And many more detailed TCP metrics

Requirements:
- Linux operating system with /proc/net/tcp, /proc/net/tcp6, /proc/net/snmp, and /proc/net/netstat files

### 🧠 Kernel Plugin

The Kernel input plugin collects metrics about the Linux kernel:

- **Core Metrics**: Boot time, context switches, interrupts, processes forked
- **Memory Management**: Disk pages in/out, entropy available
- **KSM (Kernel Samepage Merging)**: Various KSM metrics if available
- **PSI (Pressure Stall Information)**: CPU, memory, and I/O pressure metrics

Configuration options:
- Simply add the plugin to your config to enable it:
  ```yaml
  inputs:
    - kernel
  ```

Example metrics:
- `kernel_boot_time`: System boot time in seconds since epoch
- `kernel_context_switches`: Total number of context switches since boot
- `kernel_context_switches_rate`: Context switches per second
- `kernel_interrupts`: Total number of interrupts since boot
- `kernel_interrupts_rate`: Interrupts per second
- `kernel_processes_forked`: Total number of processes forked since boot
- `kernel_processes_forked_rate`: Processes forked per second
- `kernel_disk_pages_in`: Total number of disk pages paged in since boot
- `kernel_disk_pages_in_rate`: Disk pages paged in per second
- `kernel_disk_pages_out`: Total number of disk pages paged out since boot
- `kernel_disk_pages_out_rate`: Disk pages paged out per second
- `kernel_entropy_avail`: Available entropy
- `kernel_pressure_avg10`, `kernel_pressure_avg60`, `kernel_pressure_avg300`: Pressure metrics for CPU, memory, and I/O
- `kernel_fd_allocated`: Number of allocated file descriptors
- `kernel_fd_used`: Number of used file descriptors
- `kernel_fd_max`: Maximum number of file descriptors allowed
- `kernel_fd_used_percent`: Percentage of file descriptors used

Requirements:
- Linux operating system

### 💾 Linux Swap Plugin

The Linux Swap input plugin collects swap usage and I/O metrics:

- **Swap Usage**: Total, free, and used swap space
- **Swap I/O**: Bytes swapped in and out of swap space
- **Rate Metrics**: Per-second rates for swap I/O

Configuration options:
- Simply add the plugin to your config to enable it:
  ```yaml
  inputs:
    - linux_swap
  ```

Example metrics:
- **Swap Usage**:
  - `swap_total`: Total swap space in bytes
  - `swap_free`: Free swap space in bytes
  - `swap_used`: Used swap space in bytes
  - `swap_used_percent`: Percentage of swap used

- **Swap I/O**:
  - `swap_in`: Total bytes swapped in since boot
  - `swap_out`: Total bytes swapped out since boot
  - `swap_in_rate`: Bytes swapped in per second
  - `swap_out_rate`: Bytes swapped out per second

Requirements:
- Linux operating system with `/proc/meminfo` and `/proc/vmstat` files

### 🖥️ System Plugin

The System input plugin collects general system metrics:

- **Load Averages**: 1, 5, and 15-minute load averages
- **Users**: Number of logged-in users and unique users
- **CPUs**: Number of CPU cores/processors
- **Uptime**: System uptime in seconds

### 📊 Internal Plugin

The Internal input plugin collects metrics about rtcollector itself:

- **Memory Stats**: Memory usage and garbage collection metrics
- **Agent Stats**: Overall collector statistics (metrics gathered, written, dropped, errors)
- **Gather Stats**: Per-plugin collection statistics (gather time, metrics gathered)
- **Write Stats**: Per-plugin output statistics (write time, metrics written/dropped)

Configuration options:
- The plugin is automatically added to your inputs list when rtcollector starts
- No additional configuration is needed

Example metrics:
- **Memory Stats**:
  - `internal_memstats_sys_bytes`: Total memory used by the process
  - `internal_memstats_heap_alloc_bytes`: Memory allocated on the heap
  - `internal_memstats_num_gc`: Number of garbage collections performed

- **Agent Stats**:
  - `internal_agent_metrics_gathered`: Total number of metrics collected
  - `internal_agent_metrics_written`: Total number of metrics written to outputs
  - `internal_agent_metrics_dropped`: Total number of metrics dropped
  - `internal_agent_gather_errors`: Total number of collection errors
  - `internal_agent_metrics_gathered_rate`: Rate of metrics collected per second
  - `internal_agent_metrics_written_rate`: Rate of metrics written per second
  - `internal_agent_gather_errors_rate`: Rate of collection errors per second

- **Gather Stats** (per input plugin):
  - `internal_gather_gather_time_ns`: Time taken to collect metrics (nanoseconds)
  - `internal_gather_metrics_gathered`: Number of metrics collected by this plugin
  - `internal_gather_gather_time_ns_rate`: Rate of collection time per second

- **Write Stats** (per output plugin):
  - `internal_write_write_time_ns`: Time taken to write metrics (nanoseconds)
  - `internal_write_metrics_written`: Number of metrics written by this plugin
  - `internal_write_metrics_dropped`: Number of metrics dropped by this plugin
  - `internal_write_buffer_size`: Current buffer size for this plugin
  - `internal_write_buffer_limit`: Maximum buffer size for this plugin
  - `internal_write_write_time_ns_rate`: Rate of write time per second
  - `internal_write_metrics_written_rate`: Rate of metrics written per second

These metrics are useful for monitoring the performance and health of rtcollector itself, similar to Telegraf's internal metrics.

Configuration options:
- Simply add the plugin to your config to enable it:
  ```yaml
  inputs:
    - system
  ```

Example metrics:
- `system_load1`, `system_load5`, `system_load15`: System load averages
- `system_n_users`: Number of logged-in users
- `system_n_unique_users`: Number of unique logged-in users
- `system_n_cpus`: Number of CPU cores
- `system_uptime`: System uptime in seconds

### 🪟 Windows Metrics Plugins

The Windows input plugins collect system metrics on Windows platforms:

- **CPU Usage**: Per-core and total CPU utilization, user/system time, and interrupt time
- **Memory**: Physical and virtual memory usage, including swap metrics
- **Disk**: Disk space usage by volume and I/O performance statistics
- **Network**: Interface traffic, packet counts, errors, and connection states

Configuration options:
- Simply add the plugins to your config to enable them:
  ```yaml
  inputs:
    - windows_cpu
    - windows_mem
    - windows_disk
    - windows_net
  ```

Requirements:
- Windows operating system
- Python 3.7+ with psutil library installed

Example metrics:
- `windows_cpu_percent`: CPU utilization percentage per core
- `windows_mem_available`: Available physical memory in bytes
- `windows_disk_percent`: Disk usage percentage by volume
- `windows_net_bytes_sent`: Network bytes sent by interface

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
