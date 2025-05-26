import time
import platform
import socket
from core.metric import Metric

# Store previous stats for delta calculations
_last_stats = {}
_last_time = 0

def collect(config=None):
    # Verify we're on macOS
    if platform.system() != "Darwin":
        return {
            "macos_io_logs": [{
                "message": "macos_io plugin can only run on macOS systems",
                "level": "error",
                "tags": {"source": "macos_io"}
            }]
        }
    
    try:
        import psutil
    except ImportError:
        return {
            "macos_io_logs": [{
                "message": "psutil module is required for macos_io plugin",
                "level": "error",
                "tags": {"source": "macos_io"}
            }]
        }
    
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    current_time = time.time()
    
    try:
        # Get disk I/O counters
        io_counters = psutil.disk_io_counters(perdisk=True)
        
        global _last_stats, _last_time
        if not _last_stats or _last_time == 0:
            _last_stats = io_counters
            _last_time = current_time
            logs.append({
                "message": "Initialized disk I/O stats, waiting for next collection cycle",
                "level": "info",
                "tags": {"source": "macos_io"}
            })
            return {"macos_io_logs": logs}
        
        # Calculate time delta in seconds
        time_delta = current_time - _last_time
        if time_delta <= 0:
            logs.append({
                "message": "Invalid time delta, skipping I/O metrics collection",
                "level": "warn",
                "tags": {"source": "macos_io"}
            })
            return {"macos_io_logs": logs}
        
        # Process each device
        for device, stats in io_counters.items():
            if device not in _last_stats:
                continue
            
            prev = _last_stats[device]
            
            # Common labels
            labels = {"source": "macos_io", "device": device, "host": hostname}
            
            # Calculate deltas
            read_count = stats.read_count - prev.read_count
            write_count = stats.write_count - prev.write_count
            read_bytes = stats.read_bytes - prev.read_bytes
            write_bytes = stats.write_bytes - prev.write_bytes
            
            # Calculate rates
            read_count_rate = read_count / time_delta
            write_count_rate = write_count / time_delta
            read_bytes_rate = read_bytes / time_delta
            write_bytes_rate = write_bytes / time_delta
            
            # Add metrics
            metrics.extend([
                # Raw counters
                Metric(name="io_read_count", value=read_count, timestamp=timestamp, labels=labels),
                Metric(name="io_write_count", value=write_count, timestamp=timestamp, labels=labels),
                Metric(name="io_read_bytes", value=read_bytes, timestamp=timestamp, labels=labels),
                Metric(name="io_write_bytes", value=write_bytes, timestamp=timestamp, labels=labels),
                
                # Rates
                Metric(name="io_read_count_rate", value=read_count_rate, timestamp=timestamp, labels=labels),
                Metric(name="io_write_count_rate", value=write_count_rate, timestamp=timestamp, labels=labels),
                Metric(name="io_read_bytes_rate", value=read_bytes_rate, timestamp=timestamp, labels=labels),
                Metric(name="io_write_bytes_rate", value=write_bytes_rate, timestamp=timestamp, labels=labels),
            ])
            
            # Add macOS-specific metrics if available
            if hasattr(stats, 'read_time') and hasattr(prev, 'read_time'):
                read_time = stats.read_time - prev.read_time
                metrics.append(Metric(name="io_read_time", value=read_time, timestamp=timestamp, labels=labels))
            
            if hasattr(stats, 'write_time') and hasattr(prev, 'write_time'):
                write_time = stats.write_time - prev.write_time
                metrics.append(Metric(name="io_write_time", value=write_time, timestamp=timestamp, labels=labels))
        
        # Update last stats for next collection
        _last_stats = io_counters
        _last_time = current_time
        
    except Exception as e:
        logs.append({
            "message": f"Error collecting macOS I/O metrics: {e}",
            "level": "error",
            "tags": {"source": "macos_io"}
        })
    
    return {
        "macos_io_metrics": metrics,
        "macos_io_logs": logs
    }