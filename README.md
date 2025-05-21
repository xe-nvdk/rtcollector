![rtcollector](https://github.com/user-attachments/assets/ff1ffbd4-4df1-4fd1-a540-5065d4a552f3)


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

---

## 🔌 Inputs (WIP)

| Plugin        | Status  | Notes |
|---------------|---------|-------|
| `linux_cpu`   | ✅      | per-core and total CPU usage  
| `linux_mem`   | 🛠️      | free/used/available RAM  
| `linux_disk`  | 🛠️      | disk usage by mount  
| `linux_net`   | 🛠️      | bytes in/out, packet errors  
| `docker_stats`| 🧪      | container-level CPU, mem, net  
| `mysql`       | 🧪      | basic server stats via `SHOW STATUS`  
| `postgres`    | 🧪      | connections, xact commits  
| `redis`       | 🧪      | `INFO` command + optional latency info  

---

## 📤 Outputs

| Plugin            | Notes |
|-------------------|-------|
| `redistimeseries` | ✅ Default output, pipelines metrics using `TS.ADD` |
| (Planned) `stdout`| for testing/debugging locally |
| (Planned) `clickhouse` | push metrics to cold storage / analytics engine |
| (Planned) `mqtt` / `http_post` | to integrate with IoT or alerting systems |

---

## 🚀 Roadmap

- [x] Plugin-based architecture
- [x] YAML-based config loader
- [ ] Add default input suite (system, docker, databases)
- [ ] Add plugin schema validation + logging
- [ ] Add CLI (`rtcollector run --config config.yaml`)
- [ ] RedisJSON/RediSearch support for logs
- [ ] Redis Streams support for realtime events
- [ ] Alerting module (thresholds, filters, webhooks)
- [ ] Grafana dashboard templates for RedisTimeSeries

---

## 📦 Example `config.yaml`

```yaml
interval: 5

inputs:
  - linux_cpu
  - linux_mem

outputs:
  - redistimeseries:
      host: localhost
      port: 6379
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
