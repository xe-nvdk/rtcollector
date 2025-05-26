import requests_unixsocket
import time
import socket
import platform
from core.metric import Metric
import concurrent.futures

class DockerStatsCollector:
    def __init__(self, config):
        self.config = config if isinstance(config, dict) else {}
        self.endpoint = self.config.get('endpoint', 'unix:///var/run/docker.sock')
        self.session = requests_unixsocket.Session()
        self.hostname = socket.gethostname()
        self.container_include = self.config.get('container_name_include', [])
        self.container_exclude = self.config.get('container_name_exclude', [])
        self.max_workers = self.config.get('max_workers', 10)  # Limit concurrent requests
        
        # Convert Unix socket path to URL format
        if self.endpoint.startswith('unix://'):
            path = self.endpoint[7:]
            self.base_url = f'http+unix://{path.replace("/", "%2F")}'
        else:
            self.base_url = self.endpoint

    def collect(self):
        if platform.system() not in ["Linux", "Darwin"]:
            return {
                "docker_logs": [{
                    "message": "Docker plugin is only supported on Linux and macOS",
                    "level": "error",
                    "tags": {"source": "docker"}
                }]
            }
        
        metrics = []
        logs = []
        timestamp = int(time.time() * 1000)
        start_time = time.time()
        
        try:
            # Get server version once for all metrics
            try:
                resp = self.session.get(f'{self.base_url}/version', timeout=5)
                version_info = resp.json() if resp.ok else {}
                server_version = version_info.get("Version", "unknown")
            except Exception as e:
                logs.append({
                    "message": f"Failed to get Docker version: {e}",
                    "level": "error",
                    "tags": {"source": "docker"}
                })
                server_version = "unknown"
            
            # Get container list
            try:
                containers_resp = self.session.get(f'{self.base_url}/containers/json', timeout=5)
                containers = containers_resp.json() if containers_resp.ok else []
                
                # Filter containers based on include/exclude lists
                filtered_containers = []
                for container in containers:
                    container_name = container.get("Names", [""])[0].lstrip('/')
                    
                    # Apply include/exclude filters
                    if self.container_include and not any(pattern in container_name for pattern in self.container_include):
                        continue
                    if self.container_exclude and any(pattern in container_name for pattern in self.container_exclude):
                        continue
                    
                    filtered_containers.append(container)
                
                # Collect container metrics in parallel with limited concurrency
                container_metrics = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = [executor.submit(self._collect_container_metrics, container, timestamp, server_version) 
                              for container in filtered_containers]
                    
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            result = future.result()
                            container_metrics.extend(result.get("metrics", []))
                            logs.extend(result.get("logs", []))
                        except Exception as e:
                            logs.append({
                                "message": f"Error processing container metrics: {e}",
                                "level": "error",
                                "tags": {"source": "docker"}
                            })
                
                metrics.extend(container_metrics)
            except Exception as e:
                logs.append({
                    "message": f"Failed to list containers: {e}",
                    "level": "error",
                    "tags": {"source": "docker"}
                })
            
            # Collect engine metrics
            if self.config.get("collect_engine_metrics", True):
                engine_result = self._collect_engine_metrics(timestamp, server_version)
                metrics.extend(engine_result.get("metrics", []))
                logs.extend(engine_result.get("logs", []))
            
            # Collect disk usage metrics
            if self.config.get("collect_disk_usage", True):
                disk_result = self._collect_disk_usage_metrics(timestamp, server_version)
                metrics.extend(disk_result.get("metrics", []))
                logs.extend(disk_result.get("logs", []))
            
            # Collect swarm metrics if enabled
            if self.config.get("swarm_enabled", False):
                swarm_result = self._collect_swarm_metrics(timestamp, server_version)
                metrics.extend(swarm_result.get("metrics", []))
                logs.extend(swarm_result.get("logs", []))
            
            # Log collection time if debug is enabled
            collection_time = time.time() - start_time
            if self.config.get("debug", False):
                logs.append({
                    "message": f"Docker metrics collection completed in {collection_time:.2f}s, collected {len(metrics)} metrics",
                    "level": "debug",
                    "tags": {"source": "docker"}
                })
            
        except Exception as e:
            logs.append({
                "message": f"Error in Docker metrics collection: {e}",
                "level": "error",
                "tags": {"source": "docker"}
            })
        
        return {
            "docker_metrics": metrics,
            "docker_logs": logs
        }

    def _collect_container_metrics(self, container, timestamp, server_version):
        metrics = []
        logs = []
        
        try:
            container_id = container.get("Id", "")
            container_name = container.get("Names", ["unknown"])[0].lstrip('/')
            container_image = container.get("Image", "unknown")
            container_status = container.get("State", "unknown")
            short_id = container_id[:12] if container_id else "unknown"
            
            # Common tags for all metrics from this container
            tags = {
                "source": "docker",
                "engine_host": self.hostname,
                "server_version": server_version,
                "container_image": container_image,
                "container_name": container_name,
                "container_status": container_status,
                "container_id": short_id,
            }
            
            # Get container stats (non-streaming)
            stats_resp = self.session.get(f'{self.base_url}/containers/{container_id}/stats?stream=false', timeout=5)
            if not stats_resp.ok:
                logs.append({
                    "message": f"Failed to get stats for container {container_name}: HTTP {stats_resp.status_code}",
                    "level": "error",
                    "tags": {"source": "docker", "container": container_name}
                })
                return {"metrics": [], "logs": logs}
            
            stats = stats_resp.json()
            
            # CPU metrics
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})
            cpu_usage = cpu_stats.get("cpu_usage", {})
            pre_cpu_usage = precpu_stats.get("cpu_usage", {})
            
            # Calculate CPU percentage
            system_cpu_usage = cpu_stats.get("system_cpu_usage", 0)
            pre_system_cpu_usage = precpu_stats.get("system_cpu_usage", 0)
            usage_total = cpu_usage.get("total_usage", 0)
            pre_usage_total = pre_cpu_usage.get("total_usage", 0)
            
            # Get number of CPUs
            percpu_usage = cpu_usage.get("percpu_usage", [])
            online_cpus = cpu_stats.get("online_cpus") or len(percpu_usage) or 1
            
            # Calculate CPU percentage
            cpu_delta = usage_total - pre_usage_total
            system_delta = system_cpu_usage - pre_system_cpu_usage
            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
            
            # Add CPU metrics
            metrics.append(Metric(
                name="docker_cpu_percent",
                value=cpu_percent,
                labels=tags.copy(),
                timestamp=timestamp
            ))
            
            # Memory metrics
            mem_stats = stats.get("memory_stats", {})
            mem_usage = mem_stats.get("usage", 0)
            mem_limit = mem_stats.get("limit", 1)
            mem_percent = (mem_usage / mem_limit) * 100.0 if mem_limit > 0 else 0.0
            
            # Add memory metrics
            metrics.append(Metric(
                name="docker_mem_usage",
                value=mem_usage,
                labels=tags.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="docker_mem_limit",
                value=mem_limit,
                labels=tags.copy(),
                timestamp=timestamp
            ))
            
            metrics.append(Metric(
                name="docker_mem_percent",
                value=mem_percent,
                labels=tags.copy(),
                timestamp=timestamp
            ))
            
            # Network metrics
            networks = stats.get("networks", {})
            for iface, net in networks.items():
                net_tags = tags.copy()
                net_tags["interface"] = iface
                
                # Add network metrics
                if isinstance(net, dict):
                    for key, metric_name in [
                        ("rx_bytes", "docker_net_rx_bytes"),
                        ("tx_bytes", "docker_net_tx_bytes"),
                    ]:
                        if key in net:
                            metrics.append(Metric(
                                name=metric_name,
                                value=net[key],
                                labels=net_tags,
                                timestamp=timestamp
                            ))
            
        except Exception as e:
            logs.append({
                "message": f"Error collecting stats for container {container.get('Names', ['unknown'])[0]}: {e}",
                "level": "error",
                "tags": {"source": "docker", "container": container.get('Names', ['unknown'])[0]}
            })
        
        return {"metrics": metrics, "logs": logs}

    def _collect_engine_metrics(self, timestamp, server_version):
        metrics = []
        logs = []
        
        try:
            # Get Docker engine info
            resp = self.session.get(f'{self.base_url}/info', timeout=5)
            if not resp.ok:
                logs.append({
                    "message": f"Failed to get Docker engine info: HTTP {resp.status_code}",
                    "level": "error",
                    "tags": {"source": "docker"}
                })
                return {"metrics": [], "logs": logs}
            
            info = resp.json()
            
            # Common tags
            tags = {
                "source": "docker",
                "engine_host": self.hostname,
                "server_version": server_version,
            }
            
            # Add engine metrics
            engine_metrics = {
                "docker_engine_containers": info.get("Containers", 0),
                "docker_engine_containers_running": info.get("ContainersRunning", 0),
                "docker_engine_containers_paused": info.get("ContainersPaused", 0),
                "docker_engine_containers_stopped": info.get("ContainersStopped", 0),
                "docker_engine_images": info.get("Images", 0),
            }
            
            for name, value in engine_metrics.items():
                metrics.append(Metric(
                    name=name,
                    value=value,
                    labels=tags.copy(),
                    timestamp=timestamp
                ))
            
        except Exception as e:
            logs.append({
                "message": f"Error collecting Docker engine metrics: {e}",
                "level": "error",
                "tags": {"source": "docker"}
            })
        
        return {"metrics": metrics, "logs": logs}

    def _collect_disk_usage_metrics(self, timestamp, server_version):
        metrics = []
        logs = []
        
        try:
            # Get disk usage info
            resp = self.session.get(f'{self.base_url}/system/df', timeout=5)
            if not resp.ok:
                logs.append({
                    "message": f"Failed to get Docker disk usage info: HTTP {resp.status_code}",
                    "level": "error",
                    "tags": {"source": "docker"}
                })
                return {"metrics": [], "logs": logs}
            
            df = resp.json()
            
            # Common tags
            base_tags = {
                "source": "docker",
                "engine_host": self.hostname,
                "server_version": server_version,
            }
            
            # Process container disk usage
            for container in df.get('Containers', []):
                try:
                    container_id = container.get('Id', 'unknown')[:12]
                    container_name = container.get('Names', ['unknown'])[0] if container.get('Names') else 'unknown'
                    
                    # Skip if filtered
                    if self.container_include and not any(pattern in container_name for pattern in self.container_include):
                        continue
                    if self.container_exclude and any(pattern in container_name for pattern in self.container_exclude):
                        continue
                    
                    tags = base_tags.copy()
                    tags.update({
                        "container_id": container_id,
                        "container_name": container_name,
                    })
                    
                    metrics.append(Metric(
                        name="docker_container_size",
                        value=container.get('SizeRw', 0),
                        labels=tags,
                        timestamp=timestamp
                    ))
                except Exception as e:
                    logs.append({
                        "message": f"Error processing container disk usage: {e}",
                        "level": "warn",
                        "tags": {"source": "docker"}
                    })
            
        except Exception as e:
            logs.append({
                "message": f"Error collecting Docker disk usage metrics: {e}",
                "level": "error",
                "tags": {"source": "docker"}
            })
        
        return {"metrics": metrics, "logs": logs}

    def _collect_swarm_metrics(self, timestamp, server_version):
        # This is a placeholder - swarm metrics require additional API calls
        # and are only relevant if Docker is running in swarm mode
        return {"metrics": [], "logs": []}

# Expose the plugin to the collector
def collect(config=None):
    collector = DockerStatsCollector(config or {})
    return collector.collect()