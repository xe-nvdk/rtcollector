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
    
    print("[linux_disk] Starting disk metrics collection")
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
                
                # Debug output
                print(f"[linux_disk] Mount: {mount}, Total: {total}, Used: {used}, Free: {free}")
                print(f"[linux_disk] Used percent calculation: {used}/{total} = {used_percent:.2f}%")
                
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
    
    # Convert metrics to standard format
    standard_metrics = []
    for metric in metrics:
        # Remove the linux_ prefix from metric names for consistency
        if metric.name.startswith("disk_"):
            standard_metrics.append(metric)
        else:
            # Create a copy with modified name
            standard_metrics.append(
                Metric(
                    name=metric.name.replace("linux_disk_", "disk_") if metric.name.startswith("linux_disk_") else metric.name,
                    value=metric.value,
                    timestamp=metric.timestamp,
                    labels=metric.labels
                )
            )
    
    print(f"[linux_disk] Collected {len(standard_metrics)} disk metrics")
    
    return standard_metrics

def get_mount_points():
    """Get list of mount points to monitor, excluding virtual filesystems"""
    mount_points = []
    try:
        # First try to use df command output which is more reliable for actual disk usage
        import subprocess
        df_output = subprocess.check_output(["df", "-P"], universal_newlines=True)
        lines = df_output.strip().split('\n')
        
        # Skip header line
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 6:
                continue
                
            device, size, used, avail, percent, mount_point = parts
            
            # Skip pseudo filesystems
            if device in ["none", "tmpfs", "devtmpfs"] or device.startswith("udev"):
                continue
                
            # Skip bind mounts and virtual devices
            if device.startswith("/dev/loop"):
                continue
                
            print(f"[linux_disk] Found mount point: {mount_point}, device: {device}, usage: {percent}")
            mount_points.append(mount_point)
            
    except Exception as e:
        print(f"[linux_disk] Error using df command: {e}, falling back to /proc/mounts")
        
        # Fallback to /proc/mounts
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
                        
                    print(f"[linux_disk] Found mount point from /proc/mounts: {mount_point}, device: {device}, fstype: {fstype}")
                    mount_points.append(mount_point)
        except Exception as e:
            print(f"[linux_disk] Error reading mount points from /proc/mounts: {e}")
    
    if not mount_points:
        # Last resort - at least check root filesystem
        if os.path.exists("/"):
            print("[linux_disk] No mount points found, adding root (/) as fallback")
            mount_points.append("/")
    
    return mount_points