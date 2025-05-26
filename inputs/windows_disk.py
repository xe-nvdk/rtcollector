import psutil
import time
import platform
from core.metric import Metric

def collect(config=None):
    # Verify we're on Windows
    if platform.system() != "Windows":
        return {
            "windows_disk_logs": [{
                "message": "windows_disk plugin can only run on Windows systems",
                "level": "error",
                "tags": {"source": "windows_disk"}
            }]
        }
    
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    
    try:
        # Get disk usage for all partitions
        partitions = psutil.disk_partitions(all=False)
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                
                # Skip CD-ROM drives or other special devices that might not have usage stats
                if usage.total == 0:
                    continue
                
                labels = {
                    "source": "windows_disk",
                    "device": partition.device.replace(':', ''),
                    "mountpoint": partition.mountpoint.replace(':', ''),
                    "fstype": partition.fstype
                }
                
                metrics.append(Metric(
                    name="windows_disk_total",
                    value=usage.total,
                    labels=labels.copy(),
                    timestamp=timestamp
                ))
                
                metrics.append(Metric(
                    name="windows_disk_used",
                    value=usage.used,
                    labels=labels.copy(),
                    timestamp=timestamp
                ))
                
                metrics.append(Metric(
                    name="windows_disk_free",
                    value=usage.free,
                    labels=labels.copy(),
                    timestamp=timestamp
                ))
                
                metrics.append(Metric(
                    name="windows_disk_percent",
                    value=usage.percent,
                    labels=labels.copy(),
                    timestamp=timestamp
                ))
            except PermissionError:
                # Skip drives we don't have access to
                continue
            except Exception as e:
                logs.append({
                    "message": f"Error collecting disk metrics for {partition.mountpoint}: {e}",
                    "level": "warn",
                    "tags": {"source": "windows_disk", "mountpoint": partition.mountpoint}
                })
        
        # Get disk I/O statistics
        disk_io = psutil.disk_io_counters(perdisk=True)
        for disk_name, counters in disk_io.items():
            labels = {"source": "windows_disk", "disk": disk_name}
            
            metrics.append(Metric(
                name="windows_disk_read_count",
                value=counters.read_count,
                labels=labels.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="windows_disk_write_count",
                value=counters.write_count,
                labels=labels.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="windows_disk_read_bytes",
                value=counters.read_bytes,
                labels=labels.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="windows_disk_write_bytes",
                value=counters.write_bytes,
                labels=labels.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="windows_disk_read_time",
                value=counters.read_time,
                labels=labels.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="windows_disk_write_time",
                value=counters.write_time,
                labels=labels.copy(),
                timestamp=timestamp
            ))
        
    except Exception as e:
        logs.append({
            "message": f"Error collecting Windows disk metrics: {e}",
            "level": "error",
            "tags": {"source": "windows_disk"}
        })
    
    return {
        "windows_disk_metrics": metrics,
        "windows_disk_logs": logs
    }