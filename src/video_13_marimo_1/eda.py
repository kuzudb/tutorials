import marimo

__generated_with = "0.14.17"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Using Kuzu and Polars in Marimo notebooks
    Let's begin a graph project in Kuzu and use Polars and Marimo to explore the data and do the ETL!
    """
    )
    return


@app.cell
def _(pl):
    filepath = "data/nobel.json"
    df = pl.read_json(filepath).explode("prizes").unnest("prizes")
    df
    return df, filepath


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Handle malformed dates
    When exploring the data, it becomes clear that certain dates (formatted as strings) have malformed values. For example the first person in the list has the birthdate `1943-00-00`, which is clearly invalid. Working in a notebook, we can quickly test our ideas and apply them to the initial method.
    """
    )
    return


@app.cell
def _(df, pl):
    laureates_df = df.with_columns(
        pl.col("birthDate").str.replace("-00-00", "-01-01").str.to_date()
    )
    return (laureates_df,)


@app.cell
def _(df):
    df
    return


@app.cell
def _(mo):
    # Create a slider for min/max prize values
    range_slider = mo.ui.range_slider(
        start=100_000,
        stop=50_000_000,
        step=100_000,
        value=(1_000_000, 50_000_000),
    )
    return (range_slider,)


@app.cell
def _(mo, range_slider):
    min_val = range_slider.value[0]
    max_val = range_slider.value[1]
    mo.hstack(
        [
            mo.md(f"Select prize value range: {range_slider}"),
            mo.md(f"min: {min_val} | max: {max_val}"),
        ]
    )
    return


@app.cell
def _():
    return


@app.cell
def _(mo):
    # initialize the date picker at a given date
    max_birth_date = mo.ui.date(value="1945-01-01", full_width=True)
    return (max_birth_date,)


@app.cell
def _(max_birth_date, mo):
    mo.hstack(
        [
            max_birth_date,
            mo.md(
                f"Show only prize winners born before this date: {max_birth_date.value}"
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Let's use the values from the slider bar to filter on the prize values, and the calendar's values to filter on the birth dates of the laureates.""")
    return


@app.cell
def _(laureates_df, max_birth_date, pl, range_slider):
    laureates_df.filter(
        (pl.col("prizeAmount") > range_slider.value[0])
        & (pl.col("prizeAmount") < range_slider.value[1])
        & (pl.col("birthDate") < max_birth_date.value)
    ).select(
        "knownName", "category", "birthDate", "prizeAmount", "prizeAmountAdjusted"
    ).head(10)
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Import data into Kuzu
    We're now ready to begin importing the data as a graph into Kuzu!
    """
    )
    return


@app.cell
def _(Path):
    db_name = "nobel.kuzu"
    Path(db_name).unlink(missing_ok=True)  # Remove the database file if it exists
    Path(db_name + ".wal").unlink(
        missing_ok=True
    )  # Remove the database WAL file if it exists
    return (db_name,)


@app.cell
def _(db_name, kuzu):
    # Connect to the Kuzu database
    db = kuzu.Database(db_name)
    conn = kuzu.Connection(db)
    return (conn,)


@app.cell
def _(mo):
    mo.md(
        r"""Next, we'll define the schema of our graph, i.e., create the node and relationship tables."""
    )
    return


@app.cell
def _(conn):
    conn.execute(
        """
        CREATE NODE TABLE IF NOT EXISTS Scholar(
            id INT64 PRIMARY KEY,
            scholar_type STRING,
            fullName STRING,
            knownName STRING,
            gender STRING,
            birthDate STRING,
            deathDate STRING
        )
        """
    )
    conn.execute(
        """
        CREATE NODE TABLE IF NOT EXISTS Prize(
            prize_id STRING PRIMARY KEY,
            awardYear INT64,
            category STRING,
            dateAwarded STRING,
            motivation STRING,
            prizeAmount INT64,
            prizeAmountAdjusted INT64
        )
    """
    )
    conn.execute(
        "CREATE NODE TABLE IF NOT EXISTS City(name STRING PRIMARY KEY, state STRING)"
    )
    conn.execute(
        "CREATE NODE TABLE IF NOT EXISTS Country(name STRING PRIMARY KEY)"
    )
    conn.execute(
        "CREATE NODE TABLE IF NOT EXISTS Continent(name STRING PRIMARY KEY)"
    )
    conn.execute(
        "CREATE NODE TABLE IF NOT EXISTS Institution(name STRING PRIMARY KEY)"
    )
    # Relationships
    conn.execute(
        "CREATE REL TABLE IF NOT EXISTS WON(FROM Scholar TO Prize, portion STRING)"
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""Let's now ingest the data for scholars (laureates), prizes and the relationships between them (scholar wins a prize)."""
    )
    return


@app.cell
def _(conn, laureates_df):
    res = conn.execute(
        """
        LOAD FROM $df
        WITH DISTINCT CAST(id AS INT64) AS id, knownName, fullName, gender, birthDate, deathDate
        MERGE (s:Scholar {id: id})
        SET s.scholar_type = 'laureate',
            s.fullName = fullName,
            s.knownName = knownName,
            s.gender = gender,
            s.birthDate = birthDate,
            s.deathDate = deathDate
        RETURN count(s) AS num_laureates
        """,
        parameters={"df": laureates_df},
    )
    num_laureates = res.get_as_pl()["num_laureates"][0]
    print(f"{num_laureates} laureate nodes ingested")
    return


@app.cell
def _(filepath, pl):
    prizes_df = (
        pl.read_json(filepath)
        .select("id", "prizes")
        .explode("prizes")
        .with_columns(
            pl.col("prizes")
            .struct.field("category")
            .str.replace("Physiology or Medicine", "Medicine")
            .str.replace("Economic Sciences", "Economics")
            .str.to_lowercase()
        )
    )
    prizes_df = prizes_df.with_columns(
        pl.col("id"),
        pl.concat_str(
            [pl.col("prizes").struct.field("awardYear"), pl.col("category")],
            separator="_",
        ).alias("prize_id"),
        pl.col("prizes").struct.field("portion"),
        pl.col("prizes").struct.field("awardYear").cast(pl.Int64),
        pl.col("prizes").struct.field("dateAwarded").str.to_date("%Y-%m-%d"),
        pl.col("prizes").struct.field("motivation"),
        pl.col("prizes").struct.field("prizeAmount"),
        pl.col("prizes").struct.field("prizeAmountAdjusted"),
    ).drop("prizes")

    prizes_df.head()
    return (prizes_df,)


@app.cell
def _(conn, prizes_df):
    res2 = conn.execute(
        """
        LOAD FROM $df
        MERGE (p:Prize {prize_id: prize_id})
        SET p.awardYear = awardYear,
            p.category = category,
            p.dateAwarded = CAST(dateAwarded AS DATE),
            p.motivation = motivation,
            p.prizeAmount = prizeAmount,
            p.prizeAmountAdjusted = prizeAmountAdjusted
        RETURN count(DISTINCT p) AS num_prizes
    """,
        parameters={"df": prizes_df},
    )
    num_prizes = res2.get_as_pl()["num_prizes"][0]
    print(f"{num_prizes} prize nodes ingested")
    return


@app.cell
def _(conn, prizes_df):
    res3 = conn.execute(
        """
        LOAD FROM $df
        MATCH (s:Scholar {id: CAST(id AS INT64)})
        MATCH (p:Prize {prize_id: prize_id})
        MERGE (s)-[r:WON]->(p)
        RETURN count(r) AS num_awards
        """,
        parameters={"df": prizes_df},
    )
    num_awards = res3.get_as_pl()["num_awards"][0]
    print(f"{num_awards} laureate prize awards ingested")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Run queries
    Once the date is in Kuzu, we can write Cypher queries to identify paths and compute aggregations.
    """
    )
    return


@app.cell
def _(conn):
    name = "Curie"

    res4 = conn.execute(
        """
        MATCH (s:Scholar)-[r:WON]->(p:Prize)
        WHERE s.knownName CONTAINS $name
        RETURN s.*, p.*
        """,
        parameters={"name": name}
    )
    res4.get_as_pl()
    return


@app.cell
def _():
    import marimo as mo
    import kuzu
    import polars as pl
    from pathlib import Path
    from datetime import datetime
    return Path, kuzu, mo, pl


if __name__ == "__main__":
    app.run()
