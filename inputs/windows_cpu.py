import psutil
import time
import platform
from core.metric import Metric

def collect(config=None):
    # Verify we're on Windows
    if platform.system() != "Windows":
        return {
            "windows_cpu_logs": [{
                "message": "windows_cpu plugin can only run on Windows systems",
                "level": "error",
                "tags": {"source": "windows_cpu"}
            }]
        }
    
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    
    try:
        # Get per-CPU metrics
        per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
        for i, cpu_percent in enumerate(per_cpu):
            metrics.append(Metric(
                name="windows_cpu_percent",
                value=cpu_percent,
                labels={"source": "windows_cpu", "core": f"cpu{i}"},
                timestamp=timestamp
            ))
        
        # Get overall CPU metrics
        cpu_times = psutil.cpu_times_percent(interval=0.1)
        
        metrics.append(Metric(
            name="windows_cpu_user",
            value=cpu_times.user,
            labels={"source": "windows_cpu"},
            timestamp=timestamp
        ))
        
        metrics.append(Metric(
            name="windows_cpu_system",
            value=cpu_times.system,
            labels={"source": "windows_cpu"},
            timestamp=timestamp
        ))
        
        metrics.append(Metric(
            name="windows_cpu_idle",
            value=cpu_times.idle,
            labels={"source": "windows_cpu"},
            timestamp=timestamp
        ))
        
        # Windows-specific: interrupt and dpc time
        if hasattr(cpu_times, "interrupt"):
            metrics.append(Metric(
                name="windows_cpu_interrupt",
                value=cpu_times.interrupt,
                labels={"source": "windows_cpu"},
                timestamp=timestamp
            ))
        
        if hasattr(cpu_times, "dpc"):
            metrics.append(Metric(
                name="windows_cpu_dpc",
                value=cpu_times.dpc,
                labels={"source": "windows_cpu"},
                timestamp=timestamp
            ))
        
    except Exception as e:
        logs.append({
            "message": f"Error collecting Windows CPU metrics: {e}",
            "level": "error",
            "tags": {"source": "windows_cpu"}
        })
    
    return {
        "windows_cpu_metrics": metrics,
        "windows_cpu_logs": logs
    }