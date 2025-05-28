import os
import time
import platform
import subprocess
from core.metric import Metric
from utils.system import get_hostname
from utils.debug import debug_log

def collect(config=None):
    """Collect process-related metrics including counts of processes by state."""
    hostname = get_hostname()
    timestamp = int(time.time() * 1000)
    metrics = []
    
    system = platform.system()
    
    if system == "Linux":
        metrics = collect_linux_processes(hostname, timestamp, config)
    elif system == "Darwin":  # macOS
        metrics = collect_macos_processes(hostname, timestamp, config)
    elif system == "Windows":
        metrics = collect_windows_processes(hostname, timestamp, config)
    else:
        print(f"[processes] Unsupported platform: {system}")
    
    return metrics

def collect_linux_processes(hostname, timestamp, config=None):
    """Collect process metrics on Linux by reading /proc."""
    metrics = []
    
    # Initialize counters
    states = {
        "running": 0,
        "sleeping": 0,
        "stopped": 0,
        "zombie": 0,
        "dead": 0,
        "paging": 0,
        "blocked": 0,
        "parked": 0,
        "idle": 0,
        "total": 0
    }
    total_threads = 0
    
    try:
        # Iterate through all process directories in /proc
        for pid_dir in os.listdir('/proc'):
            if not pid_dir.isdigit():
                continue
                
            try:
                # Read process state
                with open(f'/proc/{pid_dir}/stat', 'r') as f:
                    stat = f.read().split()
                    if len(stat) < 3:
                        continue
                        
                    # State is the 3rd field
                    state = stat[2]
                    
                    # Count by state
                    if state == 'R':
                        states["running"] += 1
                    elif state == 'S':
                        states["sleeping"] += 1
                    elif state == 'D':
                        states["blocked"] += 1
                    elif state == 'Z':
                        states["zombie"] += 1
                    elif state == 'T':
                        states["stopped"] += 1
                    elif state == 'X':
                        states["dead"] += 1
                    elif state == 'W':
                        states["paging"] += 1
                    elif state == 'P':
                        states["parked"] += 1
                    elif state == 'I':
                        states["idle"] += 1
                        
                    states["total"] += 1
                    
                    # Count threads (20th field in stat)
                    if len(stat) >= 20:
                        try:
                            threads = int(stat[19])
                            total_threads += threads
                        except (ValueError, IndexError):
                            pass
                            
            except (IOError, OSError, IndexError):
                continue
                
        # Create metrics
        labels = {"host": hostname}
        for state, count in states.items():
            metrics.append(Metric(f"processes_{state}", count, timestamp, labels))
            
        metrics.append(Metric("processes_total_threads", total_threads, timestamp, labels))
        
        # Debug logging removed for brevity
        
    except Exception as e:
        print(f"[processes] Error collecting Linux process metrics: {e}")
        
    return metrics

def collect_macos_processes(hostname, timestamp, config=None):
    """Collect process metrics on macOS using ps command."""
    metrics = []
    
    # Initialize counters
    states = {
        "running": 0,
        "sleeping": 0,
        "stopped": 0,
        "zombie": 0,
        "idle": 0,
        "total": 0
    }
    total_threads = 0
    
    try:
        # Use ps command to get process states
        ps_output = subprocess.check_output(['ps', '-eo', 'stat,thcount'], universal_newlines=True)
        lines = ps_output.strip().split('\n')[1:]  # Skip header
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.split()
            if not parts:
                continue
                
            state = parts[0][0]  # First character of stat
            
            # Count by state
            if state == 'R':
                states["running"] += 1
            elif state == 'S' or state == 'I':
                states["sleeping"] += 1
            elif state == 'T':
                states["stopped"] += 1
            elif state == 'Z':
                states["zombie"] += 1
            elif state == 'W':
                states["idle"] += 1
                
            states["total"] += 1
            
            # Count threads if available
            if len(parts) > 1:
                try:
                    threads = int(parts[1])
                    total_threads += threads
                except ValueError:
                    pass
                    
        # Create metrics
        labels = {"host": hostname}
        for state, count in states.items():
            metrics.append(Metric(f"processes_{state}", count, timestamp, labels))
            
        metrics.append(Metric("processes_total_threads", total_threads, timestamp, labels))
        
        # Debug logging removed for brevity
        
    except Exception as e:
        print(f"[processes] Error collecting macOS process metrics: {e}")
        
    return metrics

def collect_windows_processes(hostname, timestamp, config=None):
    """Collect process metrics on Windows using wmic."""
    metrics = []
    
    # Initialize counters
    states = {
        "running": 0,
        "total": 0
    }
    total_threads = 0
    
    try:
        # Get process count
        wmic_output = subprocess.check_output(['wmic', 'process', 'get', 'ProcessId'], universal_newlines=True)
        lines = wmic_output.strip().split('\n')[1:]  # Skip header
        states["total"] = len([line for line in lines if line.strip()])
        states["running"] = states["total"]  # Windows doesn't easily expose process states
        
        # Get thread count
        wmic_output = subprocess.check_output(['wmic', 'process', 'get', 'ThreadCount'], universal_newlines=True)
        lines = wmic_output.strip().split('\n')[1:]  # Skip header
        for line in lines:
            if line.strip():
                try:
                    total_threads += int(line.strip())
                except ValueError:
                    pass
                    
        # Create metrics
        labels = {"host": hostname}
        for state, count in states.items():
            metrics.append(Metric(f"processes_{state}", count, timestamp, labels))
            
        metrics.append(Metric("processes_total_threads", total_threads, timestamp, labels))
        
        # Debug logging removed for brevity
        
    except Exception as e:
        print(f"[processes] Error collecting Windows process metrics: {e}")
        
    return metrics