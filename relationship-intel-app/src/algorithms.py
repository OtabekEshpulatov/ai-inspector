from .database import db
import networkx as nx
from community import best_partition

def run_clustering():
    if not db.driver:
        print("Neo4j database not connected. Skipping clustering.")
        return

    G = nx.Graph()
    
    with db.driver.session() as session:
        # Fetch all relationships mapping sender -> receiver to compute an aggregate weight graph
        query = """
        MATCH (s:Employee)-[rel:DAILY_ACTIVITY]->(r:Employee)
        RETURN s.id AS sender, r.id AS receiver, SUM(rel.count) AS total_count
        """
        results = session.run(query)
        
        for record in results:
            u, v, w = record["sender"], record["receiver"], record["total_count"]
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
            MATCH (e:Employee {id: $id})
            SET e.cluster_id = $cluster
            """, id=node_id, cluster=cluster_id)
            
    print(f"Clustered {len(partition)} employees into {len(set(partition.values()))} clusters.")
