import requests
import time
import re
import ssl
import socket
from datetime import datetime
from urllib.parse import urlparse
from core.metric import Metric

def collect(config=None):
    metrics = []
    logs = []
    
    urls = config.get("urls", [])
    method = config.get("method", "GET")
    timeout = config.get("timeout", 5)
    follow_redirects = config.get("follow_redirects", True)
    headers = config.get("headers", {})
    body = config.get("body", "")
    insecure_skip_verify = config.get("insecure_skip_verify", False)
    response_body_field = config.get("response_body_field", "")
    response_body_max_size = config.get("response_body_max_size", 32768)
    response_string_match = config.get("response_string_match", "")
    response_status_code = config.get("response_status_code", 0)
    interface = config.get("interface", "")
    
    for url in urls:
        start_time = time.time()
        url_parsed = urlparse(url)
        
        labels = {
            "source": "http_response",
            "server": url_parsed.netloc,
            "method": method,
            "url": url,
            "scheme": url_parsed.scheme,
            "host": url_parsed.netloc.split(':')[0] if ':' in url_parsed.netloc else url_parsed.netloc
        }
        
        try:
            # Set up session with options
            session = requests.Session()
            
            if not follow_redirects:
                session.max_redirects = 0
            
            # Set SSL verification
            verify = not insecure_skip_verify
            
            # Make the request
            response = session.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                timeout=timeout,
                allow_redirects=follow_redirects,
                verify=verify
            )
            
            response_time = time.time() - start_time
            response_size = len(response.content)
            
            # Check SSL certificate if HTTPS
            cert_expiry = 0
            if url_parsed.scheme == 'https':
                try:
                    hostname = url_parsed.netloc.split(':')[0]
                    port = url_parsed.port or 443
                    context = ssl.create_default_context()
                    if insecure_skip_verify:
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                    
                    with socket.create_connection((hostname, port)) as sock:
                        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                            cert = ssock.getpeercert()
                            if cert and 'notAfter' in cert:
                                expires = ssl.cert_time_to_seconds(cert['notAfter'])
                                cert_expiry = expires - time.time()
                except Exception as e:
                    logs.append({
                        "message": f"Failed to check SSL certificate for {url}: {e}",
                        "level": "warn",
                        "tags": labels
                    })
            
            # Check for string match if configured
            response_string_found = 0
            if response_string_match and response.text:
                if re.search(response_string_match, response.text):
                    response_string_found = 1
            
            # Check status code match if configured
            response_status_code_match = 0
            if response_status_code > 0:
                if response.status_code == response_status_code:
                    response_status_code_match = 1
            
            # Add metrics
            metrics.append(Metric(
                name="http_response_response_time",
                value=response_time,
                labels=labels.copy(),
                timestamp=int(time.time() * 1000)
            ))
            
            metrics.append(Metric(
                name="http_response_status_code",
                value=response.status_code,
                labels=labels.copy(),
                timestamp=int(time.time() * 1000)
            ))
            
            metrics.append(Metric(
                name="http_response_content_length",
                value=response_size,
                labels=labels.copy(),
                timestamp=int(time.time() * 1000)
            ))
            
            if response_string_match:
                metrics.append(Metric(
                    name="http_response_string_match",
                    value=response_string_found,
                    labels=labels.copy(),
                    timestamp=int(time.time() * 1000)
                ))
            
            if response_status_code > 0:
                metrics.append(Metric(
                    name="http_response_status_code_match",
                    value=response_status_code_match,
                    labels=labels.copy(),
                    timestamp=int(time.time() * 1000)
                ))
            
            if cert_expiry > 0:
                metrics.append(Metric(
                    name="http_response_cert_expiry",
                    value=cert_expiry,
                    labels=labels.copy(),
                    timestamp=int(time.time() * 1000)
                ))
            
            # Store response body if requested
            if response_body_field and response.text:
                truncated_body = response.text[:response_body_max_size]
                logs.append({
                    "message": f"Response body for {url}",
                    "level": "info",
                    "tags": labels,
                    response_body_field: truncated_body
                })
            
        except requests.exceptions.Timeout:
            logs.append({
                "message": f"HTTP request to {url} timed out after {timeout}s",
                "level": "error",
                "tags": labels
            })
            
            metrics.append(Metric(
                name="http_response_result_code",
                value=1,  # 1 = timeout
                labels=labels.copy(),
                timestamp=int(time.time() * 1000)
            ))
            
        except requests.exceptions.ConnectionError as e:
            logs.append({
                "message": f"Connection error for {url}: {e}",
                "level": "error",
                "tags": labels
            })
            
            metrics.append(Metric(
                name="http_response_result_code",
                value=2,  # 2 = connection error
                labels=labels.copy(),
                timestamp=int(time.time() * 1000)
            ))
            
        except requests.exceptions.RequestException as e:
            logs.append({
                "message": f"HTTP request error for {url}: {e}",
                "level": "error",
                "tags": labels
            })
            
            metrics.append(Metric(
                name="http_response_result_code",
                value=3,  # 3 = general error
                labels=labels.copy(),
                timestamp=int(time.time() * 1000)
            ))
            
        except Exception as e:
            logs.append({
                "message": f"Unexpected error for {url}: {e}",
                "level": "error",
                "tags": labels
            })
            
            metrics.append(Metric(
                name="http_response_result_code",
                value=4,  # 4 = unexpected error
                labels=labels.copy(),
                timestamp=int(time.time() * 1000)
            ))
    
    result = {}
    if metrics:
        result["http_response_metrics"] = metrics
    if logs:
        result["http_response_logs"] = logs
    return result