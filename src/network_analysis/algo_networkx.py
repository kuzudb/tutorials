"""
Use NetworkX to run a graph algorithm on a Kuzu subgraph.
"""
import kuzu
import polars as pl
import networkx as nx

db_path = "example.kuzu"

db = kuzu.Database(db_path)
conn = kuzu.Connection(db)

# Export to NetworkX graph
res = conn.execute(
    """
    MATCH (a:Scholar)-[b:MENTORED]->(c:Scholar)
    RETURN *
    """
)
nx_graph = res.get_as_networkx()

pageranks = nx.pagerank(nx_graph)
# NetworkX prefixes the node label to the results
# This step cleans up the naming so that we can import it back into Kuzu
pagerank_df = (
    pl.DataFrame({"name": k, "metric": v} for k, v in pageranks.items())
    .with_columns(pl.col("name").str.replace("Scholar_", "").alias("name"))
)

# Update Kuzu database with PageRank metric values
# First, add a new column pagerank to the Scholar node table
conn.execute("ALTER TABLE Scholar ADD IF NOT EXISTS pagerank DOUBLE DEFAULT 0.0")

conn.execute(
    """
    LOAD FROM pagerank_df
    MERGE (s:Scholar {name: name})
    SET s.pagerank = metric
    """
)
print("Finished adding graph algorithm metric scores to Kuzu database")

# Query scholars with the highest PageRank scores who won Nobel prizes in Physics 
res = conn.execute(
    """
    MATCH (s:Scholar)
    WHERE s.prize = "Physics"
    RETURN s.name, s.pagerank
    ORDER BY s.pagerank DESC LIMIT 5
    """
)
print(res.get_as_pl())


# Run betweenness centrality
bc_results = nx.betweenness_centrality(nx_graph)
# NetworkX prefixes the node label to the results
# This step cleans up the naming so that we can import it back into Kuzu
betweenness_centrality_df = (
    pl.DataFrame({"name": k, "metric": v} for k, v in bc_results.items())
    .with_columns(pl.col("name").str.replace("Scholar_", "").alias("name"))
)

conn.execute("ALTER TABLE Scholar ADD IF NOT EXISTS betweenness_centrality DOUBLE DEFAULT 0.0")

conn.execute(
    """
    LOAD FROM betweenness_centrality_df
    MERGE (s:Scholar {name: name})
    SET s.betweenness_centrality = metric
    """
)
print("Finished adding graph algorithm metric scores to Kuzu database")

# Query scholars with the highest PageRank scores who won Nobel prizes in Physics 
res = conn.execute(
    """
    MATCH (s:Scholar),
          (a:Scholar)-[:MENTORED]->(s)-[:MENTORED]->(b:Scholar)
    WHERE s.prize = "Physics"
    AND a.is_laureate = true
    AND b.is_laureate = true
    RETURN
      s.name,
      s.betweenness_centrality,
      COUNT(DISTINCT a) AS num_mentors,
      COUNT(DISTINCT b) AS num_mentees
    ORDER BY s.betweenness_centrality DESC LIMIT 5
    """
)
print(res.get_as_pl())
