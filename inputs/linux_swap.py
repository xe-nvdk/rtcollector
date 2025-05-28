import time
import socket
import os
from core.metric import Metric
from utils.metrics import calculate_rate, create_key
from utils.debug import debug_log

def collect(config=None):
    """Collect swap statistics."""
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    metrics = []
    
    # Get swap usage stats from /proc/meminfo
    try:
        swap_total = 0
        swap_free = 0
        swap_used = 0
        
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('SwapTotal:'):
                    swap_total = int(line.split()[1]) * 1024  # Convert KB to bytes
                elif line.startswith('SwapFree:'):
                    swap_free = int(line.split()[1]) * 1024  # Convert KB to bytes
        
        if swap_total > 0:
            swap_used = swap_total - swap_free
            swap_used_percent = (swap_used / swap_total) * 100
        else:
            swap_used_percent = 0
        
        # Add usage metrics
        metrics.append(Metric(
            name="swap_total",
            value=swap_total,
            timestamp=timestamp,
            labels={"host": hostname}
        ))
        
        metrics.append(Metric(
            name="swap_free",
            value=swap_free,
            timestamp=timestamp,
            labels={"host": hostname}
        ))
        
        metrics.append(Metric(
            name="swap_used",
            value=swap_used,
            timestamp=timestamp,
            labels={"host": hostname}
        ))
        
        metrics.append(Metric(
            name="swap_used_percent",
            value=swap_used_percent,
            timestamp=timestamp,
            labels={"host": hostname}
        ))
    except Exception as e:
        print(f"[linux_swap] Error collecting swap usage metrics: {e}")
    
    # Read swap I/O stats from /proc/vmstat
    try:
        swap_in = 0
        swap_out = 0
        
        with open('/proc/vmstat', 'r') as f:
            for line in f:
                if line.startswith('pswpin'):
                    # Pages swapped in
                    swap_in = int(line.split()[1]) * 4096  # Convert pages to bytes (4KB page size)
                elif line.startswith('pswpout'):
                    # Pages swapped out
                    swap_out = int(line.split()[1]) * 4096  # Convert pages to bytes (4KB page size)
        
        # Add raw counter metrics
        metrics.append(Metric(
            name="swap_in",
            value=swap_in,
            timestamp=timestamp,
            labels={"host": hostname}
        ))
        
        metrics.append(Metric(
            name="swap_out",
            value=swap_out,
            timestamp=timestamp,
            labels={"host": hostname}
        ))
        
        # Calculate and add rate metrics
        in_rate = calculate_rate("swap_in", swap_in, timestamp)
        if in_rate is not None:
            metrics.append(Metric(
                name="swap_in_rate",
                value=in_rate,
                timestamp=timestamp,
                labels={"host": hostname}
            ))
        
        out_rate = calculate_rate("swap_out", swap_out, timestamp)
        if out_rate is not None:
            metrics.append(Metric(
                name="swap_out_rate",
                value=out_rate,
                timestamp=timestamp,
                labels={"host": hostname}
            ))
    except Exception as e:
        print(f"[linux_swap] Error collecting swap I/O metrics: {e}")
    
    # Debug logging removed for brevity
    return metrics