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
    WHERE node.prize = "Physics"
    RETURN node.name, rank AS pagerank
    ORDER BY pagerank DESC LIMIT 5
    """
)
print(res.get_as_pl())