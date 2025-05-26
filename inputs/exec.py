import subprocess
import json
import os
import time
import platform
import shlex
from core.metric import Metric

def collect(config=None):
    metrics = []
    logs = []
    timestamp = int(time.time() * 1000)
    hostname = os.environ.get('HOSTNAME') or platform.node()

    if not config:
        logs.append({
            "message": "No configuration provided for exec plugin",
            "level": "error",
            "tags": {"source": "exec"}
        })
        return {"exec_logs": logs}

    # Get configuration options
    commands = config.get("commands", [])
    timeout = int(config.get("timeout", 5))
    data_format = config.get("data_format", "json")
    ignore_error = config.get("ignore_error", False)
    working_dir = config.get("working_dir", None)
    shell = config.get("shell", True)
    max_output_size = config.get("max_output_size", 1048576)  # 1MB default
    add_hostname = config.get("add_hostname", True)
    
    # Set up environment variables
    env_vars = dict(os.environ)
    for pair in config.get("environment", []):
        if "=" in pair:
            k, v = pair.split("=", 1)
            env_vars[k] = v

    # Process each command
    for cmd in commands:
        cmd_start_time = time.time()
        cmd_metrics = []
        cmd_logs = []
        
        try:
            # Prepare command (split if shell=False)
            cmd_to_run = cmd if shell else shlex.split(cmd)
            
            # Execute command
            result = subprocess.run(
                cmd_to_run, 
                shell=shell, 
                capture_output=True, 
                text=True, 
                env=env_vars, 
                timeout=timeout,
                cwd=working_dir
            )
            
            # Calculate execution time
            execution_time = time.time() - cmd_start_time
            
            # Check for command failure
            if result.returncode != 0 and not ignore_error:
                cmd_logs.append({
                    "message": f"Command '{cmd}' failed with code {result.returncode}: {result.stderr.strip()}",
                    "level": "error",
                    "tags": {"source": "exec", "cmd": cmd, "exit_code": str(result.returncode)}
                })
                
                # Add execution time metric even for failed commands
                cmd_metrics.append(Metric(
                    name="exec_execution_time",
                    value=execution_time,
                    labels={"source": "exec", "cmd": cmd, "status": "error", "host": hostname if add_hostname else None},
                    timestamp=timestamp
                ))
                
                metrics.extend(cmd_metrics)
                logs.extend(cmd_logs)
                continue

            # Truncate output if too large
            stdout = result.stdout
            stderr = result.stderr
            if len(stdout) > max_output_size:
                truncated_size = len(stdout) - max_output_size
                stdout = stdout[:max_output_size]
                cmd_logs.append({
                    "message": f"Command output truncated, {truncated_size} bytes omitted",
                    "level": "warn",
                    "tags": {"source": "exec", "cmd": cmd}
                })

            # Process output based on format
            if data_format == "json":
                cmd_metrics, format_logs = _process_json_output(stdout, stderr, cmd, timestamp, hostname, add_hostname)
                cmd_logs.extend(format_logs)
            elif data_format == "metrics":
                cmd_metrics, format_logs = _process_metrics_output(stdout, stderr, cmd, timestamp, hostname, add_hostname)
                cmd_logs.extend(format_logs)
            else:
                # Fallback to plain text logging
                if stdout.strip():
                    cmd_logs.append({
                        "message": f"stdout from '{cmd}': {stdout.strip()}",
                        "level": "info",
                        "tags": {"source": "exec", "cmd": cmd}
                    })
                if stderr.strip():
                    cmd_logs.append({
                        "message": f"stderr from '{cmd}': {stderr.strip()}",
                        "level": "error",
                        "tags": {"source": "exec", "cmd": cmd}
                    })
            
            # Add execution time metric
            cmd_metrics.append(Metric(
                name="exec_execution_time",
                value=execution_time,
                labels={"source": "exec", "cmd": cmd, "status": "success", "host": hostname if add_hostname else None},
                timestamp=timestamp
            ))
            
        except subprocess.TimeoutExpired:
            cmd_logs.append({
                "message": f"Command '{cmd}' timed out after {timeout} seconds",
                "level": "error",
                "tags": {"source": "exec", "cmd": cmd, "error": "timeout"}
            })
            
            # Add execution time metric for timeout
            cmd_metrics.append(Metric(
                name="exec_execution_time",
                value=timeout,
                labels={"source": "exec", "cmd": cmd, "status": "timeout", "host": hostname if add_hostname else None},
                timestamp=timestamp
            ))
            
        except Exception as e:
            cmd_logs.append({
                "message": f"Command '{cmd}' failed to run: {e}",
                "level": "error",
                "tags": {"source": "exec", "cmd": cmd, "error": str(type(e).__name__)}
            })
            
            # Add execution time metric for error
            execution_time = time.time() - cmd_start_time
            cmd_metrics.append(Metric(
                name="exec_execution_time",
                value=execution_time,
                labels={"source": "exec", "cmd": cmd, "status": "error", "host": hostname if add_hostname else None},
                timestamp=timestamp
            ))
        
        # Add metrics and logs from this command
        metrics.extend(cmd_metrics)
        logs.extend(cmd_logs)

    result = {}
    if metrics:
        result["exec_metrics"] = metrics
    if logs:
        result["exec_logs"] = logs
    return result

def _process_json_output(stdout, stderr, cmd, timestamp, hostname, add_hostname=True):
    """Process JSON format output from command"""
    metrics = []
    logs = []
    
    try:
        parsed = json.loads(stdout)
        
        # Handle structured format with metrics and logs
        if isinstance(parsed, dict) and "metrics" in parsed and "logs" in parsed:
            # Process metrics
            for k, v in parsed["metrics"].items():
                if not isinstance(v, (int, float)):
                    logs.append({
                        "message": f"Metric '{k}' has non-numeric value: {v}, skipping",
                        "level": "warn",
                        "tags": {"source": "exec", "cmd": cmd}
                    })
                    continue
                
                labels = {"source": "exec", "cmd": cmd}
                if add_hostname:
                    labels["host"] = hostname
                
                metrics.append(Metric(
                    name=k,
                    value=float(v),
                    labels=labels,
                    timestamp=timestamp
                ))
            
            # Process logs
            for entry in parsed["logs"]:
                if isinstance(entry, dict):
                    # Add source and cmd tags if not present
                    if "tags" not in entry:
                        entry["tags"] = {}
                    entry["tags"].setdefault("source", "exec")
                    entry["tags"].setdefault("cmd", cmd)
                    logs.append(entry)
        
        # Handle simple key-value metrics
        else:
            for k, v in parsed.items():
                if not isinstance(v, (int, float)):
                    logs.append({
                        "message": f"Metric '{k}' has non-numeric value: {v}, skipping",
                        "level": "warn",
                        "tags": {"source": "exec", "cmd": cmd}
                    })
                    continue
                
                labels = {"source": "exec", "cmd": cmd}
                if add_hostname:
                    labels["host"] = hostname
                
                metrics.append(Metric(
                    name=k,
                    value=float(v),
                    labels=labels,
                    timestamp=timestamp
                ))
    
    except json.JSONDecodeError as je:
        logs.append({
            "message": f"Failed to parse JSON from '{cmd}': {je}",
            "level": "error",
            "tags": {"source": "exec", "cmd": cmd}
        })
        
        # Log stdout/stderr as fallback
        if stdout.strip():
            logs.append({
                "message": f"stdout from '{cmd}': {stdout.strip()}",
                "level": "info",
                "tags": {"source": "exec", "cmd": cmd}
            })
        if stderr.strip():
            logs.append({
                "message": f"stderr from '{cmd}': {stderr.strip()}",
                "level": "error",
                "tags": {"source": "exec", "cmd": cmd}
            })
    
    return metrics, logs

def _process_metrics_output(stdout, stderr, cmd, timestamp, hostname, add_hostname=True):
    """Process metrics format output from command"""
    metrics = []
    logs = []
    
    for line in stdout.strip().splitlines():
        parts = line.split()
        if len(parts) < 2:
            logs.append({
                "message": f"Invalid metrics line (need at least name and value): {line}",
                "level": "warn",
                "tags": {"source": "exec", "cmd": cmd}
            })
            continue
        
        name = parts[0]
        
        try:
            value = float(parts[1])
        except ValueError:
            logs.append({
                "message": f"Non-numeric value in metrics line: {line}",
                "level": "warn",
                "tags": {"source": "exec", "cmd": cmd}
            })
            continue
        
        # Process tags
        labels = {"source": "exec", "cmd": cmd}
        if add_hostname:
            labels["host"] = hostname
            
        for tag in parts[2:]:
            if "=" in tag:
                k, v = tag.split("=", 1)
                labels[k] = v
        
        # Extract timestamp if present
        ts = None
        if "ts" in labels:
            try:
                ts = int(labels.pop("ts"))
            except ValueError:
                logs.append({
                    "message": f"Invalid timestamp in metrics line: {line}",
                    "level": "warn",
                    "tags": {"source": "exec", "cmd": cmd}
                })
        
        metrics.append(Metric(
            name=name,
            value=value,
            labels=labels,
            timestamp=ts if ts is not None else timestamp
        ))
    
    # Log stderr if present
    if stderr.strip():
        logs.append({
            "message": f"stderr from '{cmd}': {stderr.strip()}",
            "level": "warn",
            "tags": {"source": "exec", "cmd": cmd}
        })
    
    return metrics, logs