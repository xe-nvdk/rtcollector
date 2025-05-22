import redis
import socket
from core.metric import Metric

class Redistimeseries:
    def __init__(self, host="localhost", port=6379, db=0, retention=0, hostname=None):
        self.r = redis.Redis(host=host, port=port, db=db)
        self.retention = retention
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
                        "RETENTION", self.retention,
                        "DUPLICATE_POLICY", "LAST",
                        "LABELS", *label_args
                    )
                except redis.exceptions.ResponseError as e:
                    if "already exists" not in str(e):
                        print(f"[Redistimeseries] TS.CREATE failed: {e}")
                self.created_keys.add(key)

            args = ["TS.ADD", key, int(m.timestamp), float(m.value)]
            pipe.execute_command(*args)

        try:
            pipe.execute()
        except redis.exceptions.ResponseError as e:
            print(f"[Collector] Error in output plugin: {e}")