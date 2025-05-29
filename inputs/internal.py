import os
import gc
import time
import socket
import resource
import platform
import threading
from core.metric import Metric
from utils.metrics import calculate_rate

# Global stats dictionary to track collector metrics
collector_stats = {
    "metrics_gathered": 0,
    "metrics_written": 0,
    "metrics_dropped": 0,
    "gather_errors": 0,
    "gather_timeouts": 0,
}

# Plugin-specific stats dictionaries
gather_stats = {}  # Format: {"plugin_name": {"gather_time_ns": 0, "metrics_gathered": 0}}
write_stats = {}   # Format: {"plugin_name": {"write_time_ns": 0, "metrics_written": 0, "metrics_dropped": 0}}

# Lock for thread-safe updates
stats_lock = threading.Lock()

def update_collector_stats(field, value=1):
    """Update collector stats in a thread-safe way"""
    with stats_lock:
        collector_stats[field] += value

def update_gather_stats(plugin_name, field, value):
    """Update gather stats for a specific plugin"""
    with stats_lock:
        if plugin_name not in gather_stats:
            gather_stats[plugin_name] = {
                "gather_time_ns": 0,
                "metrics_gathered": 0,
                "gather_timeouts": 0
            }
        gather_stats[plugin_name][field] += value

def update_write_stats(plugin_name, field, value):
    """Update write stats for a specific plugin"""
    with stats_lock:
        if plugin_name not in write_stats:
            write_stats[plugin_name] = {
                "write_time_ns": 0,
                "metrics_written": 0,
                "metrics_dropped": 0,
                "metrics_filtered": 0,
                "buffer_size": 0,
                "buffer_limit": 0
            }
        write_stats[plugin_name][field] += value

def collect(config=None):
    """Collect internal metrics about the collector and its plugins"""
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    metrics = []
    
    # Get memory stats (similar to Go's runtime.MemStats)
    mem_usage = resource.getrusage(resource.RUSAGE_SELF)
    gc_stats = gc.get_stats()[0] if hasattr(gc, 'get_stats') else {'collections': gc.get_count()[0]}
    
    # Add memory stats metrics
    mem_metrics = {
        "sys_bytes": mem_usage.ru_maxrss * 1024,  # Convert to bytes
        "heap_alloc_bytes": mem_usage.ru_maxrss * 1024,  # Approximation
        "num_gc": gc_stats.get('collections', 0),
    }
    
    for name, value in mem_metrics.items():
        metrics.append(Metric(
            name=f"internal_memstats_{name}",
            value=value,
            timestamp=timestamp,
            labels={"host": hostname}
        ))
    
    # Add agent stats metrics
    for name, value in collector_stats.items():
        # Add raw counter metric
        metrics.append(Metric(
            name=f"internal_agent_{name}",
            value=value,
            timestamp=timestamp,
            labels={"host": hostname}
        ))
        
        # Calculate and add rate metrics for counter values
        if name in ["metrics_gathered", "metrics_written", "metrics_dropped", "gather_errors"]:
            metric_key = f"internal_agent_{name}"
            rate = calculate_rate(metric_key, value, timestamp)
            if rate is not None:
                metrics.append(Metric(
                    name=f"internal_agent_{name}_rate",
                    value=rate,
                    timestamp=timestamp,
                    labels={"host": hostname}
                ))
    
    # Add gather stats metrics for each input plugin
    for plugin_name, stats in gather_stats.items():
        for name, value in stats.items():
            # Add raw counter metric
            metrics.append(Metric(
                name=f"internal_gather_{name}",
                value=value,
                timestamp=timestamp,
                labels={"host": hostname, "input": plugin_name}
            ))
            
            # Calculate and add rate metrics for time values
            if name == "gather_time_ns":
                metric_key = f"internal_gather_{name}_{plugin_name}"
                rate = calculate_rate(metric_key, value, timestamp)
                if rate is not None:
                    metrics.append(Metric(
                        name=f"internal_gather_{name}_rate",
                        value=rate,
                        timestamp=timestamp,
                        labels={"host": hostname, "input": plugin_name}
                    ))
    
    # Add write stats metrics for each output plugin
    for plugin_name, stats in write_stats.items():
        for name, value in stats.items():
            # Add raw counter metric
            metrics.append(Metric(
                name=f"internal_write_{name}",
                value=value,
                timestamp=timestamp,
                labels={"host": hostname, "output": plugin_name}
            ))
            
            # Calculate and add rate metrics for time and counter values
            if name in ["write_time_ns", "metrics_written", "metrics_dropped"]:
                metric_key = f"internal_write_{name}_{plugin_name}"
                rate = calculate_rate(metric_key, value, timestamp)
                if rate is not None:
                    metrics.append(Metric(
                        name=f"internal_write_{name}_rate",
                        value=rate,
                        timestamp=timestamp,
                        labels={"host": hostname, "output": plugin_name}
                    ))
    
    # Add process stats
    metrics.append(Metric(
        name="internal_process_cpu_seconds_total",
        value=mem_usage.ru_utime + mem_usage.ru_stime,
        timestamp=timestamp,
        labels={"host": hostname}
    ))
    
    metrics.append(Metric(
        name="internal_process_virtual_memory_bytes",
        value=mem_usage.ru_maxrss * 1024,
        timestamp=timestamp,
        labels={"host": hostname}
    ))
    
    return metrics