from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import io
import os
from contextlib import asynccontextmanager
from .database import db
from .ingestion import ingest_xlsx
from .algorithms import run_clustering

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
    try:
        content = await file.read()
        # Read Excel file
        df = pd.read_excel(io.BytesIO(content))
        processed = ingest_xlsx(df)
        
        # Trigger clustering to group employees with similar destination patterns
        run_clustering()
        
        return {
            "status": "success", 
            "processed": processed, 
            "total_rows": len(df)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/graph")
def get_graph():
    if not db.driver:
        return {"nodes": [], "edges": []}
        
    nodes = []
    edges = []
    
    with db.driver.session() as session:
        # Fetch Employees
        emp_result = session.run("""
            MATCH (e:Employee)
            OPTIONAL MATCH (e)-[:BELONGS_TO]->(g:Group)
            RETURN e.name AS name, g.name AS group, e.cluster_id AS cluster
        """)
        for record in emp_result:
            nodes.append({
                "id": record["name"],
                "label": record["name"],
                "group": record["group"] or "Unknown",
                "cluster_id": record["cluster"] or 0,
                "type": "Employee"
            })
            
        # Fetch Destinations
        dest_result = session.run("MATCH (d:Destination) RETURN d.name AS name")
        for record in dest_result:
            nodes.append({
                "id": record["name"],
                "label": record["name"][:30] + "..." if len(record["name"]) > 30 else record["name"],
                "full_name": record["name"],
                "type": "Destination"
            })
            
        # Fetch Relationships
        edges_result = session.run("""
            MATCH (s:Employee)-[r:TRANSFERRED_TO]->(t:Destination)
            RETURN s.name AS source, t.name AS target, r.weight AS weight, 
                   r.channel AS channel, r.severity AS severity, r.action AS action
        """)
        for record in edges_result:
            edges.append({
                "from": record["source"],
                "to": record["target"],
                "value": record["weight"],
                "channel": record["channel"],
                "severity": record["severity"],
                "action": record["action"],
                "title": f"Risk Score: {record['weight']} | Channel: {record['channel']} | Action: {record['action']}"
            })
            
    return {"nodes": nodes, "edges": edges}

@app.get("/")
def serve_ui():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())
