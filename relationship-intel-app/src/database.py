from neo4j import GraphDatabase
import redis
import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "testpassword")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

class DB:
    def __init__(self):
        self.driver = None
        self.redis_client = None

    def connect(self):
        try:
            self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
            self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
            print("Connected to Neo4j and Redis.")
        except Exception as e:
            print(f"Warning: Failed to connect to DBs: {e}")

    def close(self):
        if self.driver:
            self.driver.close()
        if self.redis_client:
            self.redis_client.close()

db = DB()
