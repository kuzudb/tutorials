// Flexible join sequences
// Find all possible paths in an undirected manner between George and Edward with a maximum length of 5
MATCH (p1:Person)-[r*1..5]-(p2:Person)
WHERE p1.name = "George" AND p2.name = "Edward"
RETURN *;