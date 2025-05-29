import redis
import json
import time
import socket
from utils.debug import debug_log

class RedisSearch:
    def __init__(self, config=None, host="localhost", port=6379, db=0, index="logs_idx", key_prefix="log:", hostname=None, username=None, password=None, ssl=False, ssl_ca_certs=None, ssl_certfile=None, ssl_keyfile=None):
        # Accept both config dict or direct params for compatibility
        if config is not None:
            self.host = config.get("host", host)
            self.port = config.get("port", port)
            self.db = config.get("db", db)
            self.index_name = config.get("index", index)
            self.prefix = config.get("key_prefix", key_prefix)
            self.hostname = config.get("hostname", hostname) or socket.gethostname()
            self.debug = config.get("debug", False)
            self.username = config.get("username", username)
            self.password = config.get("password", password)
            self.ssl = config.get("ssl", ssl)
            self.ssl_ca_certs = config.get("ssl_ca_certs", ssl_ca_certs)
            self.ssl_certfile = config.get("ssl_certfile", ssl_certfile)
            self.ssl_keyfile = config.get("ssl_keyfile", ssl_keyfile)
        else:
            self.host = host
            self.port = port
            self.db = db
            self.index_name = index
            self.prefix = key_prefix
            self.hostname = hostname or socket.gethostname()
            self.debug = False
            self.username = username
            self.password = password
            self.ssl = ssl
            self.ssl_ca_certs = ssl_ca_certs
            self.ssl_certfile = ssl_certfile
            self.ssl_keyfile = ssl_keyfile
            
        # Connect to Redis
        try:
            # Configure SSL if enabled
            ssl_params = None
            if self.ssl:
                ssl_params = {
                    "ssl": True,
                    "ssl_ca_certs": self.ssl_ca_certs,
                    "ssl_certfile": self.ssl_certfile,
                    "ssl_keyfile": self.ssl_keyfile
                }
                # Remove None values
                ssl_params = {k: v for k, v in ssl_params.items() if v is not None}
            
            # Create Redis connection with auth and SSL if configured
            try:
                self.redis = redis.Redis(
                    host=self.host, 
                    port=self.port, 
                    db=self.db,
                    username=self.username,
                    password=self.password,
                    **ssl_params if ssl_params else {}
                )
                # Test connection
                self.redis.ping()
                debug_log("RedisSearch", f"Successfully connected to Redis at {self.host}:{self.port}", {"debug": self.debug})
            except redis.exceptions.AuthenticationError:
                print(f"\033[91m[RedisSearch] ERROR: Authentication failed for Redis at {self.host}:{self.port}. Please check username and password.\033[0m")
                print(f"\033[93m[RedisSearch] HINT: If Redis requires authentication, make sure to set username and/or password in config.yml\033[0m")
                self.redis = None
            except redis.exceptions.ConnectionError as e:
                print(f"\033[91m[RedisSearch] ERROR: Could not connect to Redis at {self.host}:{self.port}: {e}\033[0m")
                self.redis = None
            debug_log("RedisSearch", f"Successfully connected to Redis at {self.host}:{self.port}", {"debug": self.debug})
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
                debug_log("RedisSearch", f"Index {self.index_name} already exists", {"debug": self.debug})
            except redis.exceptions.ResponseError as e:
                if "unknown index" in str(e).lower():
                    # Index doesn't exist, create it
                    debug_log("RedisSearch", f"Creating index {self.index_name}", {"debug": self.debug})
                    
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
                        debug_log("RedisSearch", f"Successfully created index {self.index_name}", {"debug": self.debug})
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
                # Configure SSL if enabled
                ssl_params = None
                if self.ssl:
                    ssl_params = {
                        "ssl": True,
                        "ssl_ca_certs": self.ssl_ca_certs,
                        "ssl_certfile": self.ssl_certfile,
                        "ssl_keyfile": self.ssl_keyfile
                    }
                    # Remove None values
                    ssl_params = {k: v for k, v in ssl_params.items() if v is not None}
                
                self.redis = redis.Redis(
                    host=self.host, 
                    port=self.port, 
                    db=self.db,
                    username=self.username,
                    password=self.password,
                    **ssl_params if ssl_params else {}
                )
                self.redis.ping()
                # Ensure index exists
                self.ensure_index()
            except redis.exceptions.AuthenticationError:
                print(f"\033[91m[RedisSearch] ERROR: Authentication failed for Redis at {self.host}:{self.port}. Please check username and password.\033[0m")
                return
            except redis.exceptions.ConnectionError as e:
                print(f"\033[91m[RedisSearch] Failed to reconnect to Redis: {e}\033[0m")
                return
            except Exception as e:
                print(f"\033[91m[RedisSearch] Failed to reconnect to Redis: {e}\033[0m")
                return
                
        logs_to_write = []
        
        # Process and filter log entries
        for e in log_entries:
            if isinstance(e, dict):
                # Handle syslog-style entries
                if "name" in e and isinstance(e.get("name"), str) and e.get("name", "").startswith("syslog_"):
                    debug_log("RedisSearch", f"Processing syslog entry: {e}", {"debug": self.debug})
                    logs_to_write.append(e)
                # Handle message-style entries
                elif "message" in e:
                    debug_log("RedisSearch", f"Processing message entry: {e}", {"debug": self.debug})
                    logs_to_write.append(e)
        
        if not logs_to_write:
            debug_log("RedisSearch", "No valid log entries to write", {"debug": self.debug})
            return
            
        debug_log("RedisSearch", f"Writing {len(logs_to_write)} log entries", {"debug": self.debug})
        
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
                    debug_log("RedisSearch", f"Skipping invalid entry type: {type(entry)}", {"debug": self.debug})
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
                debug_log("RedisSearch", f"Writing to {redis_key}: {json_str[:100]}...", {"debug": self.debug})
                    
                self.redis.execute_command('JSON.SET', redis_key, '$', json_str)
                
            except Exception as e:
                print(f"[RedisSearch] Error writing log entry: {e}")
                debug_log("RedisSearch", f"Failed entry: {entry}", {"debug": self.debug})

    supports_logs = True
    supports_metrics = False
    output_type = "logs"  # Explicitly mark as logs output