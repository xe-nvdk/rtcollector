import time
import pymysql
from core.metric import Metric
from utils.system import get_hostname

def collect(config=None):
    if config is None:
        config = {}
    
    # If config is a dict with a 'mariadb' key, use that as our config
    if isinstance(config, dict) and "mariadb" in config:
        db_config = config["mariadb"]
    else:
        db_config = config
    
    metric_names = db_config.get("metrics", ["Threads_connected", "Connections", "Uptime", "Questions"])
    hostname = db_config.get("hostname", get_hostname())

    # Required configuration parameters
    host = db_config.get("host")
    port = db_config.get("port")
    user = db_config.get("user")
    password = db_config.get("password")

    if not all([host, port, user, password]):
        print("[mariadb] Error: Missing required configuration. Please check config.yml for host, port, user, and password settings.")
        return []

    conn = None

    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            connect_timeout=5
        )
        with conn.cursor() as cursor:
            cursor.execute("SHOW GLOBAL STATUS")
            results = cursor.fetchall()
    except Exception as e:
        print(f"[mariadb] Error connecting or querying MariaDB: {e}")
        return []

    timestamp = int(time.time() * 1000)
    metrics = []

    for key, value in results:
        if key in metric_names:
            try:
                float_val = float(value)
            except (ValueError, TypeError):
                continue
            labels = {
                "host": hostname,
                "metric": key.lower(),
            }
            metric = Metric(
                name=f"mariadb_{key.lower()}",
                value=float_val,
                timestamp=timestamp,
                labels=labels
            )
            metrics.append(metric)

    return metrics
