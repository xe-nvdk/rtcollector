import time
import platform
import socket

if platform.system() != "Darwin":
    raise EnvironmentError("macos_net.py is only supported on macOS")

import psutil
from core.metric import Metric

_last = {}

def collect():
    global _last
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    metrics = []

    counters = psutil.net_io_counters(pernic=True)
    if not _last:
        _last = counters
        return []

    for iface, stats in counters.items():
        if iface not in _last:
            continue

        prev = _last[iface]

        metrics.extend([
            Metric(name="net_bytes_sent", value=stats.bytes_sent - prev.bytes_sent, timestamp=timestamp, labels={"iface": iface, "host": hostname}),
            Metric(name="net_bytes_recv", value=stats.bytes_recv - prev.bytes_recv, timestamp=timestamp, labels={"iface": iface, "host": hostname}),
            Metric(name="net_packets_sent", value=stats.packets_sent - prev.packets_sent, timestamp=timestamp, labels={"iface": iface, "host": hostname}),
            Metric(name="net_packets_recv", value=stats.packets_recv - prev.packets_recv, timestamp=timestamp, labels={"iface": iface, "host": hostname}),
            Metric(name="net_errin", value=stats.errin - prev.errin, timestamp=timestamp, labels={"iface": iface, "host": hostname}),
            Metric(name="net_errout", value=stats.errout - prev.errout, timestamp=timestamp, labels={"iface": iface, "host": hostname}),
            Metric(name="net_dropin", value=stats.dropin - prev.dropin, timestamp=timestamp, labels={"iface": iface, "host": hostname}),
            Metric(name="net_dropout", value=stats.dropout - prev.dropout, timestamp=timestamp, labels={"iface": iface, "host": hostname}),
        ])

    _last = counters
    return metrics
