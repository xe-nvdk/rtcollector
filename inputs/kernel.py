import os
import time
import platform
from core.metric import Metric
from utils.system import get_hostname

def collect(config=None):
    """Collect kernel metrics."""
    if platform.system() != "Linux":
        print("[kernel] This plugin only works on Linux")
        return []
        
    hostname = get_hostname()
    timestamp = int(time.time() * 1000)
    metrics = []
    
    # Collect /proc/stat metrics
    try:
        with open("/proc/stat", "r") as f:
            for line in f:
                if line.startswith("ctxt "):
                    context_switches = int(line.split()[1])
                    metrics.append(Metric("kernel_context_switches", context_switches, timestamp, {"host": hostname}))
                elif line.startswith("btime "):
                    boot_time = int(line.split()[1])
                    metrics.append(Metric("kernel_boot_time", boot_time, timestamp, {"host": hostname}))
                elif line.startswith("intr "):
                    interrupts = int(line.split()[1])
                    metrics.append(Metric("kernel_interrupts", interrupts, timestamp, {"host": hostname}))
                elif line.startswith("processes "):
                    processes_forked = int(line.split()[1])
                    metrics.append(Metric("kernel_processes_forked", processes_forked, timestamp, {"host": hostname}))
                elif line.startswith("page "):
                    parts = line.split()
                    if len(parts) >= 3:
                        pages_in = int(parts[1])
                        pages_out = int(parts[2])
                        metrics.append(Metric("kernel_disk_pages_in", pages_in, timestamp, {"host": hostname}))
                        metrics.append(Metric("kernel_disk_pages_out", pages_out, timestamp, {"host": hostname}))
    except Exception as e:
        print(f"[kernel] Error reading /proc/stat: {e}")
    
    # Collect entropy available
    try:
        with open("/proc/sys/kernel/random/entropy_avail", "r") as f:
            entropy_avail = int(f.read().strip())
            metrics.append(Metric("kernel_entropy_avail", entropy_avail, timestamp, {"host": hostname}))
    except Exception as e:
        print(f"[kernel] Error reading entropy_avail: {e}")
    
    # Collect KSM (Kernel Samepage Merging) metrics if available
    ksm_files = {
        "full_scans": "kernel_ksm_full_scans",
        "max_page_sharing": "kernel_ksm_max_page_sharing",
        "merge_across_nodes": "kernel_ksm_merge_across_nodes",
        "pages_shared": "kernel_ksm_pages_shared",
        "pages_sharing": "kernel_ksm_pages_sharing",
        "pages_to_scan": "kernel_ksm_pages_to_scan",
        "pages_unshared": "kernel_ksm_pages_unshared",
        "pages_volatile": "kernel_ksm_pages_volatile",
        "run": "kernel_ksm_run",
        "sleep_millisecs": "kernel_ksm_sleep_millisecs",
        "stable_node_chains": "kernel_ksm_stable_node_chains",
        "stable_node_chains_prune_millisecs": "kernel_ksm_stable_node_chains_prune_millisecs",
        "stable_node_dups": "kernel_ksm_stable_node_dups",
        "use_zero_pages": "kernel_ksm_use_zero_pages"
    }
    
    ksm_dir = "/sys/kernel/mm/ksm"
    if os.path.isdir(ksm_dir):
        for filename, metric_name in ksm_files.items():
            try:
                with open(os.path.join(ksm_dir, filename), "r") as f:
                    value = int(f.read().strip())
                    metrics.append(Metric(metric_name, value, timestamp, {"host": hostname}))
            except Exception as e:
                # Skip files that don't exist or can't be read
                pass
    
    # Collect PSI (Pressure Stall Information) metrics if available
    psi_resources = ["cpu", "memory", "io"]
    psi_types = ["some", "full"]
    psi_metrics = ["avg10", "avg60", "avg300", "total"]
    
    for resource in psi_resources:
        psi_file = f"/proc/pressure/{resource}"
        if not os.path.exists(psi_file):
            continue
            
        try:
            with open(psi_file, "r") as f:
                lines = f.readlines()
                for line in lines:
                    parts = line.strip().split()
                    if not parts:
                        continue
                        
                    psi_type = parts[0].rstrip(":")
                    if psi_type not in psi_types:
                        continue
                        
                    labels = {"host": hostname, "resource": resource, "type": psi_type}
                    
                    for metric in parts[1:]:
                        name, value = metric.split("=")
                        if name in psi_metrics:
                            if name == "total":
                                # Total is an integer
                                metrics.append(Metric("kernel_pressure_total", int(value), timestamp, labels))
                            else:
                                # avg values are floats
                                metrics.append(Metric(f"kernel_pressure_{name}", float(value), timestamp, labels))
        except Exception as e:
            print(f"[kernel] Error reading PSI metrics for {resource}: {e}")
    
    # Collect file descriptor stats
    try:
        with open("/proc/sys/fs/file-nr", "r") as f:
            fields = f.read().strip().split()
            if len(fields) >= 3:
                allocated_fds = int(fields[0])
                used_fds = int(fields[0]) - int(fields[1])  # allocated - free
                max_fds = int(fields[2])
                
                metrics.append(Metric("kernel_fd_allocated", allocated_fds, timestamp, {"host": hostname}))
                metrics.append(Metric("kernel_fd_used", used_fds, timestamp, {"host": hostname}))
                metrics.append(Metric("kernel_fd_max", max_fds, timestamp, {"host": hostname}))
                
                # Add percentage used as a convenience metric
                if max_fds > 0:
                    fd_used_percent = (used_fds / max_fds) * 100
                    metrics.append(Metric("kernel_fd_used_percent", fd_used_percent, timestamp, {"host": hostname}))
    except Exception as e:
        print(f"[kernel] Error reading file descriptor stats: {e}")
    
    print(f"[kernel] Collected {len(metrics)} kernel metrics")
    return metrics