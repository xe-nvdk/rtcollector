from core.metric import Metric
import redis
import time

def collect(config) -> tuple:

    # If config is a dict with a 'redis' key, use that as our config
    if isinstance(config, dict) and "redis" in config:
        redis_config = config["redis"]
    else:
        redis_config = config

    # Required configuration parameters
    host = redis_config.get("host")
    port = redis_config.get("port")
    password = redis_config.get("password")
    db = redis_config.get("db", 0)  # db is optional, defaults to 0

    if not all([host, port]):
        print("[redis] Error: Missing required configuration. Please check config.yml for host and port settings.")
        return [], []

    try:
        r = redis.Redis(host=host, port=port, password=password, db=db)
        info = r.info()
    except Exception as e:
        print(f"[redis] Error connecting to Redis: {e}")
        return [], []

    timestamp = time.time()
    metrics = []
    logs = []

    keys_to_collect = [
        'uptime_in_seconds',
        'connected_clients',
        'used_memory',
        'used_memory_rss',
        'used_memory_peak',
        'used_memory_lua',
        'mem_fragmentation_ratio',
        'total_commands_processed',
        'instantaneous_ops_per_sec',
        'total_connections_received',
        'rejected_connections',
        'expired_keys',
        'evicted_keys',
        'keyspace_hits',
        'keyspace_misses',
        'pubsub_channels',
        'pubsub_patterns',
        'latest_fork_usec',
        'connected_slaves',
        'blocked_clients',
        'instantaneous_input_kbps',
        'instantaneous_output_kbps',
        'sync_full',
        'sync_partial_ok',
        'sync_partial_err',
        'used_cpu_sys',
        'used_cpu_user',
        'used_cpu_sys_children',
        'used_cpu_user_children',
        'repl_backlog_size',
        'rdb_changes_since_last_save',
        'aof_enabled',
        'aof_last_rewrite_time_sec',
        'connected_replication_backlog',
        'repl_backlog_histlen',
        'rdb_last_bgsave_status',
        'rdb_last_save_time',
        'aof_rewrite_scheduled',
        'aof_last_rewrite_status',
        'aof_last_bgrewrite_status',
        'aof_current_rewrite_time_sec',
        'aof_last_write_status',
        'total_net_input_bytes',
        'total_net_output_bytes',
        'total_reads_processed',
        'total_writes_processed',
        'active_defrag_running',
        'lazyfree_pending_objects'
    ]

    for key in keys_to_collect:
        if key in info:
            value = info[key]
            metric_name = f'redis_{key}'
            labels = {'host': host, 'port': str(port)}
            if isinstance(value, (int, float)):
                metric = Metric(metric_name, value, timestamp, labels)
                metrics.append(metric)
            else:
                log_entry = {
                    "name": metric_name,
                    "timestamp": timestamp,
                    "value": str(value),
                    "labels": labels
                }
                logs.append(log_entry)

    # Add keyspace metrics
    if 'keyspace' in info:
        for db, db_info in info['keyspace'].items():
            for k, v in db_info.items():
                metric_name = f'redis_keyspace_{db}_{k}'
                metric = Metric(metric_name, v, timestamp, {'host': host, 'port': str(port)})
                metrics.append(metric)

    # Add replication metrics
    if 'replication' in info:
        repl_info = info['replication']
        for key, value in repl_info.items():
            if isinstance(value, (int, float)):
                metric_name = f'redis_replication_{key}'
                metric = Metric(metric_name, value, timestamp, {'host': host, 'port': str(port)})
                metrics.append(metric)

    return metrics, logs
