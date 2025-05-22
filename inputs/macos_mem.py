import time
import platform
import socket

if platform.system() != "Darwin":
    raise EnvironmentError("macos_mem.py is only supported on macOS")

import psutil
from core.metric import Metric

def collect():
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    mem = psutil.virtual_memory()

    total = mem.total
    free = mem.free
    available = mem.available
    used = mem.used
    percent = mem.percent

    metrics = [
        Metric(name="mem_total", value=total, timestamp=timestamp, labels={"host": hostname}),
        Metric(name="mem_used", value=used, timestamp=timestamp, labels={"host": hostname}),
        Metric(name="mem_free", value=free, timestamp=timestamp, labels={"host": hostname}),
        Metric(name="mem_available", value=available, timestamp=timestamp, labels={"host": hostname}),
        Metric(name="mem_percent", value=percent, timestamp=timestamp, labels={"host": hostname}),
    ]
    return metrics
