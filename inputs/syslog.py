import socketserver
import threading
import ssl
import re
from datetime import datetime

from utils.system import get_hostname

syslog_collector_instance = None

# Regex for standard syslog format
SYSLOG_REGEX = re.compile(
    r"<(?P<pri>\d+)>(?P<timestamp>[^\s]+) (?P<hostname>[^\s]+) (?P<appname>[^\s]+)(?:\[(?P<procid>\d+)\])?: (?P<message>.*)"
)

# Regex to split multiple syslog messages
SYSLOG_SPLIT_REGEX = re.compile(r"<\d+>")

def parse_syslog(message):
    match = SYSLOG_REGEX.match(message)
    if not match:
        return {}
    data = match.groupdict()
    pri = int(data["pri"])
    facility = pri // 8
    severity = pri % 8
    return {
        "facility": facility,
        "severity": severity,
        "hostname": data["hostname"],
        "appname": data["appname"],
        "procid": data.get("procid", ""),
        "message": data["message"]
    }

def split_syslog_messages(data):
    """Split a buffer that may contain multiple syslog messages"""
    # Convert bytes to string if needed
    if isinstance(data, bytes):
        data = data.decode('utf-8', errors='ignore')
    
    # Find all positions where a new syslog message starts
    positions = [0] + [m.start() for m in SYSLOG_SPLIT_REGEX.finditer(data) if m.start() > 0]
    
    # Extract individual messages
    messages = []
    for i in range(len(positions)):
        start = positions[i]
        end = positions[i+1] if i+1 < len(positions) else len(data)
        message = data[start:end].strip()
        if message:
            messages.append(message)
    
    # If no messages were found or split failed, return the original as a single message
    if not messages:
        messages = [data]
    
    return messages

class SyslogTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            buffer = ""
            while True:
                data = self.request.recv(1024)
                if not data:
                    break
                
                # Add new data to buffer
                buffer += data.decode('utf-8', errors='ignore')
                
                # Process complete messages
                messages = split_syslog_messages(buffer)
                if messages:
                    # Keep the last partial message in buffer if it doesn't end with newline
                    if not buffer.endswith('\n') and len(messages) > 1:
                        buffer = messages[-1]
                        messages = messages[:-1]
                    else:
                        buffer = ""
                    
                    # Process each complete message
                    for message in messages:
                        if message:
                            self.process_message(message)
        except Exception as e:
            print(f"[syslog] TCP handler error: {e}")

    def process_message(self, message):
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        labels = {
            "host": self.server.hostname,
            "remote_ip": self.client_address[0],
        }
        
        # Try to parse the message
        parsed = parse_syslog(message)
        if parsed:
            labels.update(parsed)
        else:
            labels["message"] = message
        
        # Use appname in the log entry name if available
        log_name = f"syslog_{labels.get('appname', 'message')}" if 'appname' in labels else "syslog_message"
        
        log_entry = {
            "name": log_name,
            "timestamp": timestamp,
            **labels
        }
        self.server.metrics.append(log_entry)

class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        client_address = self.client_address
        
        # Process each message in the UDP packet
        messages = split_syslog_messages(data)
        for message in messages:
            if message:
                self.process_message(message, client_address)

    def process_message(self, message, client_address):
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        labels = {
            "host": self.server.hostname,
            "remote_ip": client_address[0],
        }
        
        # Try to parse the message
        if isinstance(message, bytes):
            message = message.decode('utf-8', errors='ignore')
            
        parsed = parse_syslog(message)
        if parsed:
            labels.update(parsed)
        else:
            labels["message"] = message
        
        # Use appname in the log entry name if available
        log_name = f"syslog_{labels.get('appname', 'message')}" if 'appname' in labels else "syslog_message"
        
        log_entry = {
            "name": log_name,
            "timestamp": timestamp,
            **labels
        }
        self.server.metrics.append(log_entry)

class SyslogServer(socketserver.ThreadingTCPServer):
    def __init__(self, server_address, RequestHandlerClass, hostname, ssl_context=None):
        super().__init__(server_address, RequestHandlerClass)
        self.daemon_threads = True
        self.allow_reuse_address = True
        self.metrics = []
        self.hostname = hostname
        self.ssl_context = ssl_context

    def get_request(self):
        socket_conn, addr = self.socket.accept()
        if self.ssl_context:
            socket_conn = self.ssl_context.wrap_socket(socket_conn, server_side=True)
        return socket_conn, addr

class SyslogUDPServer(socketserver.UDPServer):
    def __init__(self, server_address, RequestHandlerClass, hostname):
        super().__init__(server_address, RequestHandlerClass)
        self.daemon_threads = True
        self.allow_reuse_address = True
        self.metrics = []
        self.hostname = hostname

def collect(config):
    global syslog_collector_instance
    if syslog_collector_instance is not None:
        print("[syslog] Warning: syslog collector already initialized. Returning existing instance.")
        return syslog_collector_instance

    server_config = config
    server_url = server_config.get("server", "").strip()
    print(f"[syslog] Debug: server_url from config is '{server_url}'")
    if not server_url:
        print("[syslog] Error: 'server' must be specified in config under inputs.syslog.")
        return lambda: []
    hostname = config.get("hostname", get_hostname())
    tls_cert = server_config.get("tls_cert")
    tls_key = server_config.get("tls_key")

    protocol, address = server_url.split("://")
    if ":" in address:
        host, port = address.split(":")
    else:
        host, port = address, "6514"
    host = host if host else "0.0.0.0"
    port = int(port)

    ssl_context = None
    if tls_cert and tls_key:
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(certfile=tls_cert, keyfile=tls_key)

    if protocol == "tcp":
        server = SyslogServer((host, port), SyslogTCPHandler, hostname, ssl_context)
    elif protocol == "udp":
        server = SyslogUDPServer((host, port), SyslogUDPHandler, hostname)
    else:
        print("[syslog] Only tcp:// and udp:// are supported in this version.")
        return lambda: []

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"[syslog] Listening for syslog messages on {protocol}://{host}:{port}")

    class SyslogCollector:
        def __init__(self, server, server_thread):
            self.server = server
            self.thread = server_thread

        def __call__(self):
            collected = self.server.metrics[:]
            self.server.metrics.clear()
            return collected

        def stop(self):
            if hasattr(self.server, "shutdown"):
                self.server.shutdown()
            if hasattr(self.server, "server_close"):
                self.server.server_close()
            if self.thread.is_alive():
                self.thread.join(timeout=1)

    syslog_collector_instance = SyslogCollector(server, server_thread)
    return syslog_collector_instance