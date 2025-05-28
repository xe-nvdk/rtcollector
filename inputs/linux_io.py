import socket
import time
import platform
from core.metric import Metric
from utils.metrics import calculate_rate, create_key
from utils.debug import debug_log

# Store previous stats for delta calculations
_last_stats = {}
_last_time = 0

def _get_disk_devices():
    """Get a list of all disk devices from /proc/diskstats"""
    devices = []
    try:
        with open("/proc/diskstats", "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 14:
                    continue
                    
                # Get device name
                dev = parts[2]
                
                # Skip certain virtual devices
                if dev.startswith(('loop', 'ram')):
                    continue
                    
                devices.append(dev)
    except Exception as e:
        print(f"[linux_io] Error reading disk devices: {e}")  # Keep this as regular print for errors
    return devices

def collect(config=None):
    # Verify we're on Linux
    if platform.system() != "Linux":
        return {
            "linux_io_logs": [{
                "message": "linux_io plugin can only run on Linux systems",
                "level": "error",
                "tags": {"source": "linux_io"}
            }]
        }
    
    # Get configuration
    if config is None:
        config = {}
    
    # Get device filtering options
    exclude_devices = config.get('exclude_devices', [])
    include_devices = config.get('include_devices', [])
    
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    
    # Create discovery metrics for all disk devices
    try:
        all_devices = _get_disk_devices()
        for dev in all_devices:
            # Skip excluded devices
            if exclude_devices and dev in exclude_devices:
                continue
                
            # Skip devices not in include_devices if specified
            if include_devices and dev not in include_devices and len(include_devices) > 0:
                continue
                
            # Add discovery metric for this device
            metrics.append(Metric(
                name=f"diskio_device_{dev}",
                value=1,  # Just a placeholder value
                timestamp=timestamp,
                labels={"host": hostname, "device": dev}
            ))
    except Exception as e:
        logs.append({
            "message": f"Error creating disk device discovery metrics: {e}",
            "level": "error",
            "tags": {"source": "linux_io"}
        })
    
    try:
        # Read current disk stats
        current_stats = _read_diskstats(config)
        current_time = time.time()
        
        global _last_stats, _last_time
        if not _last_stats or _last_time == 0:
            _last_stats = current_stats
            _last_time = current_time
            return {
                "linux_io_logs": [{
                    "message": "Initialized IO stats, waiting for next collection cycle",
                    "level": "info",
                    "tags": {"source": "linux_io"}
                }]
            }
        
        # Calculate time delta in seconds
        time_delta = current_time - _last_time
        if time_delta <= 0:
            logs.append({
                "message": "Invalid time delta, skipping IO metrics collection",
                "level": "warn",
                "tags": {"source": "linux_io"}
            })
            return {"linux_io_logs": logs}
        
        # Process each device
        for dev, vals in current_stats.items():
            if dev not in _last_stats:
                continue
                
            # Skip excluded devices
            if exclude_devices and dev in exclude_devices:
                continue
                
            # Skip devices not in include_devices if specified
            if include_devices and dev not in include_devices and len(include_devices) > 0:
                continue
            
            # Debug logging for read metrics - removed for brevity
                
            # Calculate deltas
            delta_reads = vals["reads"] - _last_stats[dev]["reads"]
            delta_writes = vals["writes"] - _last_stats[dev]["writes"]
            delta_read_sectors = vals["read_sectors"] - _last_stats[dev]["read_sectors"]
            delta_write_sectors = vals["write_sectors"] - _last_stats[dev]["write_sectors"]
            delta_read_time = vals["read_time"] - _last_stats[dev]["read_time"]
            delta_write_time = vals["write_time"] - _last_stats[dev]["write_time"]
            delta_io_time = vals["io_time"] - _last_stats[dev]["io_time"]
            
            # Calculate rates
            reads_per_sec = delta_reads / time_delta
            writes_per_sec = delta_writes / time_delta
            
            # Convert sectors to bytes (512 bytes per sector)
            read_bytes = delta_read_sectors * 512
            write_bytes = delta_write_sectors * 512
            read_bytes_per_sec = read_bytes / time_delta
            write_bytes_per_sec = write_bytes / time_delta
            
            # Calculate read and write time rates (ms per second)
            read_time_rate = delta_read_time / time_delta
            write_time_rate = delta_write_time / time_delta
            
            # Calculate IO utilization (percentage of time the device was busy)
            io_util_percent = min(100.0, (delta_io_time / (time_delta * 1000)) * 100)
            
            # Common labels
            labels = {"source": "linux_io", "device": dev, "host": hostname}
            
            # Debug logging for calculated values - removed for brevity
            
            # Add metrics
            metrics.extend([
                # Raw counters
                Metric(name="io_reads", value=delta_reads, timestamp=timestamp, labels=labels),
                Metric(name="io_writes", value=delta_writes, timestamp=timestamp, labels=labels),
                Metric(name="io_read_bytes", value=read_bytes, timestamp=timestamp, labels=labels),
                Metric(name="io_write_bytes", value=write_bytes, timestamp=timestamp, labels=labels),
                
                # Rates
                Metric(name="io_reads_per_sec", value=reads_per_sec, timestamp=timestamp, labels=labels),
                Metric(name="io_writes_per_sec", value=writes_per_sec, timestamp=timestamp, labels=labels),
                Metric(name="io_read_bytes_per_sec", value=read_bytes_per_sec, timestamp=timestamp, labels=labels),
                Metric(name="io_write_bytes_per_sec", value=write_bytes_per_sec, timestamp=timestamp, labels=labels),
                
                # Timing
                Metric(name="io_read_time_ms", value=delta_read_time, timestamp=timestamp, labels=labels),
                Metric(name="io_write_time_ms", value=delta_write_time, timestamp=timestamp, labels=labels),
                Metric(name="io_util_percent", value=io_util_percent, timestamp=timestamp, labels=labels),
                
                # Device-specific metrics with device name in the key
                Metric(name=f"diskio_reads_rate_{dev}", value=reads_per_sec, timestamp=timestamp, labels=labels),
                Metric(name=f"diskio_writes_rate_{dev}", value=writes_per_sec, timestamp=timestamp, labels=labels),
                Metric(name=f"diskio_read_bytes_rate_{dev}", value=read_bytes_per_sec, timestamp=timestamp, labels=labels),
                Metric(name=f"diskio_write_bytes_rate_{dev}", value=write_bytes_per_sec, timestamp=timestamp, labels=labels),
                Metric(name=f"diskio_read_time_rate_{dev}", value=read_time_rate, timestamp=timestamp, labels=labels),
                Metric(name=f"diskio_write_time_rate_{dev}", value=write_time_rate, timestamp=timestamp, labels=labels),
                Metric(name=f"diskio_util_percent_{dev}", value=io_util_percent, timestamp=timestamp, labels=labels),
            ])
        
        # Update last stats for next collection
        _last_stats = current_stats
        _last_time = current_time
        
    except Exception as e:
        logs.append({
            "message": f"Error collecting Linux IO metrics: {e}",
            "level": "error",
            "tags": {"source": "linux_io"}
        })
    
    return {
        "linux_io_metrics": metrics,
        "linux_io_logs": logs
    }

def _read_diskstats(config=None):
    """Read and parse /proc/diskstats"""
    stats = {}
    try:
        with open("/proc/diskstats", "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 14:
                    continue
                    
                # Get device name
                dev = parts[2]
                
                # Debug logging for the first few devices - removed for brevity
                
                # Skip certain virtual devices but keep common disk types
                if dev.startswith(('loop', 'ram')):
                    continue
                    
                # Extract values from diskstats
                # See https://www.kernel.org/doc/Documentation/ABI/testing/procfs-diskstats
                stats[dev] = {
                    "reads": int(parts[3]),                  # Field 1: reads completed
                    "read_merged": int(parts[4]),            # Field 2: reads merged
                    "read_sectors": int(parts[5]),           # Field 3: sectors read
                    "read_time": int(parts[6]),              # Field 4: time spent reading (ms)
                    "writes": int(parts[7]),                 # Field 5: writes completed
                    "write_merged": int(parts[8]),           # Field 6: writes merged
                    "write_sectors": int(parts[9]),          # Field 7: sectors written
                    "write_time": int(parts[10]),            # Field 8: time spent writing (ms)
                    "io_in_progress": int(parts[11]),        # Field 9: I/Os currently in progress
                    "io_time": int(parts[12]),               # Field 10: time spent doing I/Os (ms)
                    "io_weighted_time": int(parts[13]),      # Field 11: weighted time spent doing I/Os (ms)
                }
    except Exception as e:
        print(f"[linux_io] Error reading /proc/diskstats: {e}")  # Keep this as regular print for errors
    return stats