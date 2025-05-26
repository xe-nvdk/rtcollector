import time
import platform
import socket
from core.metric import Metric

def collect(config=None):
    # Verify we're on macOS
    if platform.system() != "Darwin":
        return {
            "macos_disk_logs": [{
                "message": "macos_disk plugin can only run on macOS systems",
                "level": "error",
                "tags": {"source": "macos_disk"}
            }]
        }
    
    try:
        import psutil
    except ImportError:
        return {
            "macos_disk_logs": [{
                "message": "psutil module is required for macos_disk plugin",
                "level": "error",
                "tags": {"source": "macos_disk"}
            }]
        }
    
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    
    try:
        # Get disk partitions
        partitions = psutil.disk_partitions(all=False)
        
        # Filter out virtual filesystems
        physical_partitions = [p for p in partitions if p.fstype not in ('autofs', 'devfs', 'none')]
        
        # Collect metrics for each partition
        for part in physical_partitions:
            try:
                # Get disk usage
                usage = psutil.disk_usage(part.mountpoint)
                
                # Extract device name without /dev/ prefix
                device = part.device.replace("/dev/", "")
                
                # Common labels
                labels = {
                    "source": "macos_disk", 
                    "device": device, 
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "host": hostname
                }
                
                # Add disk space metrics
                metrics.extend([
                    Metric(name="disk_total", value=usage.total, timestamp=timestamp, labels=labels),
                    Metric(name="disk_used", value=usage.used, timestamp=timestamp, labels=labels),
                    Metric(name="disk_free", value=usage.free, timestamp=timestamp, labels=labels),
                    Metric(name="disk_percent", value=usage.percent, timestamp=timestamp, labels=labels),
                ])
                
                # Calculate additional metrics
                available = usage.total - usage.used
                available_percent = (available / usage.total) * 100 if usage.total > 0 else 0
                metrics.append(Metric(name="disk_available", value=available, timestamp=timestamp, labels=labels))
                metrics.append(Metric(name="disk_available_percent", value=available_percent, timestamp=timestamp, labels=labels))
                
            except PermissionError:
                logs.append({
                    "message": f"Permission denied accessing {part.mountpoint}",
                    "level": "warn",
                    "tags": {"source": "macos_disk", "mountpoint": part.mountpoint}
                })
                continue
            except Exception as e:
                logs.append({
                    "message": f"Error collecting disk metrics for {part.mountpoint}: {e}",
                    "level": "warn",
                    "tags": {"source": "macos_disk", "mountpoint": part.mountpoint}
                })
                continue
        
    except Exception as e:
        logs.append({
            "message": f"Error collecting macOS disk metrics: {e}",
            "level": "error",
            "tags": {"source": "macos_disk"}
        })
    
    return {
        "macos_disk_metrics": metrics,
        "macos_disk_logs": logs
    }