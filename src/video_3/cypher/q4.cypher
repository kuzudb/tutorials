// Recursive queries and flexible join sequences
// Find **all** shortest connections of any type between the persons George and Edward.
MATCH (p1:Person)-[r* ALL SHORTEST]-(p2:Person)
WHERE p1.name = 'George' AND p2.name = 'Edward'
RETURN *, size(rels(r)) AS depth
ORDER BY depth;