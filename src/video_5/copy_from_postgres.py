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
conn.execute("CREATE NODE TABLE IF NOT EXISTS Person(name STRING, age INT32, PRIMARY KEY (name));")
conn.execute(
    "CREATE NODE TABLE IF NOT EXISTS Product(name STRING, price DOUBLE, PRIMARY KEY (name));"
)

# Create relationship table
conn.execute("CREATE REL TABLE IF NOT EXISTS Purchased(FROM Person TO Product, quantity INT32);")

# Copy Postgres tables to Kùzu
conn.execute("COPY Person FROM (LOAD FROM pg_db.person RETURN name, age);")
conn.execute("COPY Product FROM (LOAD FROM pg_db.product RETURN product, price);")
conn.execute(
    "COPY Purchased FROM (LOAD FROM pg_db.purchased RETURN person, product, quantity);"
)
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
