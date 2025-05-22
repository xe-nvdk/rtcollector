import requests_unixsocket
import time
import socket
from core.metric import Metric
from datetime import datetime
import concurrent.futures

class DockerStatsCollector:
    def __init__(self, config):
        self.config = config if "endpoint" in config or "swarm_enabled" in config else config.get('inputs', {}).get('docker', {})
        self.endpoint = self.config.get('endpoint', 'unix:///var/run/docker.sock')
        self.session = requests_unixsocket.Session()
        self.hostname = socket.gethostname()
        self.client = None  # Placeholder to avoid attribute errors for legacy code paths

    def collect_engine_metrics(self, timestamp):
        metrics = []
        # Use raw API for engine info
        try:
            resp = self.session.get('http+unix://%2Fvar%2Frun%2Fdocker.sock/info')
            info = resp.json() if resp.ok else {}
        except Exception as e:
            print(f"[docker] Failed to get engine info: {e}")
            return metrics

        try:
            resp = self.session.get('http+unix://%2Fvar%2Frun%2Fdocker.sock/version')
            version_info = resp.json() if resp.ok else {}
            server_version = version_info.get("Version", "unknown")
        except Exception as e:
            print(f"[docker] Failed to get engine version: {e}")
            server_version = "unknown"

        tags = {
            "engine_host": self.hostname,
            "server_version": server_version,
        }

        fields = {
            "n_cpus": info.get("NCPU"),
            "n_containers": info.get("Containers"),
            "n_containers_running": info.get("ContainersRunning"),
            "n_containers_paused": info.get("ContainersPaused"),
            "n_containers_stopped": info.get("ContainersStopped"),
            "n_images": info.get("Images"),
            "n_goroutines": info.get("NGoroutines"),
            "n_listener_events": info.get("NEventsListener"),
            "n_used_file_descriptors": info.get("NFd"),
            "memory_total": info.get("MemTotal"),
        }

        for metric_name, value in fields.items():
            if value is not None:
                metrics.append(Metric(metric_name, timestamp, value, tags))
        if self.config.get("debug", False):
            print(f"[docker] Collected engine metrics: {fields}")

        return metrics

    def collect_swarm_metrics(self, timestamp):
        # TODO: update this block to use raw API
        metrics = []
        return metrics

    def collect_disk_usage_metrics(self, timestamp):
        metrics = []
        # Use raw API for disk usage
        try:
            resp_df = self.session.get('http+unix://%2Fvar%2Frun%2Fdocker.sock/system/df')
            df = resp_df.json() if resp_df.ok else {}
            resp_version = self.session.get('http+unix://%2Fvar%2Frun%2Fdocker.sock/version')
            version_info = resp_version.json() if resp_version.ok else {}
            server_version = version_info.get("Version", "unknown")
            tags_base = {
                "engine_host": self.hostname,
                "server_version": server_version,
            }

            # Containers disk usage
            containers = df.get('Containers', [])
            for container in containers:
                try:
                    container_id = container.get('Id', 'unknown')
                    container_name = container.get('Names', ['unknown'])[0] if container.get('Names') else 'unknown'
                    size_rw = container.get('SizeRw', 0)
                    size_root_fs = container.get('SizeRootFs', 0)
                    tags = tags_base.copy()
                    tags.update({
                        "container_id": container_id,
                        "container_name": container_name,
                    })
                    metrics.append(Metric("docker_disk_usage_container_size_rw", timestamp, size_rw, tags))
                    metrics.append(Metric("docker_disk_usage_container_size_root_fs", timestamp, size_root_fs, tags))
                except Exception as e:
                    print(f"[docker] Error collecting disk usage for container {container.get('Id', '')}: {e}")
                    continue

            # Images disk usage
            images = df.get('Images', [])
            for image in images:
                try:
                    image_id = image.get('Id', 'unknown')
                    repo_tags = image.get('RepoTags', [])
                    image_name = repo_tags[0] if repo_tags else 'unknown'
                    shared_size = image.get('SharedSize', 0)
                    size = image.get('Size', 0)
                    tags = tags_base.copy()
                    tags.update({
                        "image_id": image_id,
                        "image_name": image_name,
                    })
                    metrics.append(Metric("docker_disk_usage_image_shared_size", timestamp, shared_size, tags))
                    metrics.append(Metric("docker_disk_usage_image_size", timestamp, size, tags))
                except Exception as e:
                    print(f"[docker] Error collecting disk usage for image {image.get('Id', '')}: {e}")
                    continue

            # Volumes disk usage
            volumes = df.get('Volumes', [])
            for volume in volumes:
                try:
                    volume_name = volume.get('Name', 'unknown')
                    volume_size = volume.get('UsageData', {}).get('Size', 0)
                    tags = tags_base.copy()
                    tags.update({
                        "volume_name": volume_name,
                    })
                    metrics.append(Metric("docker_disk_usage_volume_size", timestamp, volume_size, tags))
                except Exception as e:
                    print(f"[docker] Error collecting disk usage for volume {volume.get('Name', '')}: {e}")
                    continue

        except Exception as e:
            print(f"[docker] Failed to get disk usage info: {e}")
        return metrics

    def _collect_container_metrics(self, container, timestamp):
        metrics = []
        try:
            container_id = container.get("Id", "")
            container_name = container.get("Names", ["unknown"])
            container_name = container_name[0] if container_name else "unknown"
            # Get stats for each container
            stats_resp = self.session.get(f'http+unix://%2Fvar%2Frun%2Fdocker.sock/containers/{container_id}/stats?stream=false')
            stats = stats_resp.json() if stats_resp.ok else {}
            # Get image and version info
            container_image = container.get("Image", "unknown")
            container_version = "unknown"
            container_status = container.get("State", "unknown")
            short_id = container_id[:12] if container_id else "unknown"
            # Try to get RepoDigests if possible
            # TODO: update this block to use raw API for image details if needed
            tags = {
                "engine_host": self.hostname,
                # get server version for tags
                "server_version": "unknown",
                "container_image": container_image,
                "container_version": container_version,
                "container_name": container_name.lstrip('/'),
                "container_status": container_status,
                "container_id": short_id,
            }
            # CPU metrics
            cpu_stats = stats.get("cpu_stats", {}) if isinstance(stats.get("cpu_stats"), dict) else {}
            precpu_stats = stats.get("precpu_stats", {}) if isinstance(stats.get("precpu_stats"), dict) else {}
            cpu_usage = cpu_stats.get("cpu_usage", {}) if isinstance(cpu_stats.get("cpu_usage"), dict) else {}
            pre_cpu_usage = precpu_stats.get("cpu_usage", {}) if isinstance(precpu_stats.get("cpu_usage"), dict) else {}
            system_cpu_usage = cpu_stats.get("system_cpu_usage", 0)
            pre_system_cpu_usage = precpu_stats.get("system_cpu_usage", 0)
            percpu_usage_list = cpu_usage.get("percpu_usage", [])
            online_cpus = cpu_stats.get("online_cpus") or (len(percpu_usage_list) if isinstance(percpu_usage_list, list) else 0) or 1

            usage_total = cpu_usage.get("total_usage", 0)
            usage_in_usermode = cpu_usage.get("usage_in_usermode", 0)
            usage_in_kernelmode = cpu_usage.get("usage_in_kernelmode", 0)
            percpu_usage = percpu_usage_list if isinstance(percpu_usage_list, list) else []
            cpu_delta = usage_total - pre_cpu_usage.get("total_usage", 0)
            system_delta = system_cpu_usage - pre_system_cpu_usage
            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0

            metrics.append(Metric("docker_cpu_percent", timestamp, cpu_percent, tags))
            metrics.append(Metric("docker_cpu_usage_total", timestamp, usage_total, tags))
            metrics.append(Metric("docker_cpu_usage_in_usermode", timestamp, usage_in_usermode, tags))
            metrics.append(Metric("docker_cpu_usage_in_kernelmode", timestamp, usage_in_kernelmode, tags))
            metrics.append(Metric("docker_cpu_system", timestamp, system_cpu_usage, tags))
            # Per-CPU usage
            if isinstance(percpu_usage, list):
                for idx, val in enumerate(percpu_usage):
                    tags_percpu = tags.copy()
                    tags_percpu["cpu"] = str(idx)
                    metrics.append(Metric("docker_cpu_percpu_usage", timestamp, val, tags_percpu))

            # Memory metrics
            mem_stats = stats.get("memory_stats", {})
            if not isinstance(mem_stats, dict):
                mem_stats = {}
            mem_usage = mem_stats.get("usage", 0)
            mem_limit = mem_stats.get("limit", 1)
            mem_max_usage = mem_stats.get("max_usage", 0)
            mem_failcnt = mem_stats.get("failcnt", 0)
            mem_percent = (mem_usage / mem_limit) * 100.0 if mem_limit else 0.0
            metrics.append(Metric("docker_mem_usage", timestamp, mem_usage, tags))
            metrics.append(Metric("docker_mem_limit", timestamp, mem_limit, tags))
            metrics.append(Metric("docker_mem_max_usage", timestamp, mem_max_usage, tags))
            metrics.append(Metric("docker_mem_failcnt", timestamp, mem_failcnt, tags))
            metrics.append(Metric("docker_mem_percent", timestamp, mem_percent, tags))
            # Add memory stats fields if present (Telegraf: total_rss, total_cache, etc.)
            if isinstance(mem_stats, dict):
                for memfield in ["total_rss", "total_cache", "total_inactive_file", "total_active_file", "total_pgmajfault"]:
                    if memfield in mem_stats:
                        metrics.append(Metric(f"docker_mem_{memfield}", timestamp, mem_stats[memfield], tags))

            # Network metrics
            networks = stats.get("networks")
            if isinstance(networks, dict):
                for iface, net in networks.items():
                    net_tags = tags.copy()
                    net_tags["interface"] = iface
                    for key in [
                        ("rx_bytes", "docker_net_rx_bytes"),
                        ("rx_packets", "docker_net_rx_packets"),
                        ("rx_errors", "docker_net_rx_errors"),
                        ("rx_dropped", "docker_net_rx_dropped"),
                        ("tx_bytes", "docker_net_tx_bytes"),
                        ("tx_packets", "docker_net_tx_packets"),
                        ("tx_errors", "docker_net_tx_errors"),
                        ("tx_dropped", "docker_net_tx_dropped"),
                    ]:
                        if isinstance(net, dict) and key[0] in net:
                            metrics.append(Metric(key[1], timestamp, net[key[0]], net_tags))

            # Block IO metrics
            blkio_stats = stats.get("blkio_stats")
            if not isinstance(blkio_stats, dict):
                blkio_stats = {}
            for stat_type in [
                ("io_service_bytes_recursive", "docker_blkio_service_bytes"),
                ("io_serviced_recursive", "docker_blkio_serviced"),
                ("io_queue_recursive", "docker_blkio_queue"),
                ("io_service_time_recursive", "docker_blkio_service_time"),
                ("io_wait_time_recursive", "docker_blkio_wait_time"),
                ("io_merged_recursive", "docker_blkio_merged"),
                ("io_time_recursive", "docker_blkio_time"),
                ("sectors_recursive", "docker_blkio_sectors"),
            ]:
                stat_list = blkio_stats.get(stat_type[0], [])
                if isinstance(stat_list, list):
                    for entry in stat_list:
                        blk_tags = tags.copy()
                        if isinstance(entry, dict):
                            if "major" in entry and "minor" in entry:
                                blk_tags["device"] = f"{entry['major']}:{entry['minor']}"
                            if "op" in entry:
                                blk_tags["op"] = entry["op"]
                            val = entry.get("value")
                            if val is not None:
                                metrics.append(Metric(stat_type[1], timestamp, val, blk_tags))

            # Container health/status metrics - not available directly, would require /containers/(id)/json
            # TODO: update this block to use raw API for container health/status metrics

        except Exception as e:
            print(f"[docker] Error collecting stats from {container.get('Names', ['unknown'])[0]}: {e}")
        return metrics

    def collect(self):
        metrics = []
        timestamp = int(time.time() * 1000)

        # Use raw API for containers list
        try:
            containers_resp = self.session.get('http+unix://%2Fvar%2Frun%2Fdocker.sock/containers/json')
            containers = containers_resp.json() if containers_resp.ok else []
        except Exception as e:
            print(f"[docker] Failed to list containers: {e}")
            return []

        # Parallelize container stats collection using ThreadPoolExecutor
        container_metrics = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self._collect_container_metrics, container, timestamp) for container in containers]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    container_metrics.extend(result)
        metrics.extend(container_metrics)

        engine_metrics = self.collect_engine_metrics(timestamp)
        metrics.extend(engine_metrics)

        # Only collect swarm metrics if enabled in config
        if self.config.get("swarm_enabled", False):
            swarm_metrics = self.collect_swarm_metrics(timestamp)
            metrics.extend(swarm_metrics)
        else:
            if self.config.get("debug", False):
                print("[docker] Swarm metrics collection skipped (disabled in config)")

        disk_usage_metrics = self.collect_disk_usage_metrics(timestamp)
        metrics.extend(disk_usage_metrics)

        if self.config.get("debug", False):
            print(f"[docker] Collected total metrics count: {len(metrics)}")

        return metrics


    def collect_swarm_metrics(self, timestamp):
        metrics = []
        try:
            services = self.client.services.list()
            for service in services:
                try:
                    service_name = service.attrs.get('Spec', {}).get('Name', 'unknown')
                    service_id = service.id
                    service_mode = 'unknown'
                    spec_mode = service.attrs.get('Spec', {}).get('Mode', {})
                    if 'Replicated' in spec_mode:
                        service_mode = 'replicated'
                    elif 'Global' in spec_mode:
                        service_mode = 'global'
                    service_status = service.attrs.get('ServiceStatus', {})
                    desired_tasks = service_status.get('DesiredTasks', 0)
                    running_tasks = service_status.get('RunningTasks', 0)

                    tags = {
                        "engine_host": self.hostname,
                        "server_version": self.client.version().get("Version", "unknown"),
                        "service_id": service_id,
                        "service_name": service_name,
                        "service_mode": service_mode,
                    }
                    metrics.append(Metric("docker_swarm_desired_tasks", timestamp, desired_tasks, tags))
                    metrics.append(Metric("docker_swarm_running_tasks", timestamp, running_tasks, tags))
                except Exception as e:
                    print(f"[docker] Error collecting swarm metrics for service {service.id}: {e}")
                    continue
        except Exception as e:
            print(f"[docker] Failed to list swarm services: {e}")
        return metrics

    def collect_disk_usage_metrics(self, timestamp):
        metrics = []
        try:
            resp_df = self.session.get('http+unix://%2Fvar%2Frun%2Fdocker.sock/system/df')
            df = resp_df.json() if resp_df.ok else {}
            resp_version = self.session.get('http+unix://%2Fvar%2Frun%2Fdocker.sock/version')
            version_info = resp_version.json() if resp_version.ok else {}
            server_version = version_info.get("Version", "unknown")
            tags_base = {
                "engine_host": self.hostname,
                "server_version": server_version,
            }

            containers = df.get('Containers', [])
            for container in containers:
                try:
                    container_id = container.get('Id', 'unknown')
                    container_name = container.get('Names', ['unknown'])[0] if container.get('Names') else 'unknown'
                    size_rw = container.get('SizeRw', 0)
                    size_root_fs = container.get('SizeRootFs', 0)
                    tags = tags_base.copy()
                    tags.update({
                        "container_id": container_id,
                        "container_name": container_name,
                    })
                    metrics.append(Metric("docker_disk_usage_container_size_rw", timestamp, size_rw, tags))
                    metrics.append(Metric("docker_disk_usage_container_size_root_fs", timestamp, size_root_fs, tags))
                except Exception as e:
                    print(f"[docker] Error collecting disk usage for container {container.get('Id', '')}: {e}")
                    continue

            images = df.get('Images', [])
            for image in images:
                try:
                    image_id = image.get('Id', 'unknown')
                    repo_tags = image.get('RepoTags', [])
                    image_name = repo_tags[0] if repo_tags else 'unknown'
                    shared_size = image.get('SharedSize', 0)
                    size = image.get('Size', 0)
                    tags = tags_base.copy()
                    tags.update({
                        "image_id": image_id,
                        "image_name": image_name,
                    })
                    metrics.append(Metric("docker_disk_usage_image_shared_size", timestamp, shared_size, tags))
                    metrics.append(Metric("docker_disk_usage_image_size", timestamp, size, tags))
                except Exception as e:
                    print(f"[docker] Error collecting disk usage for image {image.get('Id', '')}: {e}")
                    continue

            volumes = df.get('Volumes', [])
            for volume in volumes:
                try:
                    volume_name = volume.get('Name', 'unknown')
                    volume_size = volume.get('UsageData', {}).get('Size', 0)
                    tags = tags_base.copy()
                    tags.update({
                        "volume_name": volume_name,
                    })
                    metrics.append(Metric("docker_disk_usage_volume_size", timestamp, volume_size, tags))
                except Exception as e:
                    print(f"[docker] Error collecting disk usage for volume {volume.get('Name', '')}: {e}")
                    continue

        except Exception as e:
            print(f"[docker] Failed to get disk usage info: {e}")
        return metrics

# The duplicate collect method using the Docker SDK has been removed as it is deprecated and replaced by the new implementation using requests_unixsocket.

# Expose the plugin to the collector
def collect(config=None):
    collector_config = config or {}
    collector = DockerStatsCollector(collector_config)
    return collector.collect()