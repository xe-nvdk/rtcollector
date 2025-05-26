import subprocess
import json
import os
import time
from core.metric import Metric

def collect(config=None):
    metrics = []
    logs = []

    commands = config.get("commands", [])
    timeout = int(config.get("timeout", 5))
    data_format = config.get("data_format", "json")
    ignore_error = config.get("ignore_error", False)
    working_dir = config.get("working_dir", None)

    env_vars = dict(os.environ)
    for pair in config.get("environment", []):
        if "=" in pair:
            k, v = pair.split("=", 1)
            env_vars[k] = v

    for cmd in commands:
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                env=env_vars, 
                timeout=timeout,
                cwd=working_dir
            )
            if result.returncode != 0 and not ignore_error:
                logs.append({
                    "message": f"Command '{cmd}' failed with code {result.returncode}: {result.stderr.strip()}",
                    "level": "error",
                    "tags": {"source": "exec", "cmd": cmd, "exit_code": str(result.returncode)}
                })
                continue

            if data_format == "json":
                try:
                    parsed = json.loads(result.stdout)

                    if isinstance(parsed, dict) and "metrics" in parsed and "logs" in parsed:
                        for k, v in parsed["metrics"].items():
                            if not isinstance(v, (int, float)):
                                logs.append({
                                    "message": f"Metric '{k}' has non-numeric value: {v}, skipping",
                                    "level": "warn",
                                    "tags": {"source": "exec", "cmd": cmd}
                                })
                                continue
                            metrics.append(Metric(
                                name=k,
                                value=float(v),
                                labels={"source": "exec", "cmd": cmd},
                                timestamp=int(time.time() * 1000)
                            ))
                        for entry in parsed["logs"]:
                            if isinstance(entry, dict):
                                entry.setdefault("tags", {"source": "exec", "cmd": cmd})
                                logs.append(entry)
                    else:
                        for k, v in parsed.items():
                            if not isinstance(v, (int, float)):
                                logs.append({
                                    "message": f"Metric '{k}' has non-numeric value: {v}, skipping",
                                    "level": "warn",
                                    "tags": {"source": "exec", "cmd": cmd}
                                })
                                continue
                            metrics.append(Metric(
                                name=k,
                                value=float(v),
                                labels={"source": "exec", "cmd": cmd},
                                timestamp=int(time.time() * 1000)
                            ))
                except json.JSONDecodeError as je:
                    logs.append({
                        "message": f"Failed to parse JSON from '{cmd}': {je}",
                        "level": "error",
                        "tags": {"source": "exec", "cmd": cmd}
                    })
                    # Fallback if not valid JSON: record stdout and stderr as logs
                    if result.stdout.strip():
                        logs.append({
                            "message": f"stdout from '{cmd}': {result.stdout.strip()}",
                            "level": "info",
                            "tags": {"source": "exec", "cmd": cmd}
                        })
                    if result.stderr.strip():
                        logs.append({
                            "message": f"stderr from '{cmd}': {result.stderr.strip()}",
                            "level": "error",
                            "tags": {"source": "exec", "cmd": cmd}
                        })
            elif data_format == "metrics":
                for line in result.stdout.strip().splitlines():
                    parts = line.split()
                    if len(parts) >= 2:
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
                        labels = {"source": "exec", "cmd": cmd}
                        for tag in parts[2:]:
                            if "=" in tag:
                                k, v = tag.split("=", 1)
                                labels[k] = v
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
                            timestamp=ts if ts is not None else int(time.time() * 1000)
                        ))
            else:
                # Fallback if not JSON or metrics: record stdout and stderr as logs
                if result.stdout.strip():
                    logs.append({
                        "message": f"stdout from '{cmd}': {result.stdout.strip()}",
                        "level": "info",
                        "tags": {"source": "exec", "cmd": cmd}
                    })
                if result.stderr.strip():
                    logs.append({
                        "message": f"stderr from '{cmd}': {result.stderr.strip()}",
                        "level": "error",
                        "tags": {"source": "exec", "cmd": cmd}
                    })
        except subprocess.TimeoutExpired:
            logs.append({
                "message": f"Command '{cmd}' timed out after {timeout} seconds",
                "level": "error",
                "tags": {"source": "exec", "cmd": cmd, "error": "timeout"}
            })
        except Exception as e:
            logs.append({
                "message": f"Command '{cmd}' failed to run: {e}",
                "level": "error",
                "tags": {"source": "exec", "cmd": cmd, "error": str(type(e).__name__)}
            })

    result = {}
    if metrics:
        result["exec_metrics"] = metrics
    if logs:
        result["exec_logs"] = logs
    return result