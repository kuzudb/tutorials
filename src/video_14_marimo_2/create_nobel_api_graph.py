import marimo

__generated_with = "0.14.17"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Creating knowledge graphs using Kuzu, Polars and Marimo
    Let's begin a graph project in Kuzu and use Polars and Marimo to explore the data and do the ETL!
    """
    )
    return


@app.cell
def _(pl):
    filepath = "../video_13_marimo_1/data/nobel.json"
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
    mo.md(r"""Next, we'll define the schema of our graph, i.e., create the node and relationship tables.""")
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
    conn.execute("CREATE NODE TABLE IF NOT EXISTS City(name STRING PRIMARY KEY, state STRING)")
    conn.execute("CREATE NODE TABLE IF NOT EXISTS Country(name STRING PRIMARY KEY)")
    conn.execute("CREATE NODE TABLE IF NOT EXISTS Continent(name STRING PRIMARY KEY)")
    conn.execute("CREATE NODE TABLE IF NOT EXISTS Institution(name STRING PRIMARY KEY)")
    # Relationships
    conn.execute("CREATE REL TABLE IF NOT EXISTS BORN_IN(FROM Scholar TO City)")
    conn.execute("CREATE REL TABLE IF NOT EXISTS DIED_IN(FROM Scholar TO City)")
    conn.execute("CREATE REL TABLE IF NOT EXISTS IS_CITY_IN(FROM City TO Country)")
    conn.execute("CREATE REL TABLE IF NOT EXISTS IS_LOCATED_IN(FROM Institution TO City)")
    conn.execute("CREATE REL TABLE IF NOT EXISTS AFFILIATED_WITH(FROM Scholar TO Institution)")
    conn.execute("CREATE REL TABLE IF NOT EXISTS WON(FROM Scholar TO Prize, portion STRING)")
    conn.execute("CREATE REL TABLE IF NOT EXISTS IS_COUNTRY_IN(FROM Country TO Continent)")
    return


@app.cell
def _(mo):
    mo.md(r"""Let's now ingest the data for scholars (laureates), prizes and the relationships between them (scholar wins a prize).""")
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
        SET r.portion = portion
        RETURN count(r) AS num_awards
        """,
        parameters={"df": prizes_df},
    )
    num_awards = res3.get_as_pl()["num_awards"][0]
    print(f"{num_awards} laureate prize awards ingested")
    return


@app.cell
def _(conn, df):
    res4 = conn.execute(
        """
        LOAD FROM $df
        WHERE birthPlaceCity IS NOT NULL
        MERGE (c:City {name: birthPlaceCity})
        RETURN count(DISTINCT c) AS num_cities
        """,
        parameters={"df": df},
    )
    num_cities = res4.get_as_pl()["num_cities"][0]
    print(f"{num_cities} city nodes ingested")

    res5 = conn.execute(
        """
        LOAD FROM $df
        WHERE birthPlaceCountryNow IS NOT NULL
        MERGE (co:Country {name: birthPlaceCountryNow})
        RETURN count(DISTINCT co) AS num_countries
        """,
        parameters={"df": df},
    )
    num_countries = res5.get_as_pl()["num_countries"][0]
    print(f"{num_countries} country nodes merged")
    return


@app.cell
def _(conn, df):
    res6 = conn.execute(
        """
        LOAD FROM $df
        UNWIND affiliations as a
        WITH *
        WHERE a.nameNow IS NOT NULL
        MERGE (i:Institution {name: a.nameNow})
        RETURN count(DISTINCT i) AS num_institutions
        """,
        parameters={"df": df},
    )
    num_institutions = res6.get_as_pl()["num_institutions"][0]
    print(f"{num_institutions} institution nodes merged")
    return


@app.cell
def _(conn, df):
    res7 = conn.execute(
        """
        LOAD FROM $df
        UNWIND affiliations as a
        WITH *
        WHERE a.cityNow IS NOT NULL
        WITH DISTINCT a.cityNow AS cityNow
        MERGE (ci:City {name: cityNow})
        RETURN count(DISTINCT ci) AS num_cities
    """,
        parameters={"df": df},
    )
    num_cities_from_affiliations = res7.get_as_pl()["num_cities"][0]
    print(f"{num_cities_from_affiliations} city nodes merged")
    return


@app.cell
def _(conn, df):
    res8 = conn.execute(
        """
        LOAD FROM $df
        UNWIND affiliations as a
        WITH *
        WHERE a.continent IS NOT NULL
        WITH DISTINCT a.continent AS continent
        MERGE (co:Continent {name: continent})
        RETURN count(DISTINCT co) AS num_continents
        """,
        parameters={"df": df},
    )
    num_continents = res8.get_as_pl()["num_continents"][0]
    print(f"{num_continents} continent nodes merged")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Merge relationships for remaining cases
    Now that all the nodes have been merged, we're now ready to merge the relationships to create the full graph.
    """
    )
    return


@app.cell
def _(conn, df):
    res9 = conn.execute(
        """
        LOAD FROM $df
        WHERE birthPlaceCity IS NOT NULL
        MATCH (s:Scholar {id: CAST(id AS INT64)})
        MATCH (c:City {name: birthPlaceCity})
        MERGE (s)-[r:BORN_IN]->(c)
        RETURN count(DISTINCT r) AS num_laureate_place_rels
        """,
        parameters={"df": df},
    )
    num_city_country_rels = res9.get_as_pl()["num_laureate_place_rels"][0]
    print(f"{num_city_country_rels} laureate birthplace relationships ingested")
    return


@app.cell
def _(conn, df):
    res10 = conn.execute(
        """
        LOAD FROM $df
        UNWIND affiliations as a
        WITH *
        WHERE a.nameNow IS NOT NULL
        MATCH (s:Scholar {id: CAST(id AS INT64)})
        MATCH (i:Institution {name: a.nameNow})
        MERGE (s)-[ra:AFFILIATED_WITH]->(i)
        RETURN count(DISTINCT ra) AS num_laureate_affiliation_rels
        """,
        parameters={"df": df},
    )
    num_laureate_affiliation_rels = res10.get_as_pl()["num_laureate_affiliation_rels"][0]
    print(f"{num_laureate_affiliation_rels} laureate-affiliation relationships ingested")
    return


@app.cell
def _(conn, df):
    res11 = conn.execute(
        """
        LOAD FROM $df
        UNWIND affiliations as a
        WITH *
        WHERE a.cityNow IS NOT NULL AND a.nameNow IS NOT NULL
        MATCH (i:Institution {name: a.nameNow})
        MATCH (ci:City {name: a.cityNow})
        MERGE (i)-[r:IS_LOCATED_IN]->(ci)
        RETURN count(DISTINCT r) AS num_city_affiliation_rels
    """,
        parameters={"df": df},
    )
    num_city_affiliation_rels = res11.get_as_pl()["num_city_affiliation_rels"][0]
    print(f"{num_city_affiliation_rels} city-affiliation relationships ingested")
    return


@app.cell
def _(conn, df):
    res12 = conn.execute(
        """
        LOAD FROM $df
        UNWIND affiliations as a
        WITH *
        WHERE a.cityNow IS NOT NULL AND a.countryNow IS NOT NULL
        MATCH (ci:City {name: a.cityNow})
        MATCH (co:Country {name: a.countryNow})
        MERGE (ci)-[r:IS_CITY_IN]->(co)
        RETURN count(DISTINCT r) AS num_city_country_rels
        """,
        parameters={"df": df},
    )
    num_city_country_rels_affiliations = res12.get_as_pl()["num_city_country_rels"][0]
    print(f"{num_city_country_rels_affiliations} city-country relationships ingested")
    return


@app.cell
def _(conn, df):
    res13 = conn.execute(
        """
        LOAD FROM $df
        UNWIND affiliations as a
        WITH *
        WHERE a.countryNow IS NOT NULL AND a.continent IS NOT NULL
        MATCH (co:Country {name: a.countryNow})
        MATCH (con:Continent {name: a.continent})
        MERGE (co)-[rc:IS_COUNTRY_IN]->(con)
        RETURN count(DISTINCT rc) AS num_country_affiliation_rels
        """,
        parameters={"df": df},
    )
    num_country_affiliation_rels = res13.get_as_pl()["num_country_affiliation_rels"][0]
    print(f"{num_country_affiliation_rels} country-continent-affiliation relationships ingested")

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

    res_a = conn.execute(
        """
        MATCH (s:Scholar)-[x:WON]->(p:Prize),
              (s)-[y:AFFILIATED_WITH]->(i:Institution),
              (s)-[z:BORN_IN]->(c:City)
        WHERE s.knownName CONTAINS $name
        RETURN s.knownName AS knownName,
               p.category AS category,
               p.awardYear AS awardYear,
               p.prizeAmount AS prizeAmount,
               p.prizeAmountAdjusted AS prizeAmountAdjusted,
               c.name AS birthPlaceCity,
               i.name AS institutionName
        """,
        parameters={"name": name}
    )
    res_a.get_as_pl()
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
