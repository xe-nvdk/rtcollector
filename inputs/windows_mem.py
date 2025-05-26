import psutil
import time
import platform
from core.metric import Metric

def collect(config=None):
    # Verify we're on Windows
    if platform.system() != "Windows":
        return {
            "windows_mem_logs": [{
                "message": "windows_mem plugin can only run on Windows systems",
                "level": "error",
                "tags": {"source": "windows_mem"}
            }]
        }
    
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    
    try:
        # Get memory metrics
        mem = psutil.virtual_memory()
        
        metrics.append(Metric(
            name="windows_mem_total",
            value=mem.total,
            labels={"source": "windows_mem"},
            timestamp=timestamp
        ))
        
        metrics.append(Metric(
            name="windows_mem_available",
            value=mem.available,
            labels={"source": "windows_mem"},
            timestamp=timestamp
        ))
        
        metrics.append(Metric(
            name="windows_mem_used",
            value=mem.used,
            labels={"source": "windows_mem"},
            timestamp=timestamp
        ))
        
        metrics.append(Metric(
            name="windows_mem_percent",
            value=mem.percent,
            labels={"source": "windows_mem"},
            timestamp=timestamp
        ))
        
        # Get swap metrics
        swap = psutil.swap_memory()
        
        metrics.append(Metric(
            name="windows_swap_total",
            value=swap.total,
            labels={"source": "windows_mem"},
            timestamp=timestamp
        ))
        
        metrics.append(Metric(
            name="windows_swap_used",
            value=swap.used,
            labels={"source": "windows_mem"},
            timestamp=timestamp
        ))
        
        metrics.append(Metric(
            name="windows_swap_free",
            value=swap.free,
            labels={"source": "windows_mem"},
            timestamp=timestamp
        ))
        
        metrics.append(Metric(
            name="windows_swap_percent",
            value=swap.percent,
            labels={"source": "windows_mem"},
            timestamp=timestamp
        ))
        
    except Exception as e:
        logs.append({
            "message": f"Error collecting Windows memory metrics: {e}",
            "level": "error",
            "tags": {"source": "windows_mem"}
        })
    
    return {
        "windows_mem_metrics": metrics,
        "windows_mem_logs": logs
    }