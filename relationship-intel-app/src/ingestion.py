from .database import db
from datetime import datetime

def check_idempotency(event_id: str) -> bool:
    if not db.redis_client:
        return False
    if db.redis_client.exists(event_id):
        return True
    
    # Set with 30 day expiration (2592000 seconds)
    db.redis_client.set(event_id, "1", ex=2592000)
    return False

def ingest_events(events: list):
    processed = 0
    skipped = 0

    if not db.driver:
        print("Neo4j database not connected. Skipping DB insertion.")
        return 0

    with db.driver.session() as session:
        for ev in events:
            event_id = ev.get("event_id")
            if check_idempotency(event_id):
                skipped += 1
                continue
            
            sender = ev.get("sender")
            receiver = ev.get("receiver")
            dt_str = ev.get("timestamp")
            
            # Parse datetime: '2026-04-16T09:00:00'
            try:
                dt = datetime.fromisoformat(dt_str)
                date_str = dt.date().isoformat()
                hour = dt.hour
                is_out_of_hours = 1 if (hour < 9 or hour >= 18) else 0
            except:
                continue

            query = """
            MERGE (s:Employee {id: $sender})
            MERGE (r:Employee {id: $receiver})
            MERGE (s)-[rel:DAILY_ACTIVITY {date: $date_str}]->(r)
            ON CREATE SET rel.count = 1, rel.out_of_hours_count = $out_of_hours
            ON MATCH SET rel.count = rel.count + 1, rel.out_of_hours_count = rel.out_of_hours_count + $out_of_hours
            """
            session.run(query, sender=sender, receiver=receiver, date_str=date_str, out_of_hours=is_out_of_hours)
            processed += 1
            
    return processed
