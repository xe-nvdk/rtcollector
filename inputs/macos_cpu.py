import time
import platform
import socket

if platform.system() != "Darwin":
    raise EnvironmentError("macos_cpu.py is only supported on macOS")

import psutil
from core.metric import Metric

def collect():
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    metrics = []

    times = psutil.cpu_times(percpu=True)
    for i, t in enumerate(times):
        metrics.extend([
            Metric(name="cpu_usage_user", value=t.user, timestamp=timestamp, labels={"core": f"cpu{i}", "host": hostname}),
            Metric(name="cpu_usage_system", value=t.system, timestamp=timestamp, labels={"core": f"cpu{i}", "host": hostname}),
            Metric(name="cpu_usage_idle", value=t.idle, timestamp=timestamp, labels={"core": f"cpu{i}", "host": hostname}),
        ])

    total = psutil.cpu_times()
    metrics.extend([
        Metric(name="cpu_usage_user", value=total.user, timestamp=timestamp, labels={"core": "total", "host": hostname}),
        Metric(name="cpu_usage_system", value=total.system, timestamp=timestamp, labels={"core": "total", "host": hostname}),
        Metric(name="cpu_usage_idle", value=total.idle, timestamp=timestamp, labels={"core": "total", "host": hostname}),
    ])

    return metrics
