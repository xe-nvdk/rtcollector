# core/collector.py
import time
from datetime import datetime
from core.metric import Metric

class Collector:
    def __init__(self, interval, inputs, outputs, tags=None, logs_only_outputs=None, metrics_only_outputs=None, flush_interval=None, max_buffer_size=5000, warn_on_buffer=True):
        self.interval = interval
        self.flush_interval = flush_interval or interval
        self.max_buffer_size = max_buffer_size
        self.warn_on_buffer = warn_on_buffer
        if self.flush_interval < self.interval:
            print(f"[WARNING] Flush interval ({self.flush_interval}) is shorter than collection interval ({self.interval}) — this may lead to unintended behavior.")
        self.inputs = inputs
        self.outputs = outputs
        self.logs_only_outputs = logs_only_outputs or []
        self.metrics_only_outputs = metrics_only_outputs or []
        self.tags = tags or {}
        self._input_states = {}
        self._last_flush_time = time.time()
        self.buffered_metrics = []
        self.buffered_logs = []

    def run(self):
        while True:
            print(f"[{datetime.now().isoformat()}] [Collector] Collecting metrics...")
            metrics_to_send = []
            logs_to_send = []

            for input_entry in self.inputs:
                if isinstance(input_entry, dict):
                    plugin_name, input_func = list(input_entry.items())[0]
                else:
                    input_func = input_entry
                    plugin_module = getattr(input_func, "__module__", "unknown")
                    plugin_name = plugin_module.split('.')[-1]
                    if plugin_name == "__main__" or plugin_name.startswith("<"):
                        plugin_name = getattr(input_func, "__name__", "anonymous")
                        if hasattr(input_func, "_is_persistent") and input_func._is_persistent:
                            input_handler = input_func
                            self._input_states[plugin_name] = input_handler

                # Cache input state or handler if needed
                if plugin_name not in self._input_states and not (hasattr(input_func, "_is_persistent") and input_func._is_persistent):
                    # If the input_func has a collect method, call it once to initialize and cache result
                    if hasattr(input_func, "collect") and callable(input_func.collect):
                        self._input_states[plugin_name] = input_func.collect()
                    else:
                        self._input_states[plugin_name] = input_func

                input_handler = self._input_states[plugin_name]

                start = time.time()
                try:
                    # If input_handler is callable, call it to get data, else assume it's already data
                    if callable(input_handler):
                        data = input_handler()
                    else:
                        data = input_handler
                    duration = time.time() - start
                    # Determine plugin keys for logs and metrics
                    plugin_logs_key = f"{plugin_name}_logs"
                    plugin_metrics_key = f"{plugin_name}_metrics"
                    count = 0
                    if isinstance(data, dict):
                        if plugin_metrics_key in data:
                            for item in data[plugin_metrics_key]:
                                if isinstance(item, Metric):
                                    item.labels.update(self.tags)
                                    print(f"[DEBUG] Accepted metric: {item.name}={item.value} tags={item.labels}")
                                    metrics_to_send.append(item)
                                    count += 1
                        if plugin_logs_key in data:
                            for log in data[plugin_logs_key]:
                                if isinstance(log, dict):
                                    logs_to_send.append(log)
                                    count += 1
                    elif isinstance(data, tuple) and len(data) == 2:
                        metrics_part, logs_part = data
                        for item in metrics_part:
                            if isinstance(item, Metric):
                                item.labels.update(self.tags)
                                metrics_to_send.append(item)
                                count += 1
                        for log in logs_part:
                            if isinstance(log, dict):
                                logs_to_send.append(log)
                                count += 1
                    else:
                        for item in data:
                            if isinstance(item, Metric):
                                item.labels.update(self.tags)
                                metrics_to_send.append(item)
                            elif isinstance(item, dict):
                                logs_to_send.append(item)
                            count += 1
                    slow_flag = " ⚠️" if duration > 1.0 else ""
                    print(f"[{datetime.now().isoformat()}] [{plugin_name}] Collected {count} metrics in {duration:.2f}s{slow_flag}")
                except Exception as e:
                    print(f"[{datetime.now().isoformat()}] [Collector] Error in input plugin '{plugin_name}': {e}")

            self.buffered_metrics.extend(metrics_to_send)
            print(f"[{datetime.now().isoformat()}] [Collector] Buffered {len(self.buffered_metrics)} metrics.")
            self.buffered_logs.extend(logs_to_send)
            print(f"[{datetime.now().isoformat()}] [Collector] Buffered {len(self.buffered_logs)} logs.")
            metric_progress = int((len(self.buffered_metrics) / self.max_buffer_size) * 20)
            log_progress = int((len(self.buffered_logs) / self.max_buffer_size) * 20)
            metric_bar = f"\033[92m{'#' * metric_progress}\033[90m{'.' * (20 - metric_progress)}\033[0m"
            log_bar = f"\033[94m{'#' * log_progress}\033[90m{'.' * (20 - log_progress)}\033[0m"
            print(f"[{datetime.now().isoformat()}] [Collector] Metric buffer: [{metric_bar}] {len(self.buffered_metrics)}/{self.max_buffer_size}")
            print(f"[{datetime.now().isoformat()}] [Collector] Log buffer:    [{log_bar}] {len(self.buffered_logs)}/{self.max_buffer_size}")

            now = time.time()
            if now - self._last_flush_time >= self.flush_interval:
                if len(self.buffered_metrics) > self.max_buffer_size:
                    if self.warn_on_buffer:
                        print(f"[WARNING] Buffered metrics exceeded max buffer size ({self.max_buffer_size}). Dropping oldest entries.")
                    self.buffered_metrics = self.buffered_metrics[-self.max_buffer_size:]

                if len(self.buffered_logs) > self.max_buffer_size:
                    if self.warn_on_buffer:
                        print(f"[WARNING] Buffered logs exceeded max buffer size ({self.max_buffer_size}). Dropping oldest entries.")
                    self.buffered_logs = self.buffered_logs[-self.max_buffer_size:]

                all_successful = True
                try:
                    for output in self.outputs:
                        try:
                            if hasattr(output, "supports_logs") and output.supports_logs:
                                if self.buffered_logs:
                                    try:
                                        output.write(self.buffered_logs)
                                        print(f"[{datetime.now().isoformat()}] [Collector] Wrote {len(self.buffered_logs)} logs to {output.__class__.__name__}")
                                    except Exception as e:
                                        all_successful = False
                                        print(f"[{datetime.now().isoformat()}] [Collector] Failed to write logs to {output.__class__.__name__}: {e}")
                            elif hasattr(output, "supports_metrics") and output.supports_metrics:
                                if self.buffered_metrics:
                                    output.write(self.buffered_metrics)
                                    print(f"[{datetime.now().isoformat()}] [Collector] Wrote {len(self.buffered_metrics)} metrics to {output.__class__.__name__}")
                            else:
                                if self.buffered_metrics:
                                    output.write(self.buffered_metrics)
                                if self.buffered_logs:
                                    output.write(self.buffered_logs)
                                print(f"[{datetime.now().isoformat()}] [Collector] Wrote {len(self.buffered_metrics) + len(self.buffered_logs)} metrics to {output.__class__.__name__}")
                        except Exception as e:
                            all_successful = False
                            print(f"[{datetime.now().isoformat()}] [Collector] Error in output plugin: {e}")

                    for output in self.metrics_only_outputs:
                        try:
                            if self.buffered_metrics:
                                output.write(self.buffered_metrics)
                                print(f"[{datetime.now().isoformat()}] [Collector] Wrote {len(self.buffered_metrics)} metrics to {output.__class__.__name__}")
                        except Exception as e:
                            all_successful = False
                            print(f"[{datetime.now().isoformat()}] [Collector] Error in metrics-only output plugin: {e}")

                    for output in self.logs_only_outputs:
                        try:
                            if self.buffered_logs:
                                output.write(self.buffered_logs)
                                print(f"[{datetime.now().isoformat()}] [Collector] Wrote {len(self.buffered_logs)} logs to {output.__class__.__name__}")
                        except Exception as e:
                            all_successful = False
                            print(f"[{datetime.now().isoformat()}] [Collector] Error in logs-only output plugin: {e}")
                except Exception:
                    all_successful = False

                if all_successful:
                    self.buffered_metrics.clear()
                    self.buffered_logs.clear()
                    self._last_flush_time = now

            print(f"[{datetime.now().isoformat()}] [Collector] Sleeping for {self.interval} seconds...\n")
            time.sleep(self.interval)