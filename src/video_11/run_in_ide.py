import shutil

import kuzu
import polars as pl
from yfiles_jupyter_graphs_for_kuzu import KuzuGraphWidget

DB_NAME = "ex_kuzu_db"
shutil.rmtree(DB_NAME, ignore_errors=True)
db = kuzu.Database(DB_NAME)
conn = kuzu.Connection(db)

# --- Nodes ---

# Read in the nodes
nodes_df = pl.read_json("data/nodes.json").drop("position", "selected").unnest("data")

# Create node tables
conn.execute("CREATE NODE TABLE IF NOT EXISTS RedWine(id INT64 PRIMARY KEY, name STRING)")
conn.execute("CREATE NODE TABLE IF NOT EXISTS WhiteWine(id INT64 PRIMARY KEY, name STRING)")
conn.execute(
    """
    CREATE NODE TABLE IF NOT EXISTS Cheese(
        id INT64 PRIMARY KEY,
        name STRING,
        strength INT64,
        quality INT64,
        milk STRING
    )
"""
)

# Copy node data
conn.execute(
    """
    COPY RedWine FROM (
        LOAD FROM nodes_df
        WHERE NodeType = "RedWine"
        RETURN SUID AS id, name
    )
    """
)
conn.execute(
    """
    COPY WhiteWine FROM (
        LOAD FROM nodes_df
        WHERE NodeType = "WhiteWine"
        RETURN SUID AS id, name
    )
    """
)
conn.execute(
    """
    COPY Cheese FROM (
        LOAD FROM nodes_df
        WHERE NodeType = "Cheese"
        RETURN
          SUID AS id, name,
          Strength AS strength,
          Quality AS quality,
          Milk AS milk
    )
    """
)

res = conn.execute(
    """
    MATCH (a) RETURN labels(a) AS node_labels, COUNT(*) AS num_nodes
    """
)
res.get_as_pl()  # type: ignore

# --- Edges ---

# Read in the edges
edges_df = (
    pl.read_json("data/edges.json")
    .drop("selected")
    .unnest("data")
    .select("source", "target")
    .with_columns(pl.col("source").cast(pl.Int64), pl.col("target").cast(pl.Int64))
)

# Create edge tables
conn.execute(
    """
    CREATE REL TABLE IF NOT EXISTS PAIRS_WITH(
        FROM Cheese TO Cheese,
        FROM Cheese TO RedWine,
        FROM Cheese TO WhiteWine
    )
    """
)

# Cheese -> RedWine
conn.execute(
    """
    LOAD FROM edges_df
    MATCH (s1:Cheese {id: source}), (t1:RedWine {id: target})
    MERGE (s1)-[:PAIRS_WITH]->(t1)
    """
)

# Cheese -> WhiteWine
conn.execute(
    """
    LOAD FROM edges_df
    MATCH (s2:Cheese {id: source}), (t2:WhiteWine {id: target})
    MERGE (s2)-[:PAIRS_WITH]->(t2)
    """
)

# Cheese -> Cheese
conn.execute(
    """
    LOAD FROM edges_df
    MATCH (s3:Cheese {id: source}), (t3:Cheese {id: target})
    MERGE (s3)-[:PAIRS_WITH]->(t3)
    """
)

res = conn.execute(
    """
    MATCH ()-[r]->() RETURN labels(r) AS rel_labels, COUNT(*) AS num_edges
    """
)
res.get_as_pl()  # type: ignore

# --- Query using yFiles Jupyter Graphs for Kuzu ---

g = KuzuGraphWidget(conn)

g.add_node_configuration("Cheese", color="yellow")  # type: ignore
g.add_node_configuration("RedWine", color="#800020")  # type: ignore
g.add_node_configuration("WhiteWine", color="white")  # type: ignore

# Cheeses that go with Chianti Classico (Static)
g.show_cypher(
    """
    MATCH (cheese:Cheese)-[r:PAIRS_WITH]->(w:RedWine)
    WHERE w.name = "Chianti Classico"
    RETURN * LIMIT 50;
    """
)

# Are there any paths between Gruyere and Cheshire cheeses? (Interactive)
g.show_cypher(
    """
    MATCH (c1:Cheese)-[r *1..3]-(c2:Cheese)
    WHERE c1.name = "Cheshire" AND c2.name = "Gruyere"
    RETURN DISTINCT * LIMIT 50;
    """
)

# How are Brie cheeses connected to Munster cheeses? (Tree)
g.show_cypher(
    """
    MATCH (c1:Cheese)-[r:PAIRS_WITH *1..4 (_, n | WHERE label(n) = "Cheese") ]-(c2:Cheese)
    WHERE c1.name CONTAINS "Brie" AND c2.name CONTAINS "Munster"
    RETURN DISTINCT * LIMIT 50;
    """
)

# Starting from Gruyere, what wines can we pair with it? (Radial)
g.show_cypher(
    """
    MATCH (c1:Cheese)-[r *1..3]->(x)
    WHERE c1.name = "Gruyere"
    RETURN * LIMIT 50;
    """
)

# What cheeses go with Californian and Tuscan reds? (Circular)
g.show_cypher(
    """
    MATCH (w1:RedWine)<-[r1]-(c:Cheese)-[r2]->(w2:RedWine)
    WHERE w1.name CONTAINS "California" AND w2.name CONTAINS "Tuscan"
    RETURN * LIMIT 50;
    """
)
