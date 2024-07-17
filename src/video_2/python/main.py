import shutil

import kuzu


def main() -> None:
    # Initialize database
    shutil.rmtree("./db", ignore_errors=True)
    db = kuzu.Database("./db")
    conn = kuzu.Connection(db)

    # Create schema
    conn.execute("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY (name))")
    conn.execute("CREATE NODE TABLE City(name STRING, population INT64, PRIMARY KEY (name))")
    conn.execute("CREATE REL TABLE Follows(FROM Person TO Person)")
    conn.execute("CREATE REL TABLE LivesIn(FROM Person TO City)")

    # Insert data
    conn.execute("COPY Person FROM '../data/person.csv'")
    conn.execute("COPY City FROM '../data/city.csv'")
    conn.execute("COPY Follows FROM '../data/follows.csv'")
    conn.execute("COPY LivesIn FROM '../data/lives_in.csv'")

    # Run query 1
    response1 = conn.execute(
        """
        MATCH (c:City)
        WHERE c.population > $min_population
        RETURN c.name AS city, c.population AS population
        ORDER BY population DESC
        """,
        parameters={"min_population": 1_000_000},
    )
    while response1.has_next():
        r1 = response1.get_next()
        print(f"{r1[0]} has a population of {r1[1]}")

    # Run query 2
    response2 = conn.execute(
        """
        MATCH (:Person)-[f:Follows]->(p2:Person)
        RETURN p2.name AS person, count(f) AS num_followers
        ORDER BY num_followers DESC LIMIT 1
        """
    )
    r2 = response2.get_next()
    print(f"{r2[0]} has the most followers: {r2[1]}")


if __name__ == "__main__":
    main()
