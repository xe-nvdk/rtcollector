import time
import socket
import os
from core.metric import Metric
from utils.metrics import calculate_rate, create_key
from utils.debug import debug_log

def _read_netdev():
    stats = {}
    with open("/proc/net/dev", "r") as f:
        lines = f.readlines()[2:]  # skip headers
        for line in lines:
            parts = line.strip().split()
            iface = parts[0].strip(":")
            stats[iface] = {
                "rx_bytes": int(parts[1]),
                "rx_packets": int(parts[2]),
                "rx_errs": int(parts[3]),
                "rx_drop": int(parts[4]),
                "tx_bytes": int(parts[9]),
                "tx_packets": int(parts[10]),
                "tx_errs": int(parts[11]),
                "tx_drop": int(parts[12]),
            }
    return stats

def _get_interfaces(config=None):
    """Get list of network interfaces based on configuration."""
    interfaces = []
    
    # Try /sys/class/net first (more reliable)
    try:
        interfaces = os.listdir('/sys/class/net')
        # Debug logging removed for brevity
    except Exception as e:
        print(f"[linux_net] Error reading /sys/class/net: {e}")
        # Fallback to /proc/net/dev
        try:
            with open('/proc/net/dev', 'r') as f:
                lines = f.readlines()[2:]  # skip headers
                for line in lines:
                    iface = line.strip().split()[0].strip(':')
                    interfaces.append(iface)
                # Debug logging removed for brevity
        except Exception as e:
            print(f"[linux_net] Error reading /proc/net/dev: {e}")
    
    # Also try using 'ip link' command as a last resort
    if not interfaces:
        try:
            import subprocess
            result = subprocess.run(['ip', 'link'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for i in range(0, len(lines), 2):
                    if i < len(lines):
                        line = lines[i]
                        if ': ' in line:
                            iface = line.split(': ')[1].split(':')[0]
                            interfaces.append(iface)
                # Debug logging removed for brevity
        except Exception as e:
            print(f"[linux_net] Error running 'ip link': {e}")
    
    # Apply filtering based on configuration
    if config is None:
        config = {}
    
    # Get filter settings from config
    exclude_patterns = config.get('exclude_patterns', ['veth', 'docker', '^br-'])
    include_patterns = config.get('include_patterns', [])
    exclude_interfaces = config.get('exclude_interfaces', [])
    include_interfaces = config.get('include_interfaces', [])
    
    # Start with all interfaces
    filtered_interfaces = interfaces.copy()
    
    # Apply exclusion patterns
    if exclude_patterns:
        import re
        for pattern in exclude_patterns:
            regex = re.compile(pattern)
            filtered_interfaces = [iface for iface in filtered_interfaces 
                                  if not regex.search(iface)]
    
    # Remove explicitly excluded interfaces
    if exclude_interfaces:
        filtered_interfaces = [iface for iface in filtered_interfaces 
                              if iface not in exclude_interfaces]
    
    # Add interfaces that match include patterns
    if include_patterns:
        import re
        for pattern in include_patterns:
            regex = re.compile(pattern)
            for iface in interfaces:
                if regex.search(iface) and iface not in filtered_interfaces:
                    filtered_interfaces.append(iface)
    
    # Add explicitly included interfaces
    if include_interfaces:
        for iface in include_interfaces:
            if iface in interfaces and iface not in filtered_interfaces:
                filtered_interfaces.append(iface)
    
    # Debug logging removed for brevity
    return filtered_interfaces

def collect(config=None):
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    current = _read_netdev()
    metrics = []

    # Get list of interfaces (including those that might not have traffic yet)
    interfaces = _get_interfaces(config)
    
    # Create interface discovery metrics
    for iface in interfaces:
        # Add a discovery metric with unique name for each interface
        metrics.append(Metric(
            name=f"net_interface_{iface}",
            value=1,  # Just a placeholder value
            timestamp=timestamp,
            labels={"host": hostname, "interface": iface}
        ))
        
        # Also create empty rate metrics for interfaces with no traffic yet
        if iface not in current:
            labels = {"iface": iface, "host": hostname}
            # Create basic rate metrics with zero values
            metrics.append(Metric(
                name=f"net_rx_bytes_rate_{iface}",
                value=0,
                timestamp=timestamp,
                labels=labels
            ))
            metrics.append(Metric(
                name=f"net_tx_bytes_rate_{iface}",
                value=0,
                timestamp=timestamp,
                labels=labels
            ))
            metrics.append(Metric(
                name=f"net_rx_bytes_bits_rate_{iface}",
                value=0,
                timestamp=timestamp,
                labels=labels
            ))
            metrics.append(Metric(
                name=f"net_tx_bytes_bits_rate_{iface}",
                value=0,
                timestamp=timestamp,
                labels=labels
            ))
    
    # Process network traffic metrics
    for iface, vals in current.items():
        labels = {"iface": iface, "host": hostname}
        
        # Process each metric type
        for metric_type in ["rx_bytes", "tx_bytes", "rx_packets", "tx_packets", 
                           "rx_errs", "tx_errs", "rx_drop", "tx_drop"]:
            # Get the current value
            value = vals[metric_type]
            
            # Create metric name
            metric_name = f"net_{metric_type}"
            
            # Add raw counter metric
            metrics.append(Metric(
                name=metric_name,
                value=value,
                timestamp=timestamp,
                labels=labels
            ))
            
            # Calculate and add rate metric
            metric_key = create_key(f"{metric_name}_{iface}", labels)
            rate = calculate_rate(metric_key, value, timestamp)
            if rate is not None:
                # Add bytes/sec or packets/sec rate with interface in the name
                metrics.append(Metric(
                    name=f"{metric_name}_rate_{iface}",
                    value=rate,
                    timestamp=timestamp,
                    labels=labels
                ))
                
                # Keep the original metric for backward compatibility
                metrics.append(Metric(
                    name=f"{metric_name}_rate",
                    value=rate,
                    timestamp=timestamp,
                    labels=labels
                ))
                
                # For bytes metrics, also add bits/sec rate (multiply by 8)
                if metric_type in ["rx_bytes", "tx_bytes"]:
                    # Add bits/sec rate with interface in the name
                    metrics.append(Metric(
                        name=f"{metric_name}_bits_rate_{iface}",
                        value=rate * 8,  # Convert bytes to bits
                        timestamp=timestamp,
                        labels=labels
                    ))
                    
                    # Keep the original metric for backward compatibility
                    metrics.append(Metric(
                        name=f"{metric_name}_bits_rate",
                        value=rate * 8,  # Convert bytes to bits
                        timestamp=timestamp,
                        labels=labels
                    ))
    
    # Debug logging removed for brevity
    return metrics