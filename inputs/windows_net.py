import psutil
import time
import platform
from core.metric import Metric

def collect(config=None):
    # Verify we're on Windows
    if platform.system() != "Windows":
        return {
            "windows_net_logs": [{
                "message": "windows_net plugin can only run on Windows systems",
                "level": "error",
                "tags": {"source": "windows_net"}
            }]
        }
    
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    
    try:
        # Get network I/O statistics
        net_io = psutil.net_io_counters(pernic=True)
        for interface, counters in net_io.items():
            # Skip loopback interfaces
            if interface.lower().startswith('lo') or interface.lower() == 'loopback':
                continue
                
            labels = {"source": "windows_net", "interface": interface}
            
            metrics.append(Metric(
                name="windows_net_bytes_sent",
                value=counters.bytes_sent,
                labels=labels.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="windows_net_bytes_recv",
                value=counters.bytes_recv,
                labels=labels.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="windows_net_packets_sent",
                value=counters.packets_sent,
                labels=labels.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="windows_net_packets_recv",
                value=counters.packets_recv,
                labels=labels.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="windows_net_errin",
                value=counters.errin,
                labels=labels.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="windows_net_errout",
                value=counters.errout,
                labels=labels.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="windows_net_dropin",
                value=counters.dropin,
                labels=labels.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="windows_net_dropout",
                value=counters.dropout,
                labels=labels.copy(),
                timestamp=timestamp
            ))
        
        # Get network connection counts
        try:
            connections = psutil.net_connections()
            conn_counts = {
                'ESTABLISHED': 0,
                'SYN_SENT': 0,
                'SYN_RECV': 0,
                'FIN_WAIT1': 0,
                'FIN_WAIT2': 0,
                'TIME_WAIT': 0,
                'CLOSE': 0,
                'CLOSE_WAIT': 0,
                'LAST_ACK': 0,
                'LISTEN': 0,
                'CLOSING': 0,
                'NONE': 0
            }
            
            for conn in connections:
                if conn.status in conn_counts:
                    conn_counts[conn.status] += 1
                else:
                    conn_counts['NONE'] += 1
            
            for status, count in conn_counts.items():
                metrics.append(Metric(
                    name="windows_net_connections",
                    value=count,
                    labels={"source": "windows_net", "status": status},
                    timestamp=timestamp
                ))
        except psutil.AccessDenied:
            # This requires admin privileges on Windows
            logs.append({
                "message": "Access denied when collecting network connection stats. Try running with administrator privileges.",
                "level": "warn",
                "tags": {"source": "windows_net"}
            })
        
    except Exception as e:
        logs.append({
            "message": f"Error collecting Windows network metrics: {e}",
            "level": "error",
            "tags": {"source": "windows_net"}
        })
    
    return {
        "windows_net_metrics": metrics,
        "windows_net_logs": logs
    }