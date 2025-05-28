"""
Utility functions for metric processing.
"""

# Store previous values for rate calculations
_last_values = {}
_last_timestamps = {}

def calculate_rate(name, value, timestamp, reset_value=None):
    """
    Calculate rate of change for counter metrics.
    
    Args:
        name: Unique identifier for the counter (should include metric name and labels)
        value: Current counter value
        timestamp: Current timestamp in milliseconds
        reset_value: Maximum value before counter reset (optional)
        
    Returns:
        Rate per second or None if this is the first measurement or invalid
    """
    global _last_values, _last_timestamps
    
    # If this is the first measurement, store and return None
    if name not in _last_values or name not in _last_timestamps:
        _last_values[name] = value
        _last_timestamps[name] = timestamp
        return None
    
    # Calculate time difference in seconds
    time_diff = (timestamp - _last_timestamps[name]) / 1000.0
    if time_diff <= 0:
        return None
    
    # Calculate value difference
    value_diff = value - _last_values[name]
    
    # Handle counter reset
    if value_diff < 0:
        if reset_value is not None:
            # Counter wrapped around
            value_diff = (reset_value - _last_values[name]) + value
        else:
            # Counter reset (e.g., system reboot)
            _last_values[name] = value
            _last_timestamps[name] = timestamp
            return None
    
    # Store current values for next calculation
    _last_values[name] = value
    _last_timestamps[name] = timestamp
    
    # Calculate and return rate
    return value_diff / time_diff

def create_key(metric_name, labels):
    """
    Create a unique key for a metric based on its name and labels.
    
    Args:
        metric_name: Name of the metric
        labels: Dictionary of labels
        
    Returns:
        String key that uniquely identifies this metric
    """
    if not labels:
        return metric_name
        
    # Sort labels for consistent key generation
    sorted_labels = sorted(labels.items())
    labels_str = ",".join(f"{k}={v}" for k, v in sorted_labels)
    return f"{metric_name}:{labels_str}"