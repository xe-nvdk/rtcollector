
import time
import socket
from core.metric import Metric

def _read_meminfo():
    meminfo = {}
    with open("/proc/meminfo", "r") as f:
        for line in f:
            parts = line.strip().split(":")
            key = parts[0]
            value = int(parts[1].strip().split()[0]) * 1024  # convert kB to bytes
            meminfo[key] = value
    return meminfo

def collect():
    timestamp = int(time.time() * 1000)
    meminfo = _read_meminfo()
    hostname = socket.gethostname()

    total = meminfo.get("MemTotal", 0)
    free = meminfo.get("MemFree", 0)
    available = meminfo.get("MemAvailable", 0)
    buffers = meminfo.get("Buffers", 0)
    cached = meminfo.get("Cached", 0)
    used = total - free - buffers - cached
    percent = (used / total) * 100 if total > 0 else 0

    labels = {"host": hostname}
    metrics = [
        Metric(name="mem_total", value=total, timestamp=timestamp, labels=labels),
        Metric(name="mem_used", value=used, timestamp=timestamp, labels=labels),
        Metric(name="mem_free", value=free, timestamp=timestamp, labels=labels),
        Metric(name="mem_available", value=available, timestamp=timestamp, labels=labels),
        Metric(name="mem_percent", value=percent, timestamp=timestamp, labels=labels),
    ]
    return metrics