import os
import time
import socket
import platform
from core.metric import Metric
from utils.metrics import calculate_rate, create_key
from utils.debug import debug_log

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
    
    # Get configuration
    if config is None:
        config = {}
    
    # Get mount point filtering options
    exclude_mounts = config.get('exclude_mounts', [])
    exclude_docker = config.get('exclude_docker', True)  # Default to excluding Docker mounts
    include_mounts = config.get('include_mounts', [])
    
    # Debug logging removed for brevity
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    
    try:
        # Get mount points to monitor
        mount_points = get_mount_points(config)
        
        # Create discovery metrics for all mount points
        for mount in mount_points:
            # Skip excluded mount points
            if exclude_mounts and mount in exclude_mounts:
                continue
                
            # Skip mount points not in include_mounts if specified
            if include_mounts and mount not in include_mounts and len(include_mounts) > 0:
                continue
                
            # Add discovery metric for this mount point
            mount_key = mount.replace('/', '_').strip('_')
            if not mount_key and mount == "/":
                mount_key = "root"  # For root directory
                
            metrics.append(Metric(
                name=f"disk_mountpoint_{mount_key}",
                value=1,  # Just a placeholder value
                timestamp=timestamp,
                labels={"host": hostname, "mountpoint": mount if mount != "/" else "root"}
            ))
        
        # Collect disk usage metrics for each mount point
        for mount in mount_points:
            # Skip excluded mount points
            if exclude_mounts and mount in exclude_mounts:
                continue
                
            # Skip mount points not in include_mounts if specified
            if include_mounts and mount not in include_mounts and len(include_mounts) > 0:
                continue
            try:
                stats = os.statvfs(mount)
                
                # Calculate disk space metrics
                total = stats.f_blocks * stats.f_frsize
                free = stats.f_bfree * stats.f_frsize
                available = stats.f_bavail * stats.f_frsize  # Available to non-root users
                used = total - free
                used_percent = (used / total) * 100 if total > 0 else 0
                
                # Debug output
                # Only log detailed metrics in debug mode
                
                # Calculate inodes metrics
                inodes_total = stats.f_files
                inodes_free = stats.f_ffree
                inodes_used = inodes_total - inodes_free
                inodes_percent = (inodes_used / inodes_total) * 100 if inodes_total > 0 else 0
                
                # Common labels - use "root" instead of "/" for the root mount point
                labels = {"source": "linux_disk", "mount": "root" if mount == "/" else mount, "host": hostname}
                
                # Add disk space metrics
                metrics.extend([
                    Metric(name="disk_total", value=total, timestamp=timestamp, labels=labels),
                    Metric(name="disk_used", value=used, timestamp=timestamp, labels=labels),
                    Metric(name="disk_free", value=free, timestamp=timestamp, labels=labels),
                    Metric(name="disk_available", value=available, timestamp=timestamp, labels=labels),
                    Metric(name="disk_used_percent", value=used_percent, timestamp=timestamp, labels=labels),
                ])
                
                # Add mount-specific metrics with mount point in the key
                # Replace slashes with underscores for valid metric names
                mount_key = mount.replace('/', '_').strip('_')
                if not mount_key:
                    mount_key = "root"  # For root directory
                
                # Debug output to help diagnose the issue
                print(f"[linux_disk] Processing mount point: {mount}, mount_key: {mount_key}")
                    
                metrics.extend([
                    Metric(name=f"disk_total_{mount_key}", value=total, timestamp=timestamp, labels=labels),
                    Metric(name=f"disk_used_{mount_key}", value=used, timestamp=timestamp, labels=labels),
                    Metric(name=f"disk_free_{mount_key}", value=free, timestamp=timestamp, labels=labels),
                    Metric(name=f"disk_used_percent_{mount_key}", value=used_percent, timestamp=timestamp, labels=labels),
                ])
                
                # Add inode metrics
                metrics.extend([
                    Metric(name="disk_inodes_total", value=inodes_total, timestamp=timestamp, labels=labels),
                    Metric(name="disk_inodes_used", value=inodes_used, timestamp=timestamp, labels=labels),
                    Metric(name="disk_inodes_free", value=inodes_free, timestamp=timestamp, labels=labels),
                    Metric(name="disk_inodes_percent", value=inodes_percent, timestamp=timestamp, labels=labels),
                ])
                
                # Add mount-specific inode metrics with mount point in the key
                metrics.extend([
                    Metric(name=f"disk_inodes_total_{mount_key}", value=inodes_total, timestamp=timestamp, labels=labels),
                    Metric(name=f"disk_inodes_used_{mount_key}", value=inodes_used, timestamp=timestamp, labels=labels),
                    Metric(name=f"disk_inodes_free_{mount_key}", value=inodes_free, timestamp=timestamp, labels=labels),
                    Metric(name=f"disk_inodes_percent_{mount_key}", value=inodes_percent, timestamp=timestamp, labels=labels),
                        # Add direct key names for easier ts.range queries
                    Metric(name=f"inodes_total_{mount_key}", value=inodes_total, timestamp=timestamp, labels=labels),
                    Metric(name=f"inodes_used_{mount_key}", value=inodes_used, timestamp=timestamp, labels=labels),
                    Metric(name=f"inodes_free_{mount_key}", value=inodes_free, timestamp=timestamp, labels=labels),
                    
                    # Always add root-specific metrics for the root filesystem
                    Metric(name=f"inodes_total_root" if mount == "/" else f"inodes_total_root_skip", value=inodes_total, timestamp=timestamp, labels=labels),
                    Metric(name=f"inodes_used_root" if mount == "/" else f"inodes_used_root_skip", value=inodes_used, timestamp=timestamp, labels=labels),
                    Metric(name=f"inodes_free_root" if mount == "/" else f"inodes_free_root_skip", value=inodes_free, timestamp=timestamp, labels=labels),
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
    
    # Debug logging removed for brevity
    
    return standard_metrics

def get_mount_points(config=None):
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
                
            # Skip Docker overlay mounts if configured to do so
            if config.get('exclude_docker', True) and (mount_point.startswith("/var/lib/docker/overlay") or "docker" in device):
                continue
                
            # Debug logging removed for brevity
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
                        
                    # Skip Docker overlay mounts if configured to do so
                    if config.get('exclude_docker', True) and (mount_point.startswith("/var/lib/docker/overlay") or fstype == "overlay"):
                        continue
                        
                    # Debug logging removed for brevity
                    mount_points.append(mount_point)
        except Exception as e:
            print(f"[linux_disk] Error reading mount points from /proc/mounts: {e}")
    
    if not mount_points:
        # Last resort - at least check root filesystem
        if os.path.exists("/"):
            # Debug logging removed for brevity
            mount_points.append("/")
    
    return mount_points