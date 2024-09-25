import kuzu
import shutil

shutil.rmtree("./ex_db_kuzu", ignore_errors=True)
db = kuzu.Database("./ex_db_kuzu")
conn = kuzu.Connection(db)

# Install Postgres extension for Kùzu to be able to scan/copy from Postgres tables
conn.execute("INSTALL postgres; LOAD EXTENSION postgres;")

# Attach the Postgres database
PG_CONNECTION_STRING = (
    "dbname=postgres user=postgres host=localhost password=testpassword port=5432"
)
conn.execute(
    f"""
    ATTACH '{PG_CONNECTION_STRING}' AS pg_db (
        dbtype postgres,
        skip_unsupported_table=false
    )
    """
)

# Create node tables
conn.execute("CREATE NODE TABLE IF NOT EXISTS Customer(name STRING, city STRING, PRIMARY KEY (name));")
conn.execute(
    "CREATE NODE TABLE IF NOT EXISTS Product(name STRING, price DOUBLE, PRIMARY KEY (name));"
)

# Create relationship table
conn.execute("CREATE REL TABLE IF NOT EXISTS PURCHASED(FROM Customer TO Product, quantity INT32);")

# --- Nodes --- #
# Copy from customer table in Postgres to Customer node table in Kùzu
conn.execute("COPY Customer FROM (LOAD FROM pg_db.customer RETURN name, city);")
# Copy from product.parquet to Product node table in Kùzu
conn.execute("COPY Product FROM 'data/product.parquet';")
print("Finished copying nodes to Kùzu!")

# --- Relationships --- #
# Copy from purchased table in Postgres to PURCHASED relationship table in Kùzu
conn.execute("COPY PURCHASED FROM (LOAD FROM pg_db.purchased RETURN customer, product, quantity);")
print("Finished copying rels to Kùzu!")

# Query the database in Cypher: How many products has each person purchased?
response = conn.execute(
    """
    MATCH (p:Customer)-[r:PURCHASED]->(pr:Product)
    RETURN p.name AS customer, SUM(r.quantity) AS num_products_purchased
    ORDER BY num_products_purchased DESC
    LIMIT 5;
    """
)
while response.has_next():
    print(response.get_next())