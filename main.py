# rtcollector/main.py
import importlib
import argparse
import platform
from datetime import datetime
from core.collector import Collector
from core.config import load_config
from urllib.parse import urlparse

def apply_proxy_settings(config):
    try:
        import socks
        import socket
    except ImportError:
        print("[Proxy] PySocks not installed. Skipping proxy setup.")
        return

    outputs = config.get("outputs", [])
    for output in outputs:
        for name, params in output.items():
            proxy_url = params.get("socks5_proxy") or params.get("socks4_proxy")
            if proxy_url:
                parsed = urlparse(proxy_url)
                if parsed.scheme in ("socks5", "socks4"):
                    proxy_type = socks.SOCKS5 if parsed.scheme == "socks5" else socks.SOCKS4
                    proxy_host = parsed.hostname
                    proxy_port = parsed.port
                    proxy_username = parsed.username
                    proxy_password = parsed.password
                    print(f"[Proxy] Enabling {parsed.scheme.upper()} proxy to {proxy_host}:{proxy_port}")
                    socks.set_default_proxy(proxy_type, proxy_host, proxy_port, True, proxy_username, proxy_password)
                    socket.socket = socks.socksocket

def main():
    parser = argparse.ArgumentParser(description="Run rtcollector")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--once", action="store_true", help="Collect and push once")
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    # Override debug setting from command line
    if args.debug:
        config["debug"] = True

    apply_proxy_settings(config)

    # Detect OS for plugin mapping
    system = platform.system().lower()  # 'linux', 'darwin', 'windows'

    # Load input plugins
    inputs = []
    seen_plugins = set()
    for name in config["inputs"]:
        if isinstance(name, dict):
            plugin_name = list(name.keys())[0]
            plugin_config = config["inputs"][config["inputs"].index(name)][plugin_name]
        else:
            plugin_name = name
            plugin_config = {}

        if system == "darwin" and plugin_name.startswith("linux_"):
            plugin_name = plugin_name.replace("linux_", "macos_")

        if plugin_name in seen_plugins:
            continue
        seen_plugins.add(plugin_name)

        try:
            mod = importlib.import_module(f"inputs.{plugin_name}")
            # Add debug flag to plugin config
            if not plugin_config:
                plugin_config = {}
            plugin_config["debug"] = config.get("debug", False) or args.debug
            
            if plugin_config:
                if config.get("debug", False) or args.debug:
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
        collector_args = {
            "interval": config["interval"],
            "flush_interval": config.get("flush_interval"),
            "inputs": inputs,
            "outputs": outputs,
            "tags": config.get("tags")
        }

        if "warn_on_buffer" in config:
            collector_args["warn_on_buffer"] = config["warn_on_buffer"]
        if "buffer_limit" in config:
            collector_args["buffer_limit"] = config["buffer_limit"]

        collector = Collector(**collector_args)
        collector.output_types = output_types
        collector.debug = config.get("debug", False) or args.debug
        
        # Print startup information
        print(f"[{datetime.now().isoformat()}] [rtcollector] Starting rtcollector...")
        print(f"[{datetime.now().isoformat()}] [rtcollector] Collection interval: {config['interval']} seconds")
        print(f"[{datetime.now().isoformat()}] [rtcollector] Flush interval: {config.get('flush_interval', config['interval'])} seconds")
        print(f"[{datetime.now().isoformat()}] [rtcollector] Configured inputs: {', '.join([i.__name__ if callable(i) else str(i) for i in inputs])}")
        print(f"[{datetime.now().isoformat()}] [rtcollector] Configured outputs: {', '.join([o.__class__.__name__ for o in outputs])}")
        
        if collector.debug:
            print(f"[{datetime.now().isoformat()}] [rtcollector] Running in DEBUG mode")
        
        try:
            collector.run()
        except KeyboardInterrupt:
            print("\n[rtcollector] Stopped by user.")

if __name__ == "__main__":
    main()