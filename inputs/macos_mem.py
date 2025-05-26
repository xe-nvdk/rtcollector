import time
import platform
import socket
from core.metric import Metric

def collect(config=None):
    # Verify we're on macOS
    if platform.system() != "Darwin":
        return {
            "macos_mem_logs": [{
                "message": "macos_mem plugin can only run on macOS systems",
                "level": "error",
                "tags": {"source": "macos_mem"}
            }]
        }
    
    try:
        import psutil
    except ImportError:
        return {
            "macos_mem_logs": [{
                "message": "psutil module is required for macos_mem plugin",
                "level": "error",
                "tags": {"source": "macos_mem"}
            }]
        }
    
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    
    try:
        # Get virtual memory metrics
        mem = psutil.virtual_memory()
        
        # Common labels
        labels = {"source": "macos_mem", "host": hostname}
        
        # Add memory metrics
        metrics.extend([
            Metric(name="mem_total", value=mem.total, timestamp=timestamp, labels=labels),
            Metric(name="mem_used", value=mem.used, timestamp=timestamp, labels=labels),
            Metric(name="mem_free", value=mem.free, timestamp=timestamp, labels=labels),
            Metric(name="mem_available", value=mem.available, timestamp=timestamp, labels=labels),
            Metric(name="mem_percent", value=mem.percent, timestamp=timestamp, labels=labels),
        ])
        
        # Add macOS-specific memory metrics if available
        if hasattr(mem, 'active'):
            metrics.append(Metric(name="mem_active", value=mem.active, timestamp=timestamp, labels=labels))
        if hasattr(mem, 'inactive'):
            metrics.append(Metric(name="mem_inactive", value=mem.inactive, timestamp=timestamp, labels=labels))
        if hasattr(mem, 'wired'):
            metrics.append(Metric(name="mem_wired", value=mem.wired, timestamp=timestamp, labels=labels))
        
        # Get swap memory metrics
        swap = psutil.swap_memory()
        
        # Add swap metrics
        metrics.extend([
            Metric(name="swap_total", value=swap.total, timestamp=timestamp, labels=labels),
            Metric(name="swap_used", value=swap.used, timestamp=timestamp, labels=labels),
            Metric(name="swap_free", value=swap.free, timestamp=timestamp, labels=labels),
            Metric(name="swap_percent", value=swap.percent, timestamp=timestamp, labels=labels),
            Metric(name="swap_sin", value=swap.sin, timestamp=timestamp, labels=labels),
            Metric(name="swap_sout", value=swap.sout, timestamp=timestamp, labels=labels),
        ])
        
        # Calculate additional metrics
        used_percent = (mem.used / mem.total) * 100 if mem.total > 0 else 0
        metrics.append(Metric(name="mem_used_percent", value=used_percent, timestamp=timestamp, labels=labels))
        
    except Exception as e:
        logs.append({
            "message": f"Error collecting macOS memory metrics: {e}",
            "level": "error",
            "tags": {"source": "macos_mem"}
        })
    
    return {
        "macos_mem_metrics": metrics,
        "macos_mem_logs": logs
    }