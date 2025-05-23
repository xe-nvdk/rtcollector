# rtcollector/main.py
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
                print(f"[DEBUG] Loading plugin: {plugin_name} with config: {plugin_config}")
                def make_collector(mod, plugin_config):
                    def collect_with_config():
                        result = mod.collect(plugin_config)
                        if callable(result):
                            return result()
                        return result
                    collect_with_config.__name__ = plugin_name
                    return collect_with_config
                inputs.append(make_collector(mod, plugin_config))
            else:
                print(f"[WARNING] No configuration found for plugin: {plugin_name}, using defaults if available.")
                inputs.append(mod.collect)
        except ModuleNotFoundError as e:
            print(f"[Collector] Skipping unavailable plugin '{plugin_name}': {e}")

    # Load output plugins
    outputs = []
    output_types = {}  # Track output types (e.g., metrics, logs)
    for item in config["outputs"]:
        for name, params in item.items():
            mod = importlib.import_module(f"outputs.{name}")
            # Robust class name resolution: e.g., 'redis_search' -> 'RedisSearch'
            class_name = "".join(part.capitalize() for part in name.split("_"))
            try:
                output_class = getattr(mod, class_name)
            except AttributeError:
                # Try case-insensitive match (e.g., RedisSearch)
                output_class = next((cls for cls_name, cls in vars(mod).items()
                                     if cls_name.lower() == class_name.lower()), None)
                if output_class is None:
                    raise
            # Instantiate output plugin passing only **params, not config=params
            instance = output_class(**params)
            output_type = getattr(instance, "output_type", "metrics")
            output_types[instance] = output_type
            outputs.append(instance)

    if args.once:
        all_metrics = []
        for collect_func in inputs:
            raw_results = collect_func()
            if isinstance(raw_results, list):
                all_metrics.extend(raw_results)
            elif callable(raw_results):
                result = raw_results()
                if isinstance(result, list):
                    all_metrics.extend(result)
        if args.debug:
            for m in all_metrics:
                print(m)
        logs = [m for m in all_metrics if isinstance(m, dict)]
        metrics = [m for m in all_metrics if not isinstance(m, dict)]
        for output in outputs:
            if output_types.get(output) == "logs":
                output.write(logs)
            else:
                output.write(metrics)
    else:
        collector = Collector(
            interval=config["interval"],
            inputs=inputs,
            outputs=outputs,
            tags=config.get("tags", {})
        )
        collector.output_types = output_types
        if args.debug:
            print(f"[{datetime.now().isoformat()}] [rtcollector] Starting in debug mode...")
        try:
            collector.run()
        except KeyboardInterrupt:
            print("\n[rtcollector] Stopped by user.")

if __name__ == "__main__":
    main()