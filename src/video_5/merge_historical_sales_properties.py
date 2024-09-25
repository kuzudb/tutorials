"""
This script adds historical sales numbers for each product to the Product table in the Kùzu database.
"""

import kuzu
import pandas as pd

# Read the CSV file of historical sales
df = pd.read_csv("./data/historical_sales.csv")

# Group by product and sum the quantities
historical_sales = (
    df.groupby("product")["quantity"].sum().sort_values(ascending=False).reset_index()
)

# Rename the column for clarity
historical_sales = historical_sales.rename(columns={"quantity": "total_sales"})

# Open existing Kùzu database
db = kuzu.Database("./ex_db_kuzu")
conn = kuzu.Connection(db)

# Alter table to add the `historical_sales` column
try:
    res = conn.execute("ALTER TABLE Product ADD historical_sales INT32;")
    print("Created new column `historical_sales` in Product table")
except RuntimeError:
    # If the column already exists, we don't need to do anything
    pass

conn.execute(
    """
    LOAD FROM historical_sales
    MERGE (p:Product {name: product})
    SET p.historical_sales = total_sales;
    """
)
print("Merged historical sales numbers for each product into Product table")
