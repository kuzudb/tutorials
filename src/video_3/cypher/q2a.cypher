// Recursive query
// Find all direct and indirect paths, up to length 5
// between the accounts owned by George and Edward
MATCH (p1:Person)-[o1:Owns]->(a1:Account)-[t:Transfer* 1..5]-(a2:Account)<-[o2:Owns]-(p2:Person)
WHERE p1.name = "George" AND p2.name = "Edward"
RETURN t, size(rels(t)) AS depth
ORDER BY depth;