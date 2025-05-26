import time
import platform
import socket
from core.metric import Metric

def collect(config=None):
    # Verify we're on macOS
    if platform.system() != "Darwin":
        return {
            "macos_cpu_logs": [{
                "message": "macos_cpu plugin can only run on macOS systems",
                "level": "error",
                "tags": {"source": "macos_cpu"}
            }]
        }
    
    try:
        import psutil
    except ImportError:
        return {
            "macos_cpu_logs": [{
                "message": "psutil module is required for macos_cpu plugin",
                "level": "error",
                "tags": {"source": "macos_cpu"}
            }]
        }
    
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    
    try:
        # Get per-CPU metrics
        per_cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        for i, cpu_percent in enumerate(per_cpu_percent):
            metrics.append(Metric(
                name="cpu_percent",
                value=cpu_percent,
                labels={"source": "macos_cpu", "core": f"cpu{i}", "host": hostname},
                timestamp=timestamp
            ))
        
        # Get detailed CPU times per core
        times = psutil.cpu_times(percpu=True)
        for i, t in enumerate(times):
            metrics.extend([
                Metric(
                    name="cpu_user",
                    value=t.user,
                    labels={"source": "macos_cpu", "core": f"cpu{i}", "host": hostname},
                    timestamp=timestamp
                ),
                Metric(
                    name="cpu_system",
                    value=t.system,
                    labels={"source": "macos_cpu", "core": f"cpu{i}", "host": hostname},
                    timestamp=timestamp
                ),
                Metric(
                    name="cpu_idle",
                    value=t.idle,
                    labels={"source": "macos_cpu", "core": f"cpu{i}", "host": hostname},
                    timestamp=timestamp
                ),
            ])
            
            # Add macOS-specific metrics if available
            if hasattr(t, 'nice'):
                metrics.append(Metric(
                    name="cpu_nice",
                    value=t.nice,
                    labels={"source": "macos_cpu", "core": f"cpu{i}", "host": hostname},
                    timestamp=timestamp
                ))
        
        # Get total CPU metrics
        total_percent = psutil.cpu_percent(interval=0.1)
        metrics.append(Metric(
            name="cpu_percent",
            value=total_percent,
            labels={"source": "macos_cpu", "core": "total", "host": hostname},
            timestamp=timestamp
        ))
        
        total = psutil.cpu_times()
        metrics.extend([
            Metric(
                name="cpu_user",
                value=total.user,
                labels={"source": "macos_cpu", "core": "total", "host": hostname},
                timestamp=timestamp
            ),
            Metric(
                name="cpu_system",
                value=total.system,
                labels={"source": "macos_cpu", "core": "total", "host": hostname},
                timestamp=timestamp
            ),
            Metric(
                name="cpu_idle",
                value=total.idle,
                labels={"source": "macos_cpu", "core": "total", "host": hostname},
                timestamp=timestamp
            ),
        ])
        
        # Add load averages (1, 5, 15 minutes)
        load1, load5, load15 = psutil.getloadavg()
        metrics.extend([
            Metric(
                name="cpu_load1",
                value=load1,
                labels={"source": "macos_cpu", "host": hostname},
                timestamp=timestamp
            ),
            Metric(
                name="cpu_load5",
                value=load5,
                labels={"source": "macos_cpu", "host": hostname},
                timestamp=timestamp
            ),
            Metric(
                name="cpu_load15",
                value=load15,
                labels={"source": "macos_cpu", "host": hostname},
                timestamp=timestamp
            ),
        ])
        
    except Exception as e:
        logs.append({
            "message": f"Error collecting macOS CPU metrics: {e}",
            "level": "error",
            "tags": {"source": "macos_cpu"}
        })
    
    return {
        "macos_cpu_metrics": metrics,
        "macos_cpu_logs": logs
    }