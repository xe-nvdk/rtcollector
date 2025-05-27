# inputs/system.py
import os
import time
import platform
import multiprocessing
import subprocess
from datetime import datetime, timedelta
from core.metric import Metric
from utils.system import get_hostname

def get_load_avg():
    """Get system load averages for 1, 5, and 15 minutes."""
    try:
        if platform.system() == "Windows":
            # Windows doesn't have load averages
            return 0.0, 0.0, 0.0
        else:
            return os.getloadavg()
    except (AttributeError, OSError):
        return 0.0, 0.0, 0.0

def get_uptime():
    """Get system uptime in seconds."""
    if platform.system() == "Linux":
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            return int(uptime_seconds)
    elif platform.system() == "Darwin":  # macOS
        try:
            boot_time = subprocess.check_output(['sysctl', '-n', 'kern.boottime']).decode()
            boot_timestamp = int(boot_time.split()[3].strip(','))
            uptime_seconds = int(time.time()) - boot_timestamp
            return uptime_seconds
        except (subprocess.SubprocessError, ValueError, IndexError):
            return 0
    elif platform.system() == "Windows":
        try:
            uptime_ms = subprocess.check_output(['powershell', '-Command', 
                                               '(Get-CimInstance -ClassName Win32_OperatingSystem).LastBootUpTime']).decode()
            boot_time = datetime.strptime(uptime_ms.strip(), "%m/%d/%Y %I:%M:%S %p")
            uptime_seconds = (datetime.now() - boot_time).total_seconds()
            return int(uptime_seconds)
        except (subprocess.SubprocessError, ValueError):
            return 0
    return 0

def get_users():
    """Get number of logged in users and unique users."""
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output(['query', 'user']).decode()
            lines = output.strip().split('\n')
            if len(lines) <= 1:  # Header only
                return 0, 0
            users = [line.split()[0] for line in lines[1:]]
            return len(users), len(set(users))
        except (subprocess.SubprocessError, IndexError):
            return 0, 0
    else:
        try:
            output = subprocess.check_output(['who']).decode()
            lines = output.strip().split('\n')
            if not lines or lines[0] == '':
                return 0, 0
            users = [line.split()[0] for line in lines]
            return len(users), len(set(users))
        except (subprocess.SubprocessError, IndexError):
            return 0, 0

def collect(config=None):
    """Collect system metrics."""
    hostname = get_hostname()
    timestamp = int(time.time() * 1000)
    
    # Get system metrics
    load1, load5, load15 = get_load_avg()
    uptime_seconds = get_uptime()
    n_users, n_unique_users = get_users()
    n_cpus = multiprocessing.cpu_count()
    
    # Format uptime as a string (HH:MM:SS)
    uptime_formatted = str(timedelta(seconds=uptime_seconds))
    
    # Create metrics
    metrics = [
        Metric("system_load1", load1, timestamp, {"host": hostname}),
        Metric("system_load5", load5, timestamp, {"host": hostname}),
        Metric("system_load15", load15, timestamp, {"host": hostname}),
        Metric("system_n_users", n_users, timestamp, {"host": hostname}),
        Metric("system_n_unique_users", n_unique_users, timestamp, {"host": hostname}),
        Metric("system_n_cpus", n_cpus, timestamp, {"host": hostname}),
        Metric("system_uptime", uptime_seconds, timestamp, {"host": hostname}),
    ]
    
    return metrics
