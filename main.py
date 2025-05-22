# rtcollector/main.py
import time
import yaml
import importlib
import argparse
import platform
from datetime import datetime
from core.collector import Collector
from core.config import load_config

def main():
    parser = argparse.ArgumentParser(description="Run rtcollector")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--once", action="store_true", help="Collect and push once")
    args = parser.parse_args()

    config = load_config(args.config)

    # Detect OS for plugin mapping
    system = platform.system().lower()  # 'linux', 'darwin', 'windows'

    # Load input plugins
    inputs = []
    seen_plugins = set()
    for name in config["inputs"]:
        if isinstance(name, dict):
            plugin_name = list(name.keys())[0]
            plugin_config = name[plugin_name]
        else:
            plugin_name = name
            plugin_config = {}

        # If on macOS, try to map linux_* to macos_* if available
        if system == "darwin" and plugin_name.startswith("linux_"):
            plugin_name = plugin_name.replace("linux_", "macos_")

        if plugin_name in seen_plugins:
            continue
        seen_plugins.add(plugin_name)

        try:
            mod = importlib.import_module(f"inputs.{plugin_name}")
            if plugin_config:
                def make_collector(mod, plugin_config):
                    def collect_with_config():
                        return mod.collect(plugin_config)
                    collect_with_config.__name__ = mod.__name__.split('.')[-1]
                    return collect_with_config
                inputs.append(make_collector(mod, plugin_config))
            else:
                inputs.append(mod.collect)
        except ModuleNotFoundError as e:
            print(f"[Collector] Skipping unavailable plugin '{plugin_name}': {e}")

    # Load output plugins
    outputs = []
    for item in config["outputs"]:
        for name, params in item.items():
            mod = importlib.import_module(f"outputs.{name}")
            output_class = getattr(mod, name.title().replace("_", ""))  # e.g., redistimeseries -> Redistimeseries
            outputs.append(output_class(**params))

    if args.once:
        all_metrics = []
        for collect_func in inputs:
            all_metrics.extend(collect_func())
        if args.debug:
            for m in all_metrics:
                print(m)
        for output in outputs:
            output.write(all_metrics)
    else:
        collector = Collector(
            interval=config["interval"],
            inputs=inputs,
            outputs=outputs
        )
        if args.debug:
            print(f"[{datetime.now().isoformat()}] [rtcollector] Starting in debug mode...")
        try:
            collector.run()
        except KeyboardInterrupt:
            print("\n[rtcollector] Stopped by user.")

if __name__ == "__main__":
    main()