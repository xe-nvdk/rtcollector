import redis
import socket
from core.metric import Metric

class Redistimeseries:
    supports_logs = False
    supports_metrics = True
    def __init__(self, host="localhost", port=6379, db=0, retention="0", hostname=None):
        self.r = redis.Redis(host=host, port=port, db=db)
        if isinstance(retention, str):
            if retention.endswith("d"):
                self.retention = int(float(retention[:-1]) * 86400000)
            elif retention.endswith("h"):
                self.retention = int(float(retention[:-1]) * 3600000)
            elif retention.endswith("y"):
                self.retention = int(float(retention[:-1]) * 365 * 86400000)
            else:
                self.retention = int(retention)
        else:
            self.retention = int(retention)
        if self.retention == 0:
            print("\033[93m[Redistimeseries] WARNING: Retention is set to 0. Data will be stored indefinitely. This may lead to memory or disk usage issues over time.\033[0m")
        if hostname is not None and isinstance(hostname, str) and hostname.strip():
            self.hostname = hostname
        else:
            self.hostname = socket.gethostname()
        self.created_keys = set()

    def write(self, metrics):
        pipe = self.r.pipeline()
        for m in metrics:
            key = m.name
            if key not in self.created_keys:
                try:
                    labels = m.labels.copy()
                    labels["host"] = self.hostname
                    label_args = []
                    for k, v in labels.items():
                        label_args.extend([k, v])
                    self.r.execute_command(
                        "TS.CREATE", key,
                        "RETENTION", str(self.retention),
                        "DUPLICATE_POLICY", "LAST",
                        "LABELS", *label_args
                    )
                except redis.exceptions.ResponseError as e:
                    if "already exists" not in str(e):
                        print(f"[Redistimeseries] TS.CREATE failed: {e}")
                self.created_keys.add(key)

            try:
                pipe.execute_command("TS.ADD", key, int(m.timestamp), float(m.value))
            except redis.exceptions.ResponseError as e:
                if "DUPLICATE_POLICY" in str(e) or "at upsert" in str(e):
                    pipe.execute_command("TS.ADD", key, "*", float(m.value))
                else:
                    print(f"[Redistimeseries] TS.ADD failed: {e}")

        try:
            pipe.execute()
        except redis.exceptions.ResponseError as e:
            print(f"[Collector] Error in output plugin: {e}")