# core/collector.py
import time
from datetime import datetime

class Collector:
    def __init__(self, interval, inputs, outputs):
        self.interval = interval
        self.inputs = inputs
        self.outputs = outputs

    def run(self):
        while True:
            print(f"[{datetime.now().isoformat()}] [Collector] Collecting metrics...")
            all_metrics = []
            for input_func in self.inputs:
                plugin_module = getattr(input_func, "__module__", "unknown")
                plugin_name = plugin_module.split('.')[-1]

                if plugin_name == "__main__" or plugin_name.startswith("<"):
                    plugin_name = getattr(input_func, "__name__", "anonymous")
                start = time.time()
                try:
                    metrics = input_func()
                    duration = time.time() - start
                    all_metrics.extend(metrics)
                    slow_flag = " ⚠️" if duration > 1.0 else ""
                    print(f"[{datetime.now().isoformat()}] [{plugin_name}] Collected {len(metrics)} metrics in {duration:.2f}s{slow_flag}")
                except Exception as e:
                    print(f"[{datetime.now().isoformat()}] [Collector] Error in input plugin '{plugin_name}': {e}")
            for output in self.outputs:
                try:
                    output.write(all_metrics)
                    print(f"[{datetime.now().isoformat()}] [Collector] Wrote {len(all_metrics)} metrics to {output.__class__.__name__}")
                except Exception as e:
                    print(f"[{datetime.now().isoformat()}] [Collector] Error in output plugin: {e}")
            print(f"[{datetime.now().isoformat()}] [Collector] Sleeping for {self.interval} seconds...\n")
            time.sleep(self.interval)