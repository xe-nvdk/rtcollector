import os
import time
import socket
import platform
from core.metric import Metric

def collect(config=None):
    # Verify we're on Linux
    if platform.system() != "Linux":
        return {
            "linux_disk_logs": [{
                "message": "linux_disk plugin can only run on Linux systems",
                "level": "error",
                "tags": {"source": "linux_disk"}
            }]
        }
    
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    
    try:
        # Get mount points to monitor
        mount_points = get_mount_points()
        
        # Collect disk usage metrics for each mount point
        for mount in mount_points:
            try:
                stats = os.statvfs(mount)
                
                # Calculate disk space metrics
                total = stats.f_blocks * stats.f_frsize
                free = stats.f_bfree * stats.f_frsize
                available = stats.f_bavail * stats.f_frsize  # Available to non-root users
                used = total - free
                used_percent = (used / total) * 100 if total > 0 else 0
                
                # Calculate inodes metrics
                inodes_total = stats.f_files
                inodes_free = stats.f_ffree
                inodes_used = inodes_total - inodes_free
                inodes_percent = (inodes_used / inodes_total) * 100 if inodes_total > 0 else 0
                
                # Common labels
                labels = {"source": "linux_disk", "mount": mount, "host": hostname}
                
                # Add disk space metrics
                metrics.extend([
                    Metric(name="disk_total", value=total, timestamp=timestamp, labels=labels),
                    Metric(name="disk_used", value=used, timestamp=timestamp, labels=labels),
                    Metric(name="disk_free", value=free, timestamp=timestamp, labels=labels),
                    Metric(name="disk_available", value=available, timestamp=timestamp, labels=labels),
                    Metric(name="disk_used_percent", value=used_percent, timestamp=timestamp, labels=labels),
                ])
                
                # Add inode metrics
                metrics.extend([
                    Metric(name="disk_inodes_total", value=inodes_total, timestamp=timestamp, labels=labels),
                    Metric(name="disk_inodes_used", value=inodes_used, timestamp=timestamp, labels=labels),
                    Metric(name="disk_inodes_free", value=inodes_free, timestamp=timestamp, labels=labels),
                    Metric(name="disk_inodes_percent", value=inodes_percent, timestamp=timestamp, labels=labels),
                ])
                
            except Exception as e:
                logs.append({
                    "message": f"Error collecting disk metrics for {mount}: {e}",
                    "level": "warn",
                    "tags": {"source": "linux_disk", "mount": mount}
                })
                continue
        
    except Exception as e:
        logs.append({
            "message": f"Error collecting Linux disk metrics: {e}",
            "level": "error",
            "tags": {"source": "linux_disk"}
        })
    
    return {
        "linux_disk_metrics": metrics,
        "linux_disk_logs": logs
    }

def get_mount_points():
    """Get list of mount points to monitor, excluding virtual filesystems"""
    mount_points = []
    try:
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 3:
                    continue
                    
                device, mount_point, fstype = parts[0], parts[1], parts[2]
                
                # Skip virtual filesystems and special mounts
                if fstype in ["tmpfs", "proc", "sysfs", "devtmpfs", "devpts", "securityfs", 
                             "cgroup", "pstore", "debugfs", "configfs", "selinuxfs"]:
                    continue
                    
                # Skip bind mounts and virtual devices
                if device.startswith("/dev/loop") or device == "none":
                    continue
                    
                mount_points.append(mount_point)
    except Exception as e:
        print(f"[linux_disk] Error reading mount points: {e}")
    
    return mount_points