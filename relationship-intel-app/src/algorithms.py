from .database import db
import networkx as nx
from community import best_partition

def run_clustering():
    if not db.driver:
        print("Neo4j database not connected. Skipping clustering.")
        return

    G = nx.Graph()
    
    with db.driver.session() as session:
        # We cluster employees based on their shared destination interactions.
        # If two employees send data to the same destination, they are linked in the projection.
        query = """
        MATCH (e1:Employee)-[r1:TRANSFERRED_TO]->(d:Destination)<-[r2:TRANSFERRED_TO]-(e2:Employee)
        WHERE e1.name < e2.name
        RETURN e1.name AS e1, e2.name AS e2, SUM(r1.weight + r2.weight) AS shared_risk
        """
        results = session.run(query)
        
        for record in results:
            u, v, w = record["e1"], record["e2"], record["shared_risk"]
            if G.has_edge(u, v):
                G[u][v]["weight"] += w
            else:
                G.add_edge(u, v, weight=w)
                
    if len(G.nodes) == 0:
        return
        
    # Run Louvain
    partition = best_partition(G, weight='weight')
    
    # Write back to Neo4j
    with db.driver.session() as session:
        for node_id, cluster_id in partition.items():
            session.run("""
            MATCH (e:Employee {name: $name})
            SET e.cluster_id = $cluster
            """, name=node_id, cluster=cluster_id)
            
    print(f"Clustered {len(partition)} employees into {len(set(partition.values()))} clusters.")
