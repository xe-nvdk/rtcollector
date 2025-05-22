


import socket
import time
from core.metric import Metric

def _read_diskstats():
    stats = {}
    with open("/proc/diskstats", "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 14:
                continue
            major, minor, dev = parts[0], parts[1], parts[2]
            reads = int(parts[3])
            read_sectors = int(parts[5])
            writes = int(parts[7])
            write_sectors = int(parts[9])
            stats[dev] = {
                "reads": reads,
                "read_sectors": read_sectors,
                "writes": writes,
                "write_sectors": write_sectors,
            }
    return stats

_last_stats = {}

def collect():
    global _last_stats
    timestamp = int(time.time() * 1000)
    current = _read_diskstats()
    hostname = socket.gethostname()
    metrics = []

    if not _last_stats:
        _last_stats = current
        return []

    for dev, vals in current.items():
        if dev in _last_stats:
            delta_reads = vals["reads"] - _last_stats[dev]["reads"]
            delta_writes = vals["writes"] - _last_stats[dev]["writes"]
            delta_rsec = vals["read_sectors"] - _last_stats[dev]["read_sectors"]
            delta_wsec = vals["write_sectors"] - _last_stats[dev]["write_sectors"]
            labels = {"device": dev, "host": hostname}
            metrics.extend([
                Metric(name="disk_reads", value=delta_reads, timestamp=timestamp, labels=labels),
                Metric(name="disk_writes", value=delta_writes, timestamp=timestamp, labels=labels),
                Metric(name="disk_read_sectors", value=delta_rsec, timestamp=timestamp, labels=labels),
                Metric(name="disk_write_sectors", value=delta_wsec, timestamp=timestamp, labels=labels),
            ])

    _last_stats = current
    return metrics