"""
This script performs network analysis on the Nobel Prize laureate graph database.
It calculates and updates the PageRank and Betweenness Centrality metrics for the scholars.
"""

import kuzu
import networkx as nx
import polars as pl


def get_connection(db_path: str) -> kuzu.Connection:
    db = kuzu.Database(db_path)
    return kuzu.Connection(db)


def add_column(conn: kuzu.Connection, table_name: str, column_name: str, column_type: str) -> None:
    try:
        conn.execute(f"ALTER TABLE {table_name} ADD {column_name} {column_type}")
    except RuntimeError:
        pass


def get_mentorship_graph(conn: kuzu.Connection, is_directed: bool = False) -> nx.Graph:
    res = conn.execute(
        """
        MATCH (a:Scholar)-[b:MENTORED]->(c:Scholar)
        WHERE c.type = "laureate"
        RETURN *
        """
    )
    return res.get_as_networkx(directed=is_directed)


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


if __name__ == "__main__":
    conn = get_connection("ex_db_kuzu")

    # Add necessary columns
    add_column(conn, "Scholar", "pagerank", "DOUBLE DEFAULT 0.0")
    add_column(conn, "Scholar", "betweenness_centrality", "DOUBLE DEFAULT 0.0")

    res = conn.execute("MATCH (s:Scholar {name: 'Marie Sklodowska Curie'}) RETURN s.*")
    df = res.get_as_pl()

    # Get graph
    G = get_mentorship_graph(conn, is_directed=True)

    # Calculate and update PageRank
    pagerank_df = calculate_metric(G, nx.pagerank)
    print("Finished calculating PageRank")
    update_database(conn, pagerank_df, "pagerank")

    # Calculate and update Betweenness Centrality
    bc_df = calculate_metric(G, nx.betweenness_centrality)
    print("Finished calculating Betweenness Centrality")
    update_database(conn, bc_df, "betweenness_centrality")
