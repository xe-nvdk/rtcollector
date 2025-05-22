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
                try:
                    metrics = input_func()
                    all_metrics.extend(metrics)
                    print(f"[{datetime.now().isoformat()}] [Collector] Collected {len(metrics)} metrics from {input_func.__module__}")
                except Exception as e:
                    print(f"[{datetime.now().isoformat()}] [Collector] Error in input plugin: {e}")
            for output in self.outputs:
                try:
                    output.write(all_metrics)
                    print(f"[{datetime.now().isoformat()}] [Collector] Wrote {len(all_metrics)} metrics to {output.__class__.__name__}")
                except Exception as e:
                    print(f"[{datetime.now().isoformat()}] [Collector] Error in output plugin: {e}")
            print(f"[{datetime.now().isoformat()}] [Collector] Sleeping for {self.interval} seconds...\n")
            time.sleep(self.interval)