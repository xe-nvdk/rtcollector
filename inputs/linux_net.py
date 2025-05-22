import time
import socket
from core.metric import Metric

def _read_netdev():
    stats = {}
    with open("/proc/net/dev", "r") as f:
        lines = f.readlines()[2:]  # skip headers
        for line in lines:
            parts = line.strip().split()
            iface = parts[0].strip(":")
            stats[iface] = {
                "rx_bytes": int(parts[1]),
                "rx_packets": int(parts[2]),
                "rx_errs": int(parts[3]),
                "rx_drop": int(parts[4]),
                "tx_bytes": int(parts[9]),
                "tx_packets": int(parts[10]),
                "tx_errs": int(parts[11]),
                "tx_drop": int(parts[12]),
            }
    return stats

_last_stats = {}

def collect():
    global _last_stats
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    current = _read_netdev()
    metrics = []

    if not _last_stats:
        _last_stats = current
        return []

    for iface, vals in current.items():
        if iface in _last_stats:
            labels = {"iface": iface, "host": hostname}

            metrics.extend([
                Metric(name="net_rx_bytes", value=vals["rx_bytes"] - _last_stats[iface]["rx_bytes"], timestamp=timestamp, labels=labels),
                Metric(name="net_tx_bytes", value=vals["tx_bytes"] - _last_stats[iface]["tx_bytes"], timestamp=timestamp, labels=labels),
                Metric(name="net_rx_packets", value=vals["rx_packets"] - _last_stats[iface]["rx_packets"], timestamp=timestamp, labels=labels),
                Metric(name="net_tx_packets", value=vals["tx_packets"] - _last_stats[iface]["tx_packets"], timestamp=timestamp, labels=labels),
                Metric(name="net_rx_errs", value=vals["rx_errs"] - _last_stats[iface]["rx_errs"], timestamp=timestamp, labels=labels),
                Metric(name="net_tx_errs", value=vals["tx_errs"] - _last_stats[iface]["tx_errs"], timestamp=timestamp, labels=labels),
                Metric(name="net_rx_drop", value=vals["rx_drop"] - _last_stats[iface]["rx_drop"], timestamp=timestamp, labels=labels),
                Metric(name="net_tx_drop", value=vals["tx_drop"] - _last_stats[iface]["tx_drop"], timestamp=timestamp, labels=labels),
            ])

    _last_stats = current
    return metrics