# Relationship Intelligence App

A complete backend graph analytics pipeline constructed with FastAPI, Neo4j, Redis, and Vis.js. 

Designed to algorithmically uncover hidden sub-communities, visualize communication topology, and highlight sudden data-exfiltration anomalies in near real-time.

## Tech Stack
- **Graph Database**: Neo4j
- **Idempotency & Caching**: Redis
- **Community Algorithms**: Python NetworkX + Louvain (`best_partition`)
- **API Server**: FastAPI
- **Frontend**: Vis.js

## Architecture
1. **Idempotency Layer**: Raw JSON events hit `POST /ingest` and are instantly hashed against a 30-day Redis TTL to prevent double-counting.
2. **Aggregated Storage**: Verified distinct queries compile directly into Graph `DAILY_ACTIVITY` bounds against Neo4j containing complex timestamps (`out_of_hours_count`).
3. **Graph Clustering**: Overweight/dense groupings are extracted via NetworkX, sliced algorithmically using Louvain modularity, and mapped to a unique `cluster_id` property.
4. **Visual Dashboard**: Serving directly off `GET /` natively visualizes the isolated subgroups, visually differentiating formal HR configurations vs. reality.

## Quickstart

Run via Docker:

```bash
docker compose up -d --build
```
Navigate to `http://localhost:8000` to view the unified graph dashboard dynamically scaling in real-time.

### API Endpoints
- **`GET /`**: View interactive force-directed graph UI natively.
- **`POST /ingest`**: Exposes the `upload_file` parameter allowing bulk `.json` communication logs ingestion.
- **`GET /graph`**: Programmatic access to the parsed nodes and relationships formatting optimized for UI consumption.
