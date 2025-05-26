import requests
import time
import re
from urllib.parse import urlparse
from core.metric import Metric

def collect(config=None):
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    
    status_url = config.get("status_url", "http://localhost/nginx_status")
    timeout = config.get("timeout", 5)
    
    try:
        # Extract server and port from URL for tags
        parsed_url = urlparse(status_url)
        server = parsed_url.hostname or "localhost"
        port = str(parsed_url.port or (443 if parsed_url.scheme == "https" else 80))
        
        # Common tags for all metrics
        tags = {
            "source": "nginx",
            "server": server,
            "port": port
        }
        
        response = requests.get(status_url, timeout=timeout)
        if response.status_code != 200:
            logs.append({
                "message": f"Failed to get Nginx status: HTTP {response.status_code}",
                "level": "error",
                "tags": tags
            })
            return {"nginx_logs": logs}
            
        # Parse the basic status page
        # Example: Active connections: 43 
        # server accepts handled requests
        # 7368 7368 10993
        # Reading: 0 Writing: 5 Waiting: 38
        text = response.text.strip()
        
        # Active connections
        active_match = re.search(r'Active connections:\s+(\d+)', text)
        if active_match:
            metrics.append(Metric(
                name="nginx_active",
                value=int(active_match.group(1)),
                labels=tags.copy(),
                timestamp=timestamp
            ))
        
        # Accepts, handled, requests
        stats_match = re.search(r'(\d+)\s+(\d+)\s+(\d+)', text)
        if stats_match:
            metrics.append(Metric(
                name="nginx_accepts",
                value=int(stats_match.group(1)),
                labels=tags.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="nginx_handled",
                value=int(stats_match.group(2)),
                labels=tags.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="nginx_requests",
                value=int(stats_match.group(3)),
                labels=tags.copy(),
                timestamp=timestamp
            ))
        
        # Reading, Writing, Waiting
        reading_match = re.search(r'Reading:\s+(\d+)', text)
        writing_match = re.search(r'Writing:\s+(\d+)', text)
        waiting_match = re.search(r'Waiting:\s+(\d+)', text)
        
        if reading_match:
            metrics.append(Metric(
                name="nginx_reading",
                value=int(reading_match.group(1)),
                labels=tags.copy(),
                timestamp=timestamp
            ))
        
        if writing_match:
            metrics.append(Metric(
                name="nginx_writing",
                value=int(writing_match.group(1)),
                labels=tags.copy(),
                timestamp=timestamp
            ))
        
        if waiting_match:
            metrics.append(Metric(
                name="nginx_waiting",
                value=int(waiting_match.group(1)),
                labels=tags.copy(),
                timestamp=timestamp
            ))
        
        # Calculate dropped connections (accepts - handled)
        if stats_match:
            accepts = int(stats_match.group(1))
            handled = int(stats_match.group(2))
            dropped = accepts - handled
            
            if dropped >= 0:
                metrics.append(Metric(
                    name="nginx_dropped",
                    value=dropped,
                    labels=tags.copy(),
                    timestamp=timestamp
                ))
    
    except Exception as e:
        logs.append({
            "message": f"Error collecting Nginx metrics: {e}",
            "level": "error",
            "tags": {"source": "nginx"}
        })
    
    return {
        "nginx_metrics": metrics,
        "nginx_logs": logs
    }