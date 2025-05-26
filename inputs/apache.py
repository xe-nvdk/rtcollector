import requests
import time
import re
from core.metric import Metric

def collect(config=None):
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    
    status_url = config.get("status_url", "http://localhost/server-status?auto")
    timeout = config.get("timeout", 5)
    
    try:
        response = requests.get(status_url, timeout=timeout)
        if response.status_code != 200:
            logs.append({
                "message": f"Failed to get Apache status: HTTP {response.status_code}",
                "level": "error",
                "tags": {"source": "apache"}
            })
            return {"apache_logs": logs}
        
        # Parse the ?auto format which returns plain text key-value pairs
        metrics_map = {
            'Total Accesses:': ('apache_TotalAccesses', float),
            'Total kBytes:': ('apache_TotalkBytes', float),
            'CPULoad:': ('apache_CPULoad', float),
            'Uptime:': ('apache_Uptime', float),
            'ReqPerSec:': ('apache_ReqPerSec', float),
            'BytesPerSec:': ('apache_BytesPerSec', float),
            'BytesPerReq:': ('apache_BytesPerReq', float),
            'BusyWorkers:': ('apache_BusyWorkers', float),
            'IdleWorkers:': ('apache_IdleWorkers', float),
            'ConnsTotal:': ('apache_ConnsTotal', float),
            'ConnsAsyncWriting:': ('apache_ConnsAsyncWriting', float),
            'ConnsAsyncKeepAlive:': ('apache_ConnsAsyncKeepAlive', float),
            'ConnsAsyncClosing:': ('apache_ConnsAsyncClosing', float),
            'ServerUptimeSeconds:': ('apache_ServerUptimeSeconds', float),
            'Load1:': ('apache_Load1', float),
            'Load5:': ('apache_Load5', float),
            'Load15:': ('apache_Load15', float),
            'CPUUser:': ('apache_CPUUser', float),
            'CPUSystem:': ('apache_CPUSystem', float),
            'CPUChildrenUser:': ('apache_CPUChildrenUser', float),
            'CPUChildrenSystem:': ('apache_CPUChildrenSystem', float),
            'ParentServerConfigGeneration:': ('apache_ParentServerConfigGeneration', float),
            'ParentServerMPMGeneration:': ('apache_ParentServerMPMGeneration', float),
            'Scoreboard:': ('apache_scoreboard', parse_scoreboard)
        }
        
        for line in response.text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
                
            for prefix, (metric_name, converter) in metrics_map.items():
                if line.startswith(prefix):
                    value_str = line[len(prefix):].strip()
                    
                    if metric_name == 'apache_scoreboard':
                        scoreboard_metrics = converter(value_str, timestamp)
                        metrics.extend(scoreboard_metrics)
                    else:
                        try:
                            value = converter(value_str)
                            metrics.append(Metric(
                                name=metric_name,
                                value=value,
                                labels={"source": "apache"},
                                timestamp=timestamp
                            ))
                        except (ValueError, TypeError) as e:
                            logs.append({
                                "message": f"Failed to parse Apache metric {metric_name}: {e}",
                                "level": "warn",
                                "tags": {"source": "apache"}
                            })
                    break
    
    except Exception as e:
        logs.append({
            "message": f"Error collecting Apache metrics: {e}",
            "level": "error",
            "tags": {"source": "apache"}
        })
    
    return {
        "apache_metrics": metrics,
        "apache_logs": logs
    }

def parse_scoreboard(scoreboard, timestamp):
    """Parse Apache scoreboard string into metrics"""
    metrics = []
    
    # Scoreboard key:
    # "_" Waiting for Connection
    # "S" Starting up
    # "R" Reading Request
    # "W" Sending Reply
    # "K" Keepalive (read)
    # "D" DNS Lookup
    # "C" Closing connection
    # "L" Logging
    # "G" Gracefully finishing
    # "I" Idle cleanup of worker
    # "." Open slot with no current process
    
    states = {
        '_': 'waiting',
        'S': 'starting',
        'R': 'reading',
        'W': 'sending',
        'K': 'keepalive',
        'D': 'dnslookup',
        'C': 'closing',
        'L': 'logging',
        'G': 'finishing',
        'I': 'idle_cleanup',
        '.': 'open'
    }
    
    counts = {state: 0 for state in states.values()}
    
    for char in scoreboard:
        if char in states:
            counts[states[char]] += 1
    
    for state, count in counts.items():
        metrics.append(Metric(
            name=f"apache_scboard_{state}",
            value=float(count),
            labels={"source": "apache"},
            timestamp=timestamp
        ))
    
    return metrics