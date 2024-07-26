// Matching query patterns
// Find 3 persons who have all transferred money to each other (in at least one direction)
MATCH (p1:Person)-[o1:Owns]-(a1:Account),
      (p2:Person)-[o2:Owns]-(a2:Account),
      (p3:Person)-[o3:Owns]-(a3:Account),
      (a1)-[t1:Transfer]-(a2),
      (a2)-[t2:Transfer]-(a3),
      (a1)-[t3:Transfer]-(a3)
WHERE p1.email < p2.email AND p2.email < p3.email
RETURN DISTINCT *;