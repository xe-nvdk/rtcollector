import time
import socket
import platform
from core.metric import Metric

def collect(config=None):
    # Verify we're on Linux
    if platform.system() != "Linux":
        return {
            "linux_mem_logs": [{
                "message": "linux_mem plugin can only run on Linux systems",
                "level": "error",
                "tags": {"source": "linux_mem"}
            }]
        }
    
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    
    try:
        meminfo = _read_meminfo()
        
        # Memory metrics
        total = meminfo.get("MemTotal", 0)
        free = meminfo.get("MemFree", 0)
        available = meminfo.get("MemAvailable", free)  # Fallback to free if MemAvailable not present
        buffers = meminfo.get("Buffers", 0)
        cached = meminfo.get("Cached", 0)
        
        # Calculate used memory (total - free - buffers - cached)
        used = total - free - buffers - cached
        used_percent = (used / total) * 100 if total > 0 else 0
        
        # Calculate available percent
        available_percent = (available / total) * 100 if total > 0 else 0
        
        # Common labels
        labels = {"source": "linux_mem", "host": hostname}
        
        # Add memory metrics
        metrics.extend([
            Metric(name="mem_total", value=total, timestamp=timestamp, labels=labels),
            Metric(name="mem_used", value=used, timestamp=timestamp, labels=labels),
            Metric(name="mem_free", value=free, timestamp=timestamp, labels=labels),
            Metric(name="mem_available", value=available, timestamp=timestamp, labels=labels),
            Metric(name="mem_buffers", value=buffers, timestamp=timestamp, labels=labels),
            Metric(name="mem_cached", value=cached, timestamp=timestamp, labels=labels),
            Metric(name="mem_used_percent", value=used_percent, timestamp=timestamp, labels=labels),
            Metric(name="mem_available_percent", value=available_percent, timestamp=timestamp, labels=labels),
        ])
        
        # Swap metrics
        swap_total = meminfo.get("SwapTotal", 0)
        swap_free = meminfo.get("SwapFree", 0)
        swap_used = swap_total - swap_free
        swap_percent = (swap_used / swap_total) * 100 if swap_total > 0 else 0
        
        # Add swap metrics
        if swap_total > 0:
            metrics.extend([
                Metric(name="swap_total", value=swap_total, timestamp=timestamp, labels=labels),
                Metric(name="swap_used", value=swap_used, timestamp=timestamp, labels=labels),
                Metric(name="swap_free", value=swap_free, timestamp=timestamp, labels=labels),
                Metric(name="swap_percent", value=swap_percent, timestamp=timestamp, labels=labels),
            ])
        
    except Exception as e:
        logs.append({
            "message": f"Error collecting Linux memory metrics: {e}",
            "level": "error",
            "tags": {"source": "linux_mem"}
        })
    
    return {
        "linux_mem_metrics": metrics,
        "linux_mem_logs": logs
    }

def _read_meminfo():
    meminfo = {}
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) < 2:
                    continue
                    
                key = parts[0]
                value_parts = parts[1].strip().split()
                
                # Convert to bytes (most values are in kB)
                value = int(value_parts[0])
                if len(value_parts) > 1 and value_parts[1] == "kB":
                    value *= 1024
                
                meminfo[key] = value
    except Exception as e:
        print(f"[linux_mem] Error reading /proc/meminfo: {e}")
    return meminfo