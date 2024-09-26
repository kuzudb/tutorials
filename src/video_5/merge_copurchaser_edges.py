"""
This script adds copurchaser edges to the graph, based on whether two people have purchased the same product.
"""
import kuzu

# Open existing Kùzu database
db = kuzu.Database("./ex_db_kuzu")
conn = kuzu.Connection(db)

# Create relationship table for copurchasers
conn.execute("CREATE REL TABLE IF NOT EXISTS COPURCHASED(FROM Customer TO Customer);")

# Add copurchaser edges to the graph
conn.execute(
    """
    MATCH (c1:Customer)-[:PURCHASED]->(:Product)<-[:PURCHASED]-(c2:Customer)
    WHERE id(c1) < id(c2)
    MERGE (c1)-[:COPURCHASED]->(c2);
    """
)
print("Merged copurchaser edges into the graph!")
