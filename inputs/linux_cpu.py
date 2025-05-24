import time
import socket
from core.metric import Metric

_last_cpu_times = {}

def _read_proc_stat():
    cpu_stats = {}
    with open("/proc/stat", "r") as f:
        for line in f:
            if not line.startswith("cpu"):
                continue
            parts = line.strip().split()
            cpu_id = parts[0]  # e.g., 'cpu', 'cpu0', 'cpu1'
            values = list(map(int, parts[1:]))
            cpu_stats[cpu_id] = values
    return cpu_stats


def _calculate_fields(prev, curr):
    diffs = [c - p for p, c in zip(prev, curr)]
    total = sum(diffs)
    fields = {}

    if total == 0:
        return fields

    names = [
        "user", "nice", "system", "idle", "iowait", "irq",
        "softirq", "steal", "guest", "guest_nice"
    ]

    for i, name in enumerate(names):
        if i < len(diffs):
            fields[f"time_{name}"] = diffs[i]
            fields[f"usage_{name}"] = 100.0 * diffs[i] / total

    active = sum(diffs) - diffs[3] - (diffs[4] if len(diffs) > 4 else 0)
    fields["time_active"] = active
    fields["usage_active"] = 100.0 * active / total
    fields["usage_idle"] = 100.0 * diffs[3] / total

    return fields

def collect():
    global _last_cpu_times
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    metrics = []

    current = _read_proc_stat()

    if not _last_cpu_times:
        _last_cpu_times = current
        time.sleep(0.1)
        return []

    for cpu_id in current:
        if cpu_id not in _last_cpu_times:
            print(f"[linux_cpu] Skipping uninitialized core: {cpu_id}")
            continue

        fields = _calculate_fields(_last_cpu_times[cpu_id], current[cpu_id])
        core_label = "cpu-total" if cpu_id == "cpu" else cpu_id
        for k, v in fields.items():
            metrics.append(Metric(
                name=f"cpu_{k}_{core_label}",
                value=v,
                timestamp=timestamp,
                labels={"core": core_label, "host": hostname}
            ))

    _last_cpu_times = current
    return metrics