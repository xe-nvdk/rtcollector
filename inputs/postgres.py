import psycopg2
import time
from core.metric import Metric

DEFAULT_QUERY = """
SELECT datname,
       numbackends,
       xact_commit,
       xact_rollback,
       blks_read,
       blks_hit,
       tup_returned,
       tup_fetched,
       tup_inserted,
       tup_updated,
       tup_deleted,
       conflicts,
       temp_files,
       temp_bytes,
       deadlocks,
       blk_read_time,
       blk_write_time
FROM pg_stat_database
WHERE datname IS NOT NULL AND datname NOT IN ('template0', 'template1');
"""

BGWRITER_QUERY = """
SELECT checkpoints_timed, checkpoints_req, checkpoint_write_time, 
       checkpoint_sync_time, buffers_checkpoint, buffers_clean, 
       maxwritten_clean, buffers_backend, buffers_backend_fsync, 
       buffers_alloc
FROM pg_stat_bgwriter;
"""

REPLICATION_QUERY = """
SELECT application_name, state, sent_lsn, write_lsn, 
       flush_lsn, replay_lsn, 
       EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds
FROM pg_stat_replication;
"""

def collect(config=None):
    metrics = []
    logs = []

    host = config.get("host", "localhost")
    port = config.get("port", 5432)
    user = config.get("user", "postgres")
    password = config.get("password", "")
    dbname = config.get("dbname", "postgres")
    queries = config.get("queries", [])
    collect_bgwriter = config.get("collect_bgwriter", True)
    collect_replication = config.get("collect_replication", True)

    try:
        conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname=dbname
        )
        cur = conn.cursor()

        if queries:
            for q in queries:
                name = q.get("name")
                sql = q.get("sql")

                try:
                    cur.execute(sql)
                    row = cur.fetchone()
                    if row and len(row) == 1:
                        value = row[0]
                        if value is None or not isinstance(value, (int, float)):
                            logs.append({
                                "message": f"Query '{name}' returned NULL or non-numeric value, skipping metric.",
                                "level": "warn",
                                "tags": {"source": "postgres", "query": name}
                            })
                            continue
                        metrics.append(Metric(
                            name=name,
                            value=value,
                            labels={"source": "postgres", "query": name},
                            timestamp=int(time.time() * 1000)
                        ))
                    else:
                        logs.append({
                            "message": f"Unexpected result for query '{name}'",
                            "level": "warn",
                            "tags": {"source": "postgres", "query": name}
                        })
                except Exception as qe:
                    logs.append({
                        "message": f"Query error '{name}': {qe}",
                        "level": "error",
                        "tags": {"source": "postgres", "query": name}
                    })
        else:
            cur.execute(DEFAULT_QUERY)
            columns = [desc[0] for desc in cur.description]
            for row in cur.fetchall():
                print(f"[DEBUG] Row from pg_stat_database: {dict(zip(columns, row))}")
                if not row[0] or not isinstance(row[0], str):
                    logs.append({
                        "message": f"Row with NULL or invalid datname encountered, skipping.",
                        "level": "warn",
                        "tags": {"source": "postgres"}
                    })
                    continue
                labels = {"source": "postgres", "database": row[0]}
                for i in range(1, len(columns)):
                    value = row[i]
                    if value is None or not isinstance(value, (int, float)):
                        logs.append({
                            "message": f"Field '{columns[i]}' in database '{row[0]}' is NULL or not numeric, skipping metric.",
                            "level": "warn",
                            "tags": {"source": "postgres", "database": row[0], "column": columns[i]}
                        })
                        continue
                    name = f"postgres_{columns[i]}"
                    metrics.append(Metric(name=name, value=value, labels=labels.copy(), timestamp=int(time.time() * 1000)))

        # Collect bgwriter metrics
        if collect_bgwriter:
            try:
                cur.execute(BGWRITER_QUERY)
                columns = [desc[0] for desc in cur.description]
                row = cur.fetchone()
                if row:
                    print(f"[DEBUG] Row from pg_stat_bgwriter: {dict(zip(columns, row))}")
                    for i, col in enumerate(columns):
                        value = row[i]
                        if value is None or not isinstance(value, (int, float)):
                            continue
                        name = f"postgres_bgwriter_{col}"
                        metrics.append(Metric(
                            name=name,
                            value=value,
                            labels={"source": "postgres", "type": "bgwriter"},
                            timestamp=int(time.time() * 1000)
                        ))
            except Exception as e:
                logs.append({
                    "message": f"Error collecting bgwriter metrics: {e}",
                    "level": "error",
                    "tags": {"source": "postgres", "query": "bgwriter"}
                })

        # Collect replication metrics
        if collect_replication:
            try:
                cur.execute(REPLICATION_QUERY)
                columns = [desc[0] for desc in cur.description]
                for row in cur.fetchall():
                    if not row[0] or not isinstance(row[0], str):
                        continue
                    
                    app_name = row[0]
                    state = row[1]
                    labels = {"source": "postgres", "type": "replication", "application": app_name, "state": state}
                    
                    # Only add lag_seconds as a metric since LSN values are not numeric
                    lag_idx = columns.index("lag_seconds")
                    if lag_idx >= 0 and row[lag_idx] is not None and isinstance(row[lag_idx], (int, float)):
                        metrics.append(Metric(
                            name="postgres_replication_lag_seconds",
                            value=row[lag_idx],
                            labels=labels,
                            timestamp=int(time.time() * 1000)
                        ))
            except Exception as e:
                logs.append({
                    "message": f"Error collecting replication metrics: {e}",
                    "level": "error",
                    "tags": {"source": "postgres", "query": "replication"}
                })

        cur.close()
        conn.close()

    except Exception as e:
        logs.append({
            "message": f"PostgreSQL collection error: {e}",
            "level": "error",
            "tags": {"source": "postgres"}
        })

    return {
        "postgres_metrics": metrics,
        "postgres_logs": logs
    }
