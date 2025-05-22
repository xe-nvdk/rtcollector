import os
import time
import socket
from core.metric import Metric

def get_mount_points():
    mount_points = []
    with open("/proc/mounts", "r") as f:
        for line in f:
            parts = line.split()
            device, mount_point, fstype = parts[0], parts[1], parts[2]
            if fstype not in ["tmpfs", "proc", "sysfs", "devtmpfs"]:
                mount_points.append(mount_point)
    return mount_points

def collect():
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    metrics = []
    for mount in get_mount_points():
        try:
            stats = os.statvfs(mount)
            total = stats.f_blocks * stats.f_frsize
            free = stats.f_bfree * stats.f_frsize
            used = total - free
            used_percent = (used / total) * 100 if total > 0 else 0

            labels = {"mount": mount, "host": hostname}
            metrics.extend([
                Metric(name="disk_total", value=total, timestamp=timestamp, labels=labels),
                Metric(name="disk_used", value=used, timestamp=timestamp, labels=labels),
                Metric(name="disk_free", value=free, timestamp=timestamp, labels=labels),
                Metric(name="disk_used_percent", value=used_percent, timestamp=timestamp, labels=labels),
            ])
        except Exception as e:
            continue  # skip if permission denied or inaccessible mount

    return metrics