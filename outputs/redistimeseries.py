import redis
import socket
from core.metric import Metric
from utils.debug import debug_log

class Redistimeseries:
    supports_logs = False
    supports_metrics = True
    def __init__(self, host="localhost", port=6379, db=0, retention="0", hostname=None, debug=False):
        self.r = redis.Redis(host=host, port=port, db=db)
        self.debug = debug
        self.config = {"debug": debug}  # Create a config dict for debug_log
        
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
        
        # Create indexes for common labels
        self._create_indexes()

    def _create_indexes(self):
        """Create indexes for common labels."""
        debug_log("Redistimeseries", "Creating indexes for common labels", self.config)
        
        # Create index for common labels using FT.CREATE if RediSearch is available
        try:
            # Try to create a RediSearch index for labels
            self.r.execute_command(
                "FT.CREATE", "idx:metrics", "ON", "HASH", "PREFIX", "1", "ts:", 
                "SCHEMA", "host", "TAG", "iface", "TAG", "interface", "TAG"
            )
            debug_log("Redistimeseries", "Created RediSearch index for labels", self.config)
        except Exception as e:
            if "Index already exists" in str(e):
                debug_log("Redistimeseries", "RediSearch index already exists", self.config)
            else:
                debug_log("Redistimeseries", f"Note: Could not create RediSearch index: {e}", self.config)
                debug_log("Redistimeseries", "Will try alternative indexing method", self.config)
                
                # Try alternative method - create dummy keys with specific labels
                try:
                    # Create a dummy time series for each common label we want to index
                    common_labels = ["host", "iface", "interface", "core", "source"]
                    for label in common_labels:
                        try:
                            # Create a dummy time series with this label
                            self.r.execute_command(
                                "TS.CREATE", f"idx:{label}", 
                                "RETENTION", "3600000",  # 1 hour retention
                                "LABELS", label, f"idx:{label}"
                            )
                            debug_log("Redistimeseries", f"Created index key for {label}", self.config)
                        except redis.exceptions.ResponseError as e:
                            if "already exists" not in str(e):
                                debug_log("Redistimeseries", f"Could not create index for {label}: {e}", self.config)
                except Exception as e:
                    debug_log("Redistimeseries", f"Error in alternative indexing: {e}", self.config)
        
        # Test if indexing works
        try:
            # Try a simple query to see if indexing works
            result = self.r.execute_command("TS.QUERYINDEX", "host=atila")
            debug_log("Redistimeseries", f"Index test result: {result}", self.config)
        except Exception as e:
            debug_log("Redistimeseries", f"Index test failed: {e}", self.config)
            debug_log("Redistimeseries", "This is expected if no metrics have been collected yet", self.config)
    
    def write(self, metrics):
        pipe = self.r.pipeline()
        for m in metrics:
            key = m.name
            if key not in self.created_keys:
                try:
                    # Ensure labels are properly formatted
                    labels = m.labels.copy() if m.labels else {}
                    
                    # Always set host label
                    if "host" not in labels:
                        labels["host"] = self.hostname
                    
                    # Format labels for TS.CREATE
                    label_args = []
                    for k, v in labels.items():
                        label_args.extend([k, str(v)])
                    
                    # Create the time series with labels
                    debug_log("Redistimeseries", f"Creating key {key} with labels: {labels}", self.config)
                    self.r.execute_command(
                        "TS.CREATE", key,
                        "RETENTION", str(self.retention),
                        "DUPLICATE_POLICY", "LAST",
                        "LABELS", *label_args
                    )
                    
                    # Explicitly create an index for this key's labels
                    for label_key, label_value in labels.items():
                        try:
                            index_query = f"{label_key}={label_value}"
                            self.r.execute_command("TS.QUERYINDEX", index_query)
                            debug_log("Redistimeseries", f"Verified index for {index_query}", self.config)
                        except Exception as e:
                            debug_log("Redistimeseries", f"Note: Index verification for {label_key}={label_value} failed: {e}", self.config)
                            
                except redis.exceptions.ResponseError as e:
                    if "already exists" not in str(e):
                        debug_log("Redistimeseries", f"TS.CREATE failed: {e}", self.config)
                self.created_keys.add(key)

            try:
                pipe.execute_command("TS.ADD", key, int(m.timestamp), float(m.value))
            except redis.exceptions.ResponseError as e:
                if "DUPLICATE_POLICY" in str(e) or "at upsert" in str(e):
                    pipe.execute_command("TS.ADD", key, "*", float(m.value))
                else:
                    debug_log("Redistimeseries", f"TS.ADD failed: {e}", self.config)

        try:
            pipe.execute()
        except redis.exceptions.ResponseError as e:
            print(f"[Collector] Error in output plugin: {e}")  # Keep this as regular print for errors