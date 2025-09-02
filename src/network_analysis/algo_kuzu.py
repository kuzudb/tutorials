"""
Use Kuzu's native graph algo extension to run a graph algorithm on a Kuzu subgraph.
"""
import kuzu
import polars as pl
import networkx as nx

db_path = "example.kuzu"

db = kuzu.Database(db_path)
conn = kuzu.Connection(db)

# Install and load the Kuzu algo extension
conn.execute("INSTALL algo; LOAD algo;")

# Project a subgraph
conn.execute("CALL project_graph('MentorshipGraph', ['Scholar'], ['MENTORED']);")

# Run PageRank on the projected graph
res = conn.execute(
    """
    CALL page_rank('MentorshipGraph')
    RETURN node.name AS name, rank AS pagerank
    """
)
pagerank_df = res.get_as_pl()
# Update Kuzu database with PageRank metric values
# First, add a new column pagerank to the Scholar node table
conn.execute("ALTER TABLE Scholar ADD IF NOT EXISTS pagerank DOUBLE DEFAULT 0.0")

conn.execute(
    """
    LOAD FROM pagerank_df
    MERGE (s:Scholar {name: name})
    SET s.pagerank = pagerank
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