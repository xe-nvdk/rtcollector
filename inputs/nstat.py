import time
import socket
import os
from core.metric import Metric
from utils.metrics import calculate_rate, create_key
from utils.debug import debug_log

def collect(config=None):
    """Collect network statistics from /proc/net/snmp."""
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    metrics = []
    
    try:
        # Read /proc/net/snmp
        with open('/proc/net/snmp', 'r') as f:
            lines = f.readlines()
            
            # Process each protocol section (Ip, Icmp, Tcp, Udp, etc.)
            for i in range(0, len(lines), 2):
                if i+1 < len(lines):
                    header_line = lines[i].strip()
                    values_line = lines[i+1].strip()
                    
                    header_parts = header_line.split()
                    values_parts = values_line.split()
                    
                    if len(header_parts) != len(values_parts):
                        continue
                    
                    protocol = header_parts[0].rstrip(':').lower()
                    
                    # Process each metric for this protocol
                    for j in range(1, len(header_parts)):
                        metric_name = header_parts[j]
                        try:
                            value = int(values_parts[j])
                            
                            # Create the full metric name
                            full_metric_name = f"nstat_{protocol}_{metric_name}"
                            labels = {"host": hostname}
                            
                            # Add raw counter metric
                            metrics.append(Metric(
                                name=full_metric_name,
                                value=value,
                                timestamp=timestamp,
                                labels=labels
                            ))
                            
                            # Calculate and add rate metric
                            metric_key = create_key(full_metric_name, labels)
                            rate = calculate_rate(metric_key, value, timestamp)
                            if rate is not None:
                                metrics.append(Metric(
                                    name=f"{full_metric_name}_rate",
                                    value=rate,
                                    timestamp=timestamp,
                                    labels=labels
                                ))
                        except (ValueError, IndexError):
                            continue
        
        # Process IPv6 statistics from /proc/net/snmp6
        try:
            if os.path.exists('/proc/net/snmp6'):
                with open('/proc/net/snmp6', 'r') as f:
                    lines = f.readlines()
                    
                    for line in lines:
                        parts = line.strip().split()
                        if len(parts) == 2:
                            metric_name = parts[0]
                            try:
                                value = int(parts[1])
                                
                                # Create the full metric name
                                full_metric_name = f"nstat_ip6_{metric_name}"
                                labels = {"host": hostname}
                                
                                # Add raw counter metric
                                metrics.append(Metric(
                                    name=full_metric_name,
                                    value=value,
                                    timestamp=timestamp,
                                    labels=labels
                                ))
                                
                                # Calculate and add rate metric
                                metric_key = create_key(full_metric_name, labels)
                                rate = calculate_rate(metric_key, value, timestamp)
                                if rate is not None:
                                    metrics.append(Metric(
                                        name=f"{full_metric_name}_rate",
                                        value=rate,
                                        timestamp=timestamp,
                                        labels=labels
                                    ))
                            except ValueError:
                                continue
        except Exception as e:
            print(f"[nstat] Error collecting IPv6 statistics: {e}")
        
        # Debug logging removed for brevity
    except Exception as e:
        print(f"[nstat] Error collecting network statistics: {e}")
    
    return metrics