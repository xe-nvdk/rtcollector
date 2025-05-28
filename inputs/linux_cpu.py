import time
import socket
import platform
from core.metric import Metric
from utils.debug import debug_log

_last_cpu_times = {}

def collect(config=None):
    # Verify we're on Linux
    if platform.system() != "Linux":
        print("[linux_cpu] This plugin only works on Linux")
        return []
    
    metrics = []
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    
    # Debug logging removed for brevity
    
    try:
        current = _read_proc_stat(config)
        
        global _last_cpu_times
        if not _last_cpu_times:
            _last_cpu_times = current
            time.sleep(0.1)
            current = _read_proc_stat(config)
        
        for cpu_id in current:
            if cpu_id not in _last_cpu_times:
                debug_log("linux_cpu", f"Skipping uninitialized core: {cpu_id}", config)
                continue
            
            fields = _calculate_fields(_last_cpu_times[cpu_id], current[cpu_id])
            core_label = "cpu-total" if cpu_id == "cpu" else cpu_id
            
            for k, v in fields.items():
                # Use consistent naming convention with cpu_usage_ prefix
                base_metric_name = f"cpu_usage_{k}"
                
                # Create a unique key for each core by including the core in the name
                metric_name = f"{base_metric_name}_{core_label}"
                
                metrics.append(Metric(
                    name=metric_name,
                    value=v,
                    timestamp=timestamp,
                    labels={"source": "linux_cpu", "core": core_label, "host": hostname}
                ))
                # Only log detailed metrics in debug mode
        
        _last_cpu_times = current
        
    except Exception as e:
        print(f"[linux_cpu] Error collecting Linux CPU metrics: {e}")
    
    # Debug logging removed for brevity
    return metrics

def _read_proc_stat(config=None):
    cpu_stats = {}
    try:
        with open("/proc/stat", "r") as f:
            for line in f:
                if not line.startswith("cpu"):
                    continue
                parts = line.strip().split()
                cpu_id = parts[0]  # e.g., 'cpu', 'cpu0', 'cpu1'
                values = list(map(int, parts[1:]))
                cpu_stats[cpu_id] = values
                # Debug logging removed for brevity
    except Exception as e:
        print(f"[linux_cpu] Error reading /proc/stat: {e}")
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
            fields[name] = 100.0 * diffs[i] / total

    # Calculate active time (everything except idle and iowait)
    active = total - diffs[3] - (diffs[4] if len(diffs) > 4 else 0)
    fields["active"] = 100.0 * active / total
    fields["idle"] = 100.0 * diffs[3] / total
    
    return fields