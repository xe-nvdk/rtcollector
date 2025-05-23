import socket

def get_hostname():
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"
