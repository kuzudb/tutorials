"""
This script performs network analysis on the Nobel Prize laureate graph database.
It calculates and updates the PageRank and Betweenness Centrality metrics for the scholars.
"""

import kuzu
import networkx as nx
import polars as pl


def init_database(db_path: str) -> kuzu.Connection:
    db = kuzu.Database(db_path)
    return kuzu.Connection(db)


def add_column(conn: kuzu.Connection, table_name: str, column_name: str, column_type: str) -> None:
    try:
        conn.execute(f"ALTER TABLE {table_name} ADD {column_name} {column_type}")
    except RuntimeError:
        pass


def get_mentorship_graph(conn: kuzu.Connection) -> nx.Graph:
    res = conn.execute(
        """
        MATCH (a:Scholar)-[b:MENTORED]->(c:Scholar)
        WHERE c.type = "laureate"
        RETURN *
        """
    )
    return res.get_as_networkx(directed=False)


def calculate_metric(G: nx.Graph, metric_fn: callable) -> pl.DataFrame:
    metric_values = metric_fn(G)
    df = pl.DataFrame({"name": k, "metric": v} for k, v in metric_values.items())
    return df.with_columns(pl.col("name").str.replace("Scholar_", "").alias("name"))


def update_database(conn: kuzu.Connection, df: pl.DataFrame, metric_name: str) -> None:
    conn.execute(
        f"""
        LOAD FROM df
        MERGE (s:Scholar {{name: name}})
        ON MATCH SET s.{metric_name} = metric
        """
    )


def main() -> None:
    conn = init_database("ex_db_kuzu")

    # Add necessary columns
    add_column(conn, "Scholar", "pagerank", "DOUBLE DEFAULT 0.0")
    add_column(conn, "Scholar", "betweenness_centrality", "DOUBLE DEFAULT 0.0")

    # Get graph
    G = get_mentorship_graph(conn)

    # Calculate and update PageRank
    pagerank_df = calculate_metric(G, nx.pagerank)
    print(pagerank_df.sort("metric", descending=True).head(10))
    update_database(conn, pagerank_df, "pagerank")

    # Calculate and update Betweenness Centrality
    bc_df = calculate_metric(G, nx.betweenness_centrality)
    print(bc_df.sort("metric", descending=True).head(10))
    update_database(conn, bc_df, "betweenness_centrality")


if __name__ == "__main__":
    main()
