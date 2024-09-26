import kuzu
import shutil

shutil.rmtree("./ex_db_kuzu", ignore_errors=True)
db = kuzu.Database("./ex_db_kuzu")
conn = kuzu.Connection(db)

# ---- DDL ---- #

# Create node tables
conn.execute("CREATE NODE TABLE IF NOT EXISTS Customer(name STRING, city STRING, PRIMARY KEY (name));")
conn.execute(
    "CREATE NODE TABLE IF NOT EXISTS Product(name STRING, price DOUBLE, historical_sales INT32, PRIMARY KEY (name));"
)

# Create relationship table
conn.execute("CREATE REL TABLE IF NOT EXISTS PURCHASED(FROM Customer TO Product, quantity INT32);")

# ---- Ingest nodes and relationships ---- #

# ---- STEP 1: Copy from product.parquet to Product node table in Kùzu

# Scan the parquet file to first see what's in it! We output the query results as a pandas dataframe
r = conn.execute("LOAD FROM 'data/product.parquet' RETURN *;")
print(f"Products in parquet file:\n{r.get_as_df().head()}")

# Copy the data from the parquet file to the Product node table
conn.execute("COPY Product(name, price) FROM 'data/product.parquet';")
print("Finished copying product nodes to Kùzu!")

# ---- STEP 2: Copy from Postgres customer table to Customer node table in Kùzu

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

# Copy from customer table in Postgres to Customer node table in Kùzu
conn.execute("COPY Customer FROM (LOAD FROM pg_db.customer RETURN name, city);")
print("Finished copying customer nodes to Kùzu!")

# Step 3: Copy from Postgres customer table to Purchased relationship table in Kùzu
conn.execute("COPY PURCHASED FROM (LOAD FROM pg_db.purchased RETURN customer, product, quantity);")
