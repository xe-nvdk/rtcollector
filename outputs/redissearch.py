import redis
import json
import time
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
            self.debug = config.get("debug", False)
        else:
            self.host = host
            self.port = port
            self.db = db
            self.index_name = index
            self.prefix = key_prefix
            self.hostname = hostname or socket.gethostname()
            self.debug = False
            
        # Connect to Redis
        try:
            self.redis = redis.Redis(host=self.host, port=self.port, db=self.db)
            # Test connection
            self.redis.ping()
            if self.debug:
                print(f"[RedisSearch] Successfully connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            print(f"[RedisSearch] Failed to connect to Redis at {self.host}:{self.port}: {e}")
            self.redis = None
            
        # Create or verify the index
        self.ensure_index()

    def ensure_index(self):
        """Ensure the search index exists with the correct schema"""
        if not self.redis:
            print("[RedisSearch] Cannot ensure index: Redis connection not available")
            return False
            
        try:
            # Check if index exists
            try:
                # Try to get info about the index
                self.redis.execute_command('FT.INFO', self.index_name)
                if self.debug:
                    print(f"[RedisSearch] Index {self.index_name} already exists")
            except redis.exceptions.ResponseError as e:
                if "unknown index" in str(e).lower():
                    # Index doesn't exist, create it
                    if self.debug:
                        print(f"[RedisSearch] Creating index {self.index_name}")
                    
                    # Create index using raw Redis command
                    create_cmd = [
                        'FT.CREATE', self.index_name,
                        'ON', 'JSON',
                        'PREFIX', '1', self.prefix,
                        'SCHEMA',
                        '$.timestamp', 'AS', 'timestamp', 'NUMERIC', 'SORTABLE',
                        '$.message', 'AS', 'message', 'TEXT',
                        '$.level', 'AS', 'level', 'TEXT',
                        '$.appname', 'AS', 'appname', 'TEXT',
                        '$.procid', 'AS', 'procid', 'TEXT',
                        '$.host', 'AS', 'host', 'TEXT',
                        '$.remote_ip', 'AS', 'remote_ip', 'TEXT',
                        '$.name', 'AS', 'name', 'TEXT',
                        '$.facility', 'AS', 'facility', 'TAG',
                        '$.severity', 'AS', 'severity', 'TAG',
                        '$.source', 'AS', 'source', 'TAG'
                    ]
                    
                    try:
                        self.redis.execute_command(*create_cmd)
                        if self.debug:
                            print(f"[RedisSearch] Successfully created index {self.index_name}")
                    except Exception as create_err:
                        print(f"[RedisSearch] Error creating index: {create_err}")
                        return False
                else:
                    print(f"[RedisSearch] Error checking index: {e}")
                    return False
                    
            return True
                
        except Exception as e:
            print(f"[RedisSearch] Failed to ensure index: {e}")
            return False

    def write(self, log_entries):
        """Write log entries to Redis"""
        # Ensure Redis connection
        if not self.redis:
            try:
                self.redis = redis.Redis(host=self.host, port=self.port, db=self.db)
                self.redis.ping()
                # Ensure index exists
                self.ensure_index()
            except Exception as e:
                print(f"[RedisSearch] Failed to reconnect to Redis: {e}")
                return
                
        logs_to_write = []
        
        # Process and filter log entries
        for e in log_entries:
            if isinstance(e, dict):
                # Handle syslog-style entries
                if "name" in e and isinstance(e.get("name"), str) and e.get("name", "").startswith("syslog_"):
                    if self.debug:
                        print(f"[RedisSearch] Processing syslog entry: {e}")
                    logs_to_write.append(e)
                # Handle message-style entries
                elif "message" in e:
                    if self.debug:
                        print(f"[RedisSearch] Processing message entry: {e}")
                    logs_to_write.append(e)
        
        if not logs_to_write:
            if self.debug:
                print("[RedisSearch] No valid log entries to write")
            return
            
        if self.debug:
            print(f"[RedisSearch] Writing {len(logs_to_write)} log entries")
        
        # Write each log entry to Redis
        for entry in logs_to_write:
            try:
                # Convert entry to a dictionary if it's not already
                if hasattr(entry, "to_dict") and callable(entry.to_dict):
                    data = entry.to_dict()
                elif hasattr(entry, "__dict__"):
                    data = entry.__dict__
                elif isinstance(entry, dict):
                    data = entry
                else:
                    if self.debug:
                        print(f"[RedisSearch] Skipping invalid entry type: {type(entry)}")
                    continue

                # Ensure required fields
                if "host" not in data:
                    data["host"] = self.hostname
                if "timestamp" not in data:
                    data["timestamp"] = int(time.time() * 1000)
                if "level" not in data and "severity" in data:
                    data["level"] = data["severity"]
                if "source" not in data:
                    data["source"] = "unknown"
                
                # Generate a unique key
                key = self.redis.incr("log:id")
                redis_key = f"{self.prefix}{key}"
                
                # Store the log entry using JSON.SET
                json_str = json.dumps(data)
                if self.debug:
                    print(f"[RedisSearch] Writing to {redis_key}: {json_str[:100]}...")
                    
                self.redis.execute_command('JSON.SET', redis_key, '$', json_str)
                
            except Exception as e:
                print(f"[RedisSearch] Error writing log entry: {e}")
                if self.debug:
                    print(f"[RedisSearch] Failed entry: {entry}")

    supports_logs = True
    supports_metrics = False
    output_type = "logs"  # Explicitly mark as logs output