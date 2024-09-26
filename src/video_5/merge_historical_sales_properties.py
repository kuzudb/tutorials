"""
This script adds historical sales numbers for each product to the Product table in the Kùzu database.
"""
import kuzu
import pandas as pd

# Read the CSV file of historical sales
df = pd.read_csv("./data/historical_sales.csv")
print(f"Historical sales:\n{df.head(15)}")

# Group by product and sum the quantities
historical_sales_df = (
    df.groupby("product")["quantity"].sum().sort_values(ascending=False).reset_index()
)

# Rename the column for clarity
historical_sales_df = historical_sales_df.rename(columns={"quantity": "historical_sales"})
print(f"Aggregated historical sales:\n{historical_sales_df.head(15)}")

# Open existing Kùzu database
db = kuzu.Database("./ex_db_kuzu")
conn = kuzu.Connection(db)

# Load from historical_sales_df will return (product, historical_sales) tuples.
# For each tuple, we'll match the product node p, such that p.name = product
# and then set the historical_sales value to the historical_sales property of the node.
conn.execute(
    """
    LOAD FROM historical_sales_df
    MATCH (p:Product {name: product})
    SET p.historical_sales = historical_sales;
    """
)
print("Merged historical sales numbers for each product into Product table")
