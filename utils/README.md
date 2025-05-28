# Utility Functions

This directory contains utility functions used across the rtcollector project.

## Metrics Utilities

### Rate Calculation

The `metrics.py` module provides functions for calculating rates from counter metrics:

```python
from utils.metrics import calculate_rate, create_key

# Calculate rate for a counter metric
metric_key = create_key("metric_name", {"label1": "value1"})
rate = calculate_rate(metric_key, current_value, timestamp)
```

#### Why Rate Calculation?

Many system metrics are cumulative counters that increase over time (e.g., context switches, network bytes). While these raw counters are useful for some purposes, it's often more valuable to know the rate of change (e.g., context switches per second).

**Redis TimeSeries Limitation**: Unlike other time-series databases (such as InfluxDB with its `non_negative_derivative()` function), Redis TimeSeries doesn't provide built-in functions to calculate rates from counter metrics. This means:

1. Without pre-calculation, users would see raw counters that continuously increase
2. To get meaningful rates, users would need to apply complex transformations in Grafana
3. These transformations would need to be repeated for every dashboard and panel

By implementing rate calculation directly in the collector:
1. We provide ready-to-use rate metrics (with `_rate` suffix)
2. Users get meaningful per-second values without additional processing
3. Dashboards are simpler and more consistent
4. Edge cases like counter resets are handled properly

The `calculate_rate()` function:
- Tracks previous values and timestamps
- Calculates the difference between consecutive measurements
- Divides by the time difference to get a per-second rate
- Handles counter resets and other edge cases
- Mimics the behavior of InfluxDB's `non_negative_derivative()` function

#### Benefits

1. **Consistency**: All plugins calculate rates the same way
2. **Simplicity**: Plugins don't need to manage their own state
3. **Robustness**: Edge cases like counter resets are handled properly
4. **Reusability**: Easy to add rate calculations to any plugin

#### Usage in Plugins

For counter metrics, plugins should:
1. Emit the raw counter value with its original name
2. Calculate and emit a rate with a `_rate` suffix

Example:
```python
# Raw counter
metrics.append(Metric("cpu_context_switches", counter_value, timestamp, labels))

# Rate (per second)
metric_key = create_key("cpu_context_switches", labels)
rate = calculate_rate(metric_key, counter_value, timestamp)
if rate is not None:
    metrics.append(Metric("cpu_context_switches_rate", rate, timestamp, labels))
```

## System Utilities

The `system.py` module provides functions for getting system information:

- `get_hostname()`: Returns the system hostname
- Other system-related utilities

## Other Utilities

Additional utility modules may be added as needed to support common functionality across the project.