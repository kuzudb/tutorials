MATCH (p1:Person)-[f:Follows]->(p2:Person)
RETURN p2.name AS person, count(f) AS num_followers
ORDER BY num_followers DESC LIMIT 1;