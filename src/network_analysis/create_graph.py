from pathlib import Path
import kuzu

db_path = "example.kuzu"

Path(db_path).unlink(missing_ok=True)
db = kuzu.Database(db_path)
conn = kuzu.Connection(db)

# Node table schema
conn.execute(
    """
    CREATE NODE TABLE Scholar(
        name STRING PRIMARY KEY,
        prize STRING,
        year INT64,
        is_laureate BOOLEAN DEFAULT false
    )
    """
)
# Relationship table schema
conn.execute("CREATE REL TABLE MENTORED(FROM Scholar TO Scholar)")

res = conn.execute(
    """
    LOAD FROM './data/scholars.csv' (header=true)
    MERGE (s:Scholar {name: name})
    SET s.prize = category, s.year = year, s.is_laureate = is_laureate
    RETURN COUNT(s) AS num_scholars
    """
)
print(f"Merged {res.get_as_pl()['num_scholars'][0]} scholar nodes into the database")

res = conn.execute(
    """
    LOAD FROM './data/mentorships.csv' (header=true)
    MATCH (s1:Scholar {name: mentor}), (s2:Scholar {name: mentee})
    MERGE (s1)-[:MENTORED]->(s2)
    RETURN COUNT(*) AS num_mentorships
    """
)
print(f"Merged {res.get_as_pl()['num_mentorships'][0]} mentorship relationships into the database")
