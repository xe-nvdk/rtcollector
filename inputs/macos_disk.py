import socket
import time
import platform

if platform.system() != "Darwin":
    raise EnvironmentError("macos_disk.py is only supported on macOS")

import psutil
from core.metric import Metric

def collect():
    timestamp = int(time.time() * 1000)
    metrics = []
    hostname = socket.gethostname()

    partitions = psutil.disk_partitions(all=False)
    for part in partitions:
        try:
            usage = psutil.disk_usage(part.mountpoint)
            device = part.device.replace("/dev/", "")
            labels = {"device": device, "host": hostname}
            metrics.extend([
                Metric(name="disk_total", value=usage.total, timestamp=timestamp, labels=labels),
                Metric(name="disk_used", value=usage.used, timestamp=timestamp, labels=labels),
                Metric(name="disk_free", value=usage.free, timestamp=timestamp, labels=labels),
                Metric(name="disk_used_percent", value=usage.percent, timestamp=timestamp, labels=labels),
            ])
        except PermissionError:
            continue

    return metrics
