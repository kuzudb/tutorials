import kuzu
import shutil
import polars as pl

shutil.rmtree("./ex_db_kuzu", ignore_errors=True)
db = kuzu.Database("./ex_db_kuzu")
conn = kuzu.Connection(db)

# Create node tables
conn.execute("CREATE NODE TABLE IF NOT EXISTS Person(name STRING, age INT64, PRIMARY KEY (name));")
conn.execute(
    "CREATE NODE TABLE IF NOT EXISTS Product(name STRING, price DOUBLE, PRIMARY KEY (name));"
)

# Create relationship table
conn.execute("CREATE REL TABLE IF NOT EXISTS Purchased(FROM Person TO Product, quantity UINT8);")

# Load data from pandas
person_df = pl.read_parquet("data/parquet/person.parquet")
product_df = pl.read_parquet("data/parquet/product.parquet")
purchased_df = pl.read_parquet("data/parquet/purchased.parquet")

# Copy data from pandas
conn.execute("COPY Person FROM person_df;")
conn.execute("COPY Product FROM product_df;")
conn.execute("COPY Purchased FROM purchased_df;")
print("Finished copying data to Kùzu!")

# Query the database in Cypher: How many products has each person purchased?
response = conn.execute(
    """
    MATCH (p:Person)-[r:PURCHASED]->(pr:Product)
    RETURN p.name AS person, SUM(r.quantity) AS num_products_purchased
    ORDER BY num_products_purchased DESC
    """
)
while response.has_next():
    print(response.get_next())
