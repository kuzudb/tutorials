"""
This script adds recommendation edges to the graph

A product will be recommended to a customer based on two conditions:
(1) The customer copurchased a product with another customer
(2) The product is "popular", that is, it has a high historical sales quantity of > 6000
"""
import kuzu

# Connect to the Kùzu database
db = kuzu.Database("./ex_db_kuzu")
conn = kuzu.Connection(db)

# Get recommendations for each customer
response = conn.execute(
    """
    MATCH (c:Customer)-[:Copurchased]-(c2:Customer)-[:PURCHASED]->(p:Product)
    WHERE NOT EXISTS {MATCH (c)-[:PURCHASED]->(p)}
          AND p.historical_sales > 6000
    RETURN DISTINCT c.name AS customer, p.name AS product
    """
)
recommendations_df = response.get_as_df()
recommendations_df = recommendations_df.sort_values("customer").reset_index(drop=True)
print(f"Recommendations for each customer:\n{recommendations_df.head()}")

# Add a new table `IS_RECOMMENDED` to store the recommendations
conn.execute(
    """
    CREATE REL TABLE IF NOT EXISTS IS_RECOMMENDED (
        FROM Customer TO Product
    )
    """
)

# Load from recommendations_df will return (customer, product) tuples.
# For each tuple, we'll match the customer node c and the product node p
# and then merge the IS_RECOMMENDED relationship between them
conn.execute("""
    LOAD FROM recommendations_df
    MATCH (c:Customer {name: customer}), (p:Product {name: product})
    MERGE (c)-[:IS_RECOMMENDED]->(p)
""")
print("Merged IS_RECOMMENDED edges into the graph!")

# We can obtain recommendations for each customer by running the following query
response = conn.execute(
    """
    MATCH (c:Customer)-[:IS_RECOMMENDED]->(p:Product)
    RETURN c.name AS customer, collect(p.name) AS recommendations
    """
)
recommendations_df = response.get_as_df()
print(f"Recommendations for each customer:\n{recommendations_df.head()}")

# Write the recommendations to a Parquet file
recommendations_df.to_parquet("data/recommendations.parquet")




