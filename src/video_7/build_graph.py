"""
This script builds a Kuzu graph database from Nobel Prize laureate data.
It processes the raw data from the JSON files, creates node tables for each Nobel Prize category,
and inserts scholar data into the `Scholar` node table, labeling nobel laureates as `laureate` and
those who didn't win as `scholar`.
"""

import json
import shutil

import kuzu
import polars as pl


def process_scholar_data(path: str) -> list[dict[str, str | list[str]]]:
    with open(f"{path}/tree.json", "r") as f:
        scholar_mentors = json.load(f)

    with open(f"{path}/scholars.json", "r") as f:
        scholars = json.load(f)

    mentor_relationships = []
    for scholar_pair in scholar_mentors:
        for scholar in scholar_pair["scholars"]:
            for mentor in scholar_pair["mentors"]:
                mentor_relationships.append({"scholar": scholar, "mentor": mentor})

    # Add a `mentors` JSON array to each scholar in the `scholars` JSON array
    for scholar in scholars:
        mentors = []
        for mentor_relationship in mentor_relationships:
            if mentor_relationship["scholar"] == scholar["name"]:
                mentors.append(mentor_relationship["mentor"])
        if mentors:
            scholar["mentors"] = mentors

    return scholars


def create_prize_node_table(category: str, conn: kuzu.Connection) -> None:
    conn.execute(
        f"""
        COPY {category} FROM (
            LOAD FROM df
            WHERE type = "laureate" AND category = $category
            RETURN DISTINCT year, category
        )
    """,
        parameters={"category": category},
    )


def create_schema(conn: kuzu.Connection) -> None:
    conn.execute("CREATE NODE TABLE Scholar(name STRING, type STRING, PRIMARY KEY (name))")
    conn.execute("CREATE NODE TABLE Physics(year STRING, category STRING, PRIMARY KEY (year))")
    conn.execute("CREATE NODE TABLE Chemistry(year STRING, category STRING, PRIMARY KEY (year))")
    conn.execute("CREATE NODE TABLE Medicine(year STRING, category STRING, PRIMARY KEY (year))")
    conn.execute("CREATE NODE TABLE Economics(year STRING, category STRING, PRIMARY KEY (year))")
    conn.execute("CREATE REL TABLE MENTORED(FROM Scholar TO Scholar)")
    conn.execute(
        """
        CREATE REL TABLE GROUP WON(
            FROM Scholar TO Physics,
            FROM Scholar TO Chemistry,
            FROM Scholar TO Medicine,
            FROM Scholar TO Economics
        )
        """
    )
    print("Created node and relationship tables")


def create_prize_node_tables(conn: kuzu.Connection) -> None:
    categories = ["Physics", "Chemistry", "Medicine", "Economics"]
    for category in categories:
        create_prize_node_table(category, conn)
        print(f"Created node table for {category} nobel prize")


def insert_scholars(conn: kuzu.Connection, df: pl.DataFrame) -> None:
    conn.execute("""
        LOAD FROM df
        MERGE (s:Scholar {name: name})
        ON CREATE SET s.type = type
    """)
    print("Inserted scholars into the Scholar node table")


def insert_mentored_relationships(conn: kuzu.Connection) -> None:
    conn.execute("""
        COPY MENTORED FROM (
            LOAD FROM df
            WHERE SIZE(mentors) > 0
            WITH name AS scholar, mentors
            UNWIND mentors AS mentor
            RETURN DISTINCT mentor, scholar
        )
    """)
    print("Inserted relationships into the MENTORED relationship table")


def insert_won_relationships(conn: kuzu.Connection) -> None:
    categories = ["Physics", "Chemistry", "Medicine", "Economics"]
    for category in categories:
        conn.execute(f"""
            COPY WON_Scholar_{category} FROM (
                LOAD FROM df
                WHERE type = "laureate" AND category = "{category}"
                RETURN DISTINCT name, year
            )
        """)
        print(f"Inserted data into the WON_Scholar_{category} relationship table group")


def main() -> None:
    # Remove existing database directory if it exists
    shutil.rmtree("ex_db_kuzu", ignore_errors=True)

    # Create a new Kuzu database and establish a connection
    db = kuzu.Database("ex_db_kuzu")
    conn = kuzu.Connection(db)

    ROOT_DIR = "data"
    # Process scholar data from source files
    scholars = process_scholar_data(ROOT_DIR)
    df = pl.DataFrame(scholars)

    # Create the graph schema (nodes and relationships)
    create_schema(conn)

    # Create node tables for each Nobel Prize category
    create_prize_node_tables(conn)

    # Insert scholar data into the Scholar node table
    insert_scholars(conn, df)

    # Insert mentorship relationships between scholars
    insert_mentored_relationships(conn)

    # Insert 'won' relationships between scholars and prizes
    insert_won_relationships(conn)


if __name__ == "__main__":
    main()
