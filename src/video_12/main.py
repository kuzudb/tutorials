import shutil

import kuzu
import polars as pl

DB_NAME = "ex_kuzu_db"
shutil.rmtree(DB_NAME, ignore_errors=True)
db = kuzu.Database(DB_NAME)
conn = kuzu.Connection(db)

# --- Nodes ---

# Read in the nodes
nodes_df = pl.read_json("../video_11/data/nodes.json").drop("position", "selected").unnest("data")

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
    pl.read_json("../video_11/data/edges.json")
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

