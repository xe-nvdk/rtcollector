# core/collector.py
import time
from datetime import datetime
from core.metric import Metric

class Collector:
    def __init__(self, interval, inputs, outputs, tags=None, logs_only_outputs=None, metrics_only_outputs=None):
        self.interval = interval
        self.inputs = inputs
        self.outputs = outputs
        self.logs_only_outputs = logs_only_outputs or []
        self.metrics_only_outputs = metrics_only_outputs or []
        self.tags = tags or {}
        self._input_states = {}

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
                    if isinstance(data, dict) and plugin_logs_key in data and plugin_metrics_key in data:
                        for item in data[plugin_metrics_key]:
                            if isinstance(item, Metric):
                                item.labels.update(self.tags)
                                metrics_to_send.append(item)
                                count += 1
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

            for output in self.outputs:
                try:
                    if hasattr(output, "supports_logs") and output.supports_logs:
                        if logs_to_send:
                            output.write(logs_to_send)
                            print(f"[{datetime.now().isoformat()}] [Collector] Wrote {len(logs_to_send)} logs to {output.__class__.__name__}")
                    elif hasattr(output, "supports_metrics") and output.supports_metrics:
                        if metrics_to_send:
                            output.write(metrics_to_send)
                            print(f"[{datetime.now().isoformat()}] [Collector] Wrote {len(metrics_to_send)} metrics to {output.__class__.__name__}")
                    else:
                        if metrics_to_send:
                            output.write(metrics_to_send)
                        if logs_to_send:
                            output.write(logs_to_send)
                        print(f"[{datetime.now().isoformat()}] [Collector] Wrote {len(metrics_to_send) + len(logs_to_send)} metrics to {output.__class__.__name__}")
                except Exception as e:
                    print(f"[{datetime.now().isoformat()}] [Collector] Error in output plugin: {e}")

            for output in self.metrics_only_outputs:
                try:
                    if metrics_to_send:
                        output.write(metrics_to_send)
                        print(f"[{datetime.now().isoformat()}] [Collector] Wrote {len(metrics_to_send)} metrics to {output.__class__.__name__}")
                except Exception as e:
                    print(f"[{datetime.now().isoformat()}] [Collector] Error in metrics-only output plugin: {e}")

            for output in self.logs_only_outputs:
                try:
                    if logs_to_send:
                        output.write(logs_to_send)
                        print(f"[{datetime.now().isoformat()}] [Collector] Wrote {len(logs_to_send)} logs to {output.__class__.__name__}")
                except Exception as e:
                    print(f"[{datetime.now().isoformat()}] [Collector] Error in logs-only output plugin: {e}")

            print(f"[{datetime.now().isoformat()}] [Collector] Sleeping for {self.interval} seconds...\n")
            time.sleep(self.interval)