from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import os
from contextlib import asynccontextmanager
from .database import db
from .ingestion import ingest_events
from .algorithms import run_clustering
import json

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.connect()
    yield
    db.close()

app = FastAPI(lifespan=lifespan)

# Mount static files correctly
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    content = await file.read()
    try:
        events = json.loads(content)
        processed = ingest_events(events)
        run_clustering()
        return {"status": "success", "processed": processed, "total_events": len(events)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/graph")
def get_graph():
    if not db.driver:
        return {"nodes": [], "edges": []}
        
    nodes = []
    edges = []
    
    with db.driver.session() as session:
        nodes_result = session.run("MATCH (n:Employee) RETURN n.id AS id, n.cluster_id AS cluster")
        for record in nodes_result:
            # We'll try to find metadata in data/employees.json if it exists to add name and dept
            nodes.append({
                "id": record["id"],
                "cluster_id": record["cluster"] or 0,
                "label": record["id"] # fallback
            })
            
        edges_result = session.run("""
        MATCH (s:Employee)-[r:DAILY_ACTIVITY]->(t:Employee)
        RETURN s.id AS source, t.id AS target, sum(r.count) AS weight, sum(r.out_of_hours_count) AS out_of_hours
        """)
        for record in edges_result:
            edges.append({
                "from": record["source"],
                "to": record["target"],
                "value": record["weight"],
                "outOfHours": record["out_of_hours"] or 0,
                "title": f"Messages: {record['weight']}" # Tooltip on hover/click using vis.js natively
            })
            
    # Merge employee metadata for names and departments natively if available
    try:
        with open("../event-data-generator/data/employees.json", "r") as f:
            emps = json.load(f)
            emap = {e["employee_id"]: e for e in emps}
            for n in nodes:
                if n["id"] in emap:
                    emp = emap[n["id"]]
                    n["label"] = f"{emp['name']} ({emp['department']})"
                    n["name"] = emp["name"]
                    n["department"] = emp["department"]
                    n["role"] = emp.get("role", "Unknown")
    except Exception as e:
        print(f"No employee metadata found locally. Using IDs only. {e}")
        
    return {"nodes": nodes, "edges": edges}

@app.get("/")
def serve_ui():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())
