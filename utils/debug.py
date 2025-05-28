"""
Debug utility functions for rtcollector plugins.
"""
from datetime import datetime

def debug_log(plugin_name, message, config=None):
    """
    Log a debug message if debug mode is enabled.
    
    Args:
        plugin_name (str): Name of the plugin
        message (str): Message to log
        config (dict, optional): Plugin configuration. If None, message is not logged.
    """
    if config and config.get('debug', False):
        # Use the same timestamp format as the collector for consistency
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [{plugin_name}] {message}")