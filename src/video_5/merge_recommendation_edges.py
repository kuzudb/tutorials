import kuzu

# Connect to the Kùzu database
db = kuzu.Database("./ex_db_kuzu")
conn = kuzu.Connection(db)

# Get recommendations for a customer named Oliver
response = conn.execute(
    """
    MATCH (c:Customer)-[:Copurchased]-(c2:Customer)-[:PURCHASED]->(p:Product)
    WHERE p.historical_sales > 6000
    AND NOT EXISTS {MATCH (c)-[:PURCHASED]->(p)}
    RETURN DISTINCT c.name AS customer, p.name AS product
    """
)
recommendations = response.get_as_df()

recommendations = recommendations.sort_values("customer").reset_index(drop=True)
# Add a new table `is_recommended` to store the recommendations
conn.execute(
    """
    CREATE REL TABLE IF NOT EXISTS IS_RECOMMENDED (
        FROM Customer TO Product
    )
    """
)

# Copy from the recommendations DataFrame to the Kùzu database
conn.execute("""
    LOAD FROM recommendations
    MATCH (c:Customer {name: customer}), (p:Product {name: product})
    MERGE (c)-[:IS_RECOMMENDED]->(p)
""")
print("Merged IS_RECOMMENDED edges into the graph!")
