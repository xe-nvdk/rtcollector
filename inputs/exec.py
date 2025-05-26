import subprocess
import json
import os
from core.metric import Metric

def collect(config=None):
    metrics = []
    logs = []

    commands = config.get("commands", [])
    timeout = int(config.get("timeout", 5))
    data_format = config.get("data_format", "json")
    ignore_error = config.get("ignore_error", False)

    env_vars = dict(os.environ)
    for pair in config.get("environment", []):
        if "=" in pair:
            k, v = pair.split("=", 1)
            env_vars[k] = v

    for cmd in commands:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env_vars, timeout=timeout)
            if result.returncode != 0 and not ignore_error:
                logs.append({
                    "message": f"Command '{cmd}' failed with code {result.returncode}",
                    "level": "error",
                })
                continue

            if data_format == "json":
                try:
                    parsed = json.loads(result.stdout)

                    if isinstance(parsed, dict) and "metrics" in parsed and "logs" in parsed:
                        for k, v in parsed["metrics"].items():
                            metrics.append(Metric(
                                name=k,
                                value=v,
                                labels={"source": "exec", "cmd": cmd}
                            ))
                        for entry in parsed["logs"]:
                            if isinstance(entry, dict):
                                entry.setdefault("tags", {"source": "exec", "cmd": cmd})
                                logs.append(entry)
                    else:
                        for k, v in parsed.items():
                            metrics.append(Metric(
                                name=k,
                                value=v,
                                labels={"source": "exec", "cmd": cmd}
                            ))
                except Exception:
                    # Fallback if not JSON: record stdout and stderr as logs
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
                                pass

                        metrics.append(Metric(
                            name=name,
                            value=value,
                            labels=labels,
                            timestamp=ts
                        ))
            else:
                # Fallback if not JSON: record stdout and stderr as logs
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
        except Exception as e:
            logs.append({
                "message": f"Command '{cmd}' failed to run: {e}",
                "level": "error",
                "tags": {"source": "exec", "cmd": cmd}
            })

    result = {}
    if metrics:
        result["exec_metrics"] = metrics
    if logs:
        result["exec_logs"] = logs
    print(f"[exec] Returning: metrics={metrics}, logs={logs}")
    return result