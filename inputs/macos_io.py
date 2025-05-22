import time
import platform
import socket

if platform.system() != "Darwin":
    raise EnvironmentError("macos_io.py is only supported on macOS")

import psutil
from core.metric import Metric

_last = {}

def collect():
    global _last
    timestamp = int(time.time() * 1000)
    metrics = []
    hostname = socket.gethostname()

    io_counters = psutil.disk_io_counters(perdisk=True)
    if not _last:
        _last = io_counters
        return []

    for device, stats in io_counters.items():
        if device not in _last:
            continue

        prev = _last[device]
        labels = {"device": device, "host": hostname}

        metrics.extend([
            Metric(name="disk_reads", value=stats.read_count - prev.read_count, timestamp=timestamp, labels=labels),
            Metric(name="disk_writes", value=stats.write_count - prev.write_count, timestamp=timestamp, labels=labels),
            Metric(name="disk_read_bytes", value=stats.read_bytes - prev.read_bytes, timestamp=timestamp, labels=labels),
            Metric(name="disk_write_bytes", value=stats.write_bytes - prev.write_bytes, timestamp=timestamp, labels=labels),
        ])

    _last = io_counters
    return metrics