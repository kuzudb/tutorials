use kuzu::{Connection, Database, Error, SystemConfig};
use std::fs;

fn main() -> Result<(), Error> {
    // Create an empty database and connect to it
    let path = "db";
    if fs::metadata(path).is_ok() {
        fs::remove_dir_all(path).expect("Could not remove directory");
    }
    let db = Database::new(path, SystemConfig::default())?;
    let conn = Connection::new(&db)?;

    // Create schema
    conn.query("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY (name))")?;
    conn.query("CREATE NODE TABLE City(name STRING, population INT64, PRIMARY KEY (name))")?;
    conn.query("CREATE REL TABLE Follows(FROM Person TO Person)")?;
    conn.query("CREATE REL TABLE LivesIn(FROM Person TO City)")?;

    // Insert data
    conn.query("COPY Person FROM '../data/person.csv'")?;
    conn.query("COPY City FROM '../data/city.csv'")?;
    conn.query("COPY Follows FROM '../data/follows.csv'")?;
    conn.query("COPY LivesIn FROM '../data/lives_in.csv'")?;

    // Run query 1
    let mut query1 = conn.prepare(
        "
            MATCH (c:City)
            WHERE c.population > $min_population
            RETURN c.name AS city, c.population AS population
            ORDER BY population DESC
            ",
    )?;
    let query_result = conn.execute(
        &mut query1,
        vec![("min_population", 1_000_000.into())]
    )?;
    for r in query_result {
        println!("{} has a population of {}", r[0], r[1]);
    }

    // Run query 2
    let query_result = conn.query(
        "
            MATCH (:Person)-[f:Follows]->(p2:Person)
            RETURN p2.name AS person, count(f) AS num_followers
            ORDER BY num_followers DESC LIMIT 1
            ",
    )?;
    for r in query_result {
        println!("{} has the most followers: {}", r[0], r[1]);
    }

    Ok(())
}
