# Database Schema Documentation

## Overview

The agent uses SQLite for storing runtime data, metrics, and game state. The database consists of several tables designed for efficient logging and analysis.

## Tables

### runs

Stores metadata about each run session.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| start_time | DATETIME | When run began |
| end_time | DATETIME | When run ended |
| status | TEXT | "active", "completed", "failed" |
| config | JSON | Run configuration |
| notes | TEXT | Additional notes |

**Example Query:**
```sql
SELECT * FROM runs WHERE status = 'completed' ORDER BY start_time DESC;
```

### events

Logs all game actions and events.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| run_id | INTEGER | Foreign key to runs |
| timestamp | DATETIME | When event occurred |
| type | TEXT | "action", "state", "error" |
| data | JSON | Event details |
| context | JSON | Game state context |

**Example Query:**
```sql
SELECT * FROM events
WHERE run_id = 1 AND type = 'action'
ORDER BY timestamp;
```

### state_snapshots

Periodic game state checkpoints.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| run_id | INTEGER | Foreign key to runs |
| timestamp | DATETIME | When snapshot taken |
| location | TEXT | Current location |
| party | JSON | Party Pokémon data |
| badges | INTEGER | Badge flags |
| money | INTEGER | Current money |
| inventory | JSON | Item inventory |
| memory_dump | BLOB | Raw memory snapshot |

**Example Query:**
```sql
SELECT timestamp, location, badges FROM state_snapshots
WHERE run_id = 1 ORDER BY timestamp;
```

### metrics

Performance and usage metrics.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| run_id | INTEGER | Foreign key to runs |
| timestamp | DATETIME | When metric recorded |
| metric_type | TEXT | "fps", "api_latency", "memory_usage" |
| value | REAL | Metric value |
| details | JSON | Additional context |

**Example Query:**
```sql
SELECT metric_type, AVG(value) FROM metrics
WHERE run_id = 1 GROUP BY metric_type;
```

## Indexes

Recommended indexes for performance:

```sql
CREATE INDEX idx_events_run ON events(run_id);
CREATE INDEX idx_events_type ON events(type);
CREATE INDEX idx_snapshots_run ON state_snapshots(run_id);
CREATE INDEX idx_metrics_run ON metrics(run_id);
CREATE INDEX idx_metrics_type ON metrics(metric_type);
```

## Usage Examples

### Get Run Summary

```sql
SELECT
  r.id,
  r.start_time,
  r.end_time,
  COUNT(e.id) as actions,
  MAX(s.badges) as final_badges
FROM runs r
LEFT JOIN events e ON r.id = e.run_id
LEFT JOIN state_snapshots s ON r.id = s.run_id
WHERE r.id = 1;
```

### Analyze Battle Performance

```sql
SELECT
  s.location,
  COUNT(e.id) as battles,
  SUM(CASE WHEN e.data->>'result' = 'win' THEN 1 ELSE 0 END) as wins
FROM state_snapshots s
JOIN events e ON s.run_id = e.run_id
WHERE e.type = 'battle' AND s.run_id = 1
GROUP BY s.location;
```

### Track Progress Over Time

```sql
SELECT
  s.timestamp,
  s.location,
  s.badges,
  (SELECT COUNT(*) FROM events e2
   WHERE e2.run_id = s.run_id AND e2.timestamp < s.timestamp) as actions
FROM state_snapshots s
WHERE s.run_id = 1
ORDER BY s.timestamp;
```

## Database Initialization

The database is automatically initialized when the agent starts. The schema is defined in `database/database.py`:

```python
def initialize_database():
    with sqlite3.connect('agent.db') as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (...)
        """)
        # Create other tables...
        conn.commit()
```

## Backup and Maintenance

**Recommended Practices:**
- Backup database before major runs
- Vacuum database periodically: `VACUUM;`
- Analyze query performance: `ANALYZE;`

**Exporting Data:**
```bash
sqlite3 agent.db .dump > backup.sql