import kuzu
import shutil

shutil.rmtree("./ex_db_kuzu", ignore_errors=True)
db = kuzu.Database("./ex_db_kuzu")
conn = kuzu.Connection(db)

# Install JSON extension for Kùzu to be able to scan/copy from JSON files
conn.execute("INSTALL JSON; LOAD EXTENSION JSON;")

# Create node tables
conn.execute("CREATE NODE TABLE IF NOT EXISTS Person(name STRING, age INT64, PRIMARY KEY (name));")
conn.execute(
    "CREATE NODE TABLE IF NOT EXISTS Product(name STRING, price DOUBLE, PRIMARY KEY (name));"
)

# Create relationship table
conn.execute("CREATE REL TABLE IF NOT EXISTS Purchased(FROM Person TO Product, quantity UINT8);")

# Copy data from node JSON files
conn.execute("COPY Person FROM 'data/json/person.json';")
conn.execute("COPY Product FROM 'data/json/product.json';")

# Copy data from relationship JSON file
conn.execute(
    """
    COPY Purchased FROM (
        LOAD FROM 'data/json/purchased.json'
        RETURN
            person_name AS person,
            product_name AS product,
            quantity AS quantity
    )
    """
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
