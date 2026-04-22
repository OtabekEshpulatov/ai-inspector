# Module 1 — Relationship Intelligence Model

## What We're Building
Map real relationships between employees, calculate relationship strength, and detect clusters and suspicious groups.

## Approach
- Start with **fake data** (realistic patterns)
- Abstract structure → switching to real data later = only pipeline change
- **No ML for now** — rules + algorithms first
- ML added later when real data exists

## Core Data Structure

```json
{
  "event_id":  "msg_123",
  "sender":    "employee_id",
  "receiver":  "employee_id",
  "timestamp": "datetime",
  "channel":   "email | telegram | slack | file_share | usb",
  "metadata": {
    "size": "",
    "file_type": "",
    "sensitivity_level": ""
  }
}
```

> `event_id` is required for idempotency — every event must have a unique identifier.

## Tech Stack

| Layer | Technology |
|---|---|
| Graph DB | Neo4j |
| Graph algorithms | NetworkX + python-louvain |
| Data generation | Python + Faker |
| Visualization | Neo4j Bloom or D3.js |
| API | FastAPI |
| Idempotency store | Redis |

## Data Ingestion Architecture

Data files are synced from a remote server into a **dedicated local directory**. Timing is unpredictable — could be hourly, daily, or manual.

Key principle:
> Sync time is irrelevant. What matters is the **timestamp inside each event.**

### File Details
- **Format:** JSON
- **Location:** dedicated directory (created in advance)
- **After reading:** files stay as-is, never deleted or moved
- **App behavior:** reads all files in directory **once on startup only**

### Startup Flow

```
App starts
        ↓
Read all JSON files from directory
        ↓
For each event in each file:
    → Check event_id in Redis
    → If exists: SKIP (already processed)
    → If new:
        → Extract date bucket from event timestamp
        → Increment daily bucket count in Neo4j
        → Store event_id in Redis (30 day TTL)
        ↓
Recalculate aggregated weights on all edges
        ↓
Run Louvain clustering on weighted graph
        ↓
Update cluster_id on each employee node in Neo4j
        ↓
Run spike detection across daily buckets
```

### Idempotency via Redis

```python
# Check before processing
if redis.exists(event_id):
    return  # skip

# Process event...

# Mark as processed with 30 day auto-expiry
redis.set(event_id, "1", ex=30*24*60*60)
```

No manual cleanup needed — Redis auto-expires keys after 30 days.

### Daily Bucketing

Events are grouped by **date extracted from timestamp**, not sync time.
Bucket key format: `sender_id:receiver_id:date`

```python
bucket = event["timestamp"].date()  # "2024-04-21"
key    = f"{sender_id}:{receiver_id}:{bucket}"
```

Direction is preserved — `emp_001:emp_002:2024-04-21` and `emp_002:emp_001:2024-04-21` are separate buckets.

Same day events from multiple syncs are safely incremented:

```cypher
MERGE (a)-[r:DAILY_ACTIVITY {date: $bucket}]->(b)
ON CREATE SET r.count = $new_count
ON MATCH SET  r.count = r.count + $new_count
```

### What Buckets Are Used For

| Use | How |
|---|---|
| Relationship strength | Sum all buckets → calculate weight |
| Spike detection | Compare today's bucket vs previous days average |
| Growth trend | Compare week-over-week bucket averages |
| Recency | Date of last non-zero bucket |
| Time patterns | Check bucket timestamps for late night / weekend activity |
| Relationship lifecycle | First bucket = relationship start date |
| Cluster evolution | Track cluster_id changes over time |
| Chain detection | Correlate spikes across different pairs on same day |

### Spike Detection (rule-based)

```python
avg = mean(previous_days_counts)
std = stddev(previous_days_counts)

if today_count > avg + 2 * std:
    flag as SPIKE 🚨
```

### Growth Trend Detection

```python
first_half_avg  = mean(counts[:len(counts)//2])
second_half_avg = mean(counts[len(counts)//2:])

growth = (second_half_avg - first_half_avg) / first_half_avg * 100

if growth > 100:  trend = "EXPLOSIVE"
elif growth > 50: trend = "FAST GROWING"
elif growth > 20: trend = "GROWING"
elif growth < -50:trend = "FADING"
else:             trend = "STABLE"
```

## How Relationships Work
- Every communication = edge between two nodes in Neo4j
- Weight stored on edge as a property
- **Hybrid approach** — raw daily buckets + precomputed aggregated weight
- Weight recalculated on every startup after new events are ingested
- Strength levels: `LOW` / `MEDIUM` / `HIGH` / `CRITICAL`

### Weight Formula
```python
recency_factor   = 1 / (days_since_last_interaction + 1)
channel_factor   = channels_used / total_channels
bidirectionality = min(A_to_B, B_to_A) / max(A_to_B, B_to_A)

weight = message_count × recency_factor × channel_factor × bidirectionality
```

### Strength Bucketing
```python
if weight >= 80:    strength = "CRITICAL"
elif weight >= 60:  strength = "HIGH"
elif weight >= 30:  strength = "MEDIUM"
else:               strength = "LOW"
```

### Neo4j Edge Example
```cypher
(Alice)-[:COMMUNICATES_WITH {
    message_count: 150,
    email_count: 100,
    telegram_count: 50,
    first_interaction: "2024-01-01",
    last_interaction: "2024-04-21",
    weight: 87.5,
    strength: "CRITICAL",
    trend: "EXPLOSIVE",
    growth_rate: 106.3
}]->(Bob)
```

## Cluster Detection

### How Louvain Works
```
Pull all edges + weights from Neo4j
        ↓
Build weighted graph in NetworkX (in memory)
        ↓
Run Louvain algorithm
        ↓
Each employee assigned a cluster_id
        ↓
Store cluster_id back on employee node in Neo4j
```

### Louvain in Code
```python
import networkx as nx
from community import best_partition

G = nx.Graph()
# Add edges with weights from Neo4j
G.add_edge("alice", "bob", weight=87.5)

partition = best_partition(G, weight='weight')
# → { "alice": 0, "bob": 0, "dave": 1, ... }
```

### Suspicious Cluster Rules
```python
# Cross-department cluster → suspicious
if cluster contains members from 3+ departments:
    flag as SUSPICIOUS 🚨

# External communication cluster → suspicious
if cluster contains external contacts:
    flag as SUSPICIOUS 🚨

# Late night cluster → suspicious
if cluster activity mostly outside 9am-6pm:
    flag as SUSPICIOUS 🚨
```

## ML — Future Plan
ML is introduced later when:
- Enough real data exists
- Rules produce too many false positives
- Per-person dynamic baselines are needed

Uses **unsupervised learning** — no labels needed, learns "normal" from raw data automatically.

## Important Notes for Future

1. **Concept drift** — Model needs short-term + long-term baseline to detect slow behavioral drift
2. **Cold start** — Use role-based baseline for new employees, transition to personal baseline over ~2 weeks
3. **Historical data** — Train unsupervised models from day one using existing communication logs
4. **Labeled data** — If any confirmed insider threat cases exist, semi-supervised learning becomes possible
5. **Spike detection** — Store interaction counts per daily bucket, not just totals. Use separate interval nodes in Neo4j for scalability
6. **Idempotency** — Every event must have a unique event_id. Check Redis before processing to avoid double counting. Auto-expires after 30 days
7. **Daily buckets** — 365 buckets/year per employee pair, negligible storage. Keep all for MVP. Add aggregation strategy later if needed

## Fake Data Generator Requirements
Generate realistic patterns including:
- Employee profiles with departments and roles
- Natural communication clusters (teams talk within team)
- Suspicious hidden groups (cross-department secret clusters)
- Time patterns (work hours 9am–6pm, occasional late night)
- Behavior changes over time (e.g. activity spike before resignation)

## Next Step
Build the **fake data generator** in Python.