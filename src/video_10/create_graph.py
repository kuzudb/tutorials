import shutil
import time
import kuzu
import polars as pl
from generate_data import generate_sample_data

shutil.rmtree("ex_kuzu_db", ignore_errors=True)
db = kuzu.Database("ex_kuzu_db")
conn = kuzu.Connection(db)

# Load FTS Extension
conn.execute("INSTALL fts; LOAD EXTENSION fts;")

# Create schema
conn.execute(
    "CREATE NODE TABLE IF NOT EXISTS Person(person_id INT64 PRIMARY KEY, name STRING, age INT64);"
)
conn.execute("""
             CREATE NODE TABLE IF NOT EXISTS Product(
                 product_id INT64 PRIMARY KEY, 
                 product_name STRING,
                 product_class STRING,
                 category_hierarchy STRING,
                 product_description STRING,
                 product_features STRING,
                 rating_count DOUBLE,
                 average_rating DOUBLE,
                 review_count DOUBLE
             );
             """)
conn.execute("CREATE NODE TABLE City(city_name STRING PRIMARY KEY);")
conn.execute("CREATE REL TABLE IF NOT EXISTS LIVES_IN(FROM Person TO City);")
conn.execute("CREATE REL TABLE IF NOT EXISTS PURCHASED(FROM Person TO Product, purchase_id INT64);")

# --- Insert data ---
persons_df, purchases_df = generate_sample_data(1000)
products_df = pl.read_csv("data/product.csv", separator="\t").rename({"category hierarchy": "category_hierarchy"})

# Nodes
conn.execute("COPY Person FROM (LOAD FROM persons_df RETURN person_id, name, age);")
conn.execute("COPY Product FROM (LOAD FROM products_df RETURN *);")
conn.execute("COPY City FROM (LOAD FROM persons_df RETURN DISTINCT city);")
# Relationships
conn.execute("COPY LIVES_IN FROM (LOAD FROM persons_df RETURN person_id, city);")
conn.execute(
    """
    COPY PURCHASED FROM (
        LOAD FROM purchases_df
        RETURN
            person_id,
            product_id,
            purchase_id
    );
    """
)

# --- Create FTS index ---
start_time = time.time()
conn.execute(
    """
    CALL CREATE_FTS_INDEX(
        'Product',   // Table name
        'products',  // Index name
        ['product_name', 'product_class', 'product_description']  // Columns to index
    );
"""
)
print(f"Time taken to create FTS index: {time.time() - start_time:.2f} seconds")

indexes = conn.execute("CALL SHOW_INDEXES() RETURN *;").get_as_pl()

# --- Run FTS queries ---

queries = [
    "cotton rug",
    "wooden coffee table",
]

for query in queries:
    ranked_products = conn.execute(
        f"""
        CALL QUERY_FTS_INDEX(
            'Product',
            'products',
            '{query}'
        )
        RETURN
            node.product_id AS id,
            node.product_name AS name,
            node.product_class AS class,
            score
        ORDER BY score DESC LIMIT 5;
    """)
    print(ranked_products.get_as_pl())

    # Use the FTS results to find neighbours
    persons_similar = conn.execute(
        f"""
        CALL QUERY_FTS_INDEX(
            'Product',
            'products',
            '{query}'
        )
        WITH node.product_id AS id, score
        ORDER BY score DESC LIMIT 1000
        MATCH (p:Person)-[:PURCHASED]->(p2:Product {{product_id: id}}),
            (p)-[:LIVES_IN]->(c:City)
        RETURN p.person_id AS person_id, p.name AS name, p.age AS age, c.city_name AS city
        LIMIT 5;
    """)

    print(persons_similar.get_as_pl())