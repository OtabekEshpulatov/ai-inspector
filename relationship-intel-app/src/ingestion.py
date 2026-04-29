from .database import db
from datetime import datetime
import pandas as pd

def ingest_xlsx(df: pd.DataFrame):
    processed = 0
    if not db.driver:
        print("Neo4j database not connected. Skipping DB insertion.")
        return 0

    # Replace NaN values with empty strings to prevent "nan" nodes
    df = df.fillna('')

    with db.driver.session() as session:
        for _, row in df.iterrows():
            # Extract and sanitize fields
            employee = str(row.get('Employee', '')).strip()
            group = str(row.get('Group', 'Unknown')).strip()
            destination = str(row.get('Destination', '')).strip()
            channel = str(row.get('Channel', 'Unknown')).strip()
            severity = str(row.get('Severity', 'Low')).strip()
            action = str(row.get('Action', 'Warned')).strip()
            
            if not employee or not destination:
                continue
                
            # Penalty logic: Blocked actions add much more weight/risk
            penalty = 5 if action == 'Blocked' else 1
            
            query = """
            MERGE (e:Employee {name: $employee})
            MERGE (g:Group {name: $group})
            MERGE (d:Destination {name: $destination})
            MERGE (e)-[:BELONGS_TO]->(g)
            MERGE (e)-[r:TRANSFERRED_TO]->(d)
            ON CREATE SET 
                r.weight = $penalty, 
                r.channel = $channel, 
                r.severity = $severity, 
                r.action = $action,
                r.last_updated = datetime()
            ON MATCH SET 
                r.weight = r.weight + $penalty,
                r.last_updated = datetime()
            """
            session.run(query, 
                        employee=employee, 
                        group=group, 
                        destination=destination, 
                        channel=channel, 
                        severity=severity, 
                        action=action, 
                        penalty=penalty)
            processed += 1
            
    return processed
