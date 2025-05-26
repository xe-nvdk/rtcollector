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
            "macos_net_logs": [{
                "message": "macos_net plugin can only run on macOS systems",
                "level": "error",
                "tags": {"source": "macos_net"}
            }]
        }
    
    try:
        import psutil
    except ImportError:
        return {
            "macos_net_logs": [{
                "message": "psutil module is required for macos_net plugin",
                "level": "error",
                "tags": {"source": "macos_net"}
            }]
        }
    
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    current_time = time.time()
    
    try:
        # Get network I/O counters
        net_counters = psutil.net_io_counters(pernic=True)
        
        # Filter interfaces (optional)
        interfaces_to_ignore = config.get("ignore_interfaces", ["lo", "lo0", "bridge", "veth"])
        filtered_counters = {iface: stats for iface, stats in net_counters.items() 
                            if not any(ignore in iface for ignore in interfaces_to_ignore)}
        
        global _last_stats, _last_time
        if not _last_stats or _last_time == 0:
            _last_stats = filtered_counters
            _last_time = current_time
            logs.append({
                "message": "Initialized network stats, waiting for next collection cycle",
                "level": "info",
                "tags": {"source": "macos_net"}
            })
            return {"macos_net_logs": logs}
        
        # Calculate time delta in seconds
        time_delta = current_time - _last_time
        if time_delta <= 0:
            logs.append({
                "message": "Invalid time delta, skipping network metrics collection",
                "level": "warn",
                "tags": {"source": "macos_net"}
            })
            return {"macos_net_logs": logs}
        
        # Process each interface
        for iface, stats in filtered_counters.items():
            if iface not in _last_stats:
                continue
            
            prev = _last_stats[iface]
            
            # Common labels
            labels = {"source": "macos_net", "interface": iface, "host": hostname}
            
            # Calculate deltas
            bytes_sent = stats.bytes_sent - prev.bytes_sent
            bytes_recv = stats.bytes_recv - prev.bytes_recv
            packets_sent = stats.packets_sent - prev.packets_sent
            packets_recv = stats.packets_recv - prev.packets_recv
            errin = stats.errin - prev.errin
            errout = stats.errout - prev.errout
            dropin = stats.dropin - prev.dropin
            dropout = stats.dropout - prev.dropout
            
            # Calculate rates
            bytes_sent_rate = bytes_sent / time_delta
            bytes_recv_rate = bytes_recv / time_delta
            packets_sent_rate = packets_sent / time_delta
            packets_recv_rate = packets_recv / time_delta
            
            # Add metrics
            metrics.extend([
                # Raw counters
                Metric(name="net_bytes_sent", value=bytes_sent, timestamp=timestamp, labels=labels),
                Metric(name="net_bytes_recv", value=bytes_recv, timestamp=timestamp, labels=labels),
                Metric(name="net_packets_sent", value=packets_sent, timestamp=timestamp, labels=labels),
                Metric(name="net_packets_recv", value=packets_recv, timestamp=timestamp, labels=labels),
                Metric(name="net_errin", value=errin, timestamp=timestamp, labels=labels),
                Metric(name="net_errout", value=errout, timestamp=timestamp, labels=labels),
                Metric(name="net_dropin", value=dropin, timestamp=timestamp, labels=labels),
                Metric(name="net_dropout", value=dropout, timestamp=timestamp, labels=labels),
                
                # Rates
                Metric(name="net_bytes_sent_rate", value=bytes_sent_rate, timestamp=timestamp, labels=labels),
                Metric(name="net_bytes_recv_rate", value=bytes_recv_rate, timestamp=timestamp, labels=labels),
                Metric(name="net_packets_sent_rate", value=packets_sent_rate, timestamp=timestamp, labels=labels),
                Metric(name="net_packets_recv_rate", value=packets_recv_rate, timestamp=timestamp, labels=labels),
            ])
        
        # Update last stats for next collection
        _last_stats = filtered_counters
        _last_time = current_time
        
        # Add network connections count by state
        try:
            connections = psutil.net_connections()
            conn_by_state = {}
            
            for conn in connections:
                state = conn.status if conn.status else "NONE"
                conn_by_state[state] = conn_by_state.get(state, 0) + 1
            
            for state, count in conn_by_state.items():
                metrics.append(Metric(
                    name="net_connections",
                    value=count,
                    labels={"source": "macos_net", "state": state, "host": hostname},
                    timestamp=timestamp
                ))
        except (psutil.AccessDenied, PermissionError):
            logs.append({
                "message": "Permission denied when accessing network connections",
                "level": "warn",
                "tags": {"source": "macos_net"}
            })
        except Exception as e:
            logs.append({
                "message": f"Error collecting network connections: {e}",
                "level": "warn",
                "tags": {"source": "macos_net"}
            })
        
    except Exception as e:
        logs.append({
            "message": f"Error collecting macOS network metrics: {e}",
            "level": "error",
            "tags": {"source": "macos_net"}
        })
    
    return {
        "macos_net_metrics": metrics,
        "macos_net_logs": logs
    }