import redis
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition
from redis.commands.json.path import Path
import socket

class RedisSearch:
    def __init__(self, config=None, host="localhost", port=6379, db=0, index="logs_idx", key_prefix="log:", hostname=None):
        # Accept both config dict or direct params for compatibility
        if config is not None:
            self.host = config.get("host", host)
            self.port = config.get("port", port)
            self.db = config.get("db", db)
            self.index_name = config.get("index", index)
            self.prefix = config.get("key_prefix", key_prefix)
            self.hostname = config.get("hostname", hostname) or socket.gethostname()
        else:
            self.host = host
            self.port = port
            self.db = db
            self.index_name = index
            self.prefix = key_prefix
            self.hostname = hostname or socket.gethostname()
        self.redis = redis.Redis(host=self.host, port=self.port, db=self.db)
        self.ensure_index()

    def ensure_index(self):
        try:
            # Try to get info about the index to see if it exists
            self.redis.ft(self.index_name).info()
        except Exception:
            # Define schema for the index
            schema = (
                NumericField("$.timestamp", as_name="timestamp"),
                TextField("$.host", as_name="host"),
                TextField("$.message", as_name="message"),
                TextField("$.severity", as_name="severity"),
                TextField("$.appname", as_name="appname"),
                TextField("$.procid", as_name="procid"),
                TextField("$.msgid", as_name="msgid"),
                TextField("$.structured_data", as_name="structured_data"),
                TagField("$.facility", as_name="facility"),
                TagField("$.hostname", as_name="hostname"),
                TagField("$.program", as_name="program"),
                TextField("$.tag", as_name="tag"),
            )
            definition = IndexDefinition(prefix=[self.prefix], index_type='JSON')
            self.redis.ft(self.index_name).create_index(schema, definition=definition)

    def transform_generic_log(self, entry, default_host):
        return {
            "timestamp": int(entry.get("timestamp", 0)),
            "host": entry.get("labels", {}).get("host", default_host),
            "message": f"{entry.get('name')}: {entry.get('value')}",
            "severity": "info",
            "appname": "redis",
            "procid": "",
            "msgid": "",
            "structured_data": "",
            "facility": "monitoring",
            "hostname": entry.get("labels", {}).get("host", default_host),
            "program": "redis_exporter",
            "tag": entry.get("name")
        }

    def write(self, log_entries):
        logs_to_write = []
        for e in log_entries:
            if isinstance(e, dict):
                if "message" in e:
                    logs_to_write.append(e)
                elif "name" in e and "value" in e:
                    logs_to_write.append(self.transform_generic_log(e, self.hostname))
        if not logs_to_write:
            # print("[RedisSearch] No valid log entries to write.")
            return
        # print(f"[RedisSearch] Received {len(logs_to_write)} log entries for writing.")
        for entry in logs_to_write:
            try:
                if hasattr(entry, "to_dict") and callable(entry.to_dict):
                    data = entry.to_dict()
                elif hasattr(entry, "__dict__"):
                    data = entry.__dict__
                elif isinstance(entry, dict):
                    data = entry
                else:
                    # print(f"[RedisSearch] Skipping invalid entry type: {type(entry)}")
                    continue

                if "host" not in data:
                    data["host"] = self.hostname
                # print(f"[RedisSearch] Writing log entry data: {data}")
                key = self.redis.incr("log:id")
                redis_key = f"{self.prefix}{key}"
                self.redis.json().set(redis_key, Path.root_path(), data)
                # print(f"[RedisSearch] Written log entry to key: {redis_key}")
            except Exception as e:
                print(f"[RedisSearch] Error writing log entry: {e}")

    supports_logs = True
    supports_metrics = False
    output_type = "logs"  # Explicitly mark as logs output
