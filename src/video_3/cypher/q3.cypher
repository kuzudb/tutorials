// Recursive queries and flexible join sequences
// Find the shortest connection of type `Transfer` between the accounts owned by George and Edward.
MATCH (p1:Person)-[o1:Owns]->(a1:Account)-[t:Transfer* SHORTEST]-(a2:Account)<-[o2:Owns]-(p2:Person) 
WHERE p1.name = 'George' AND p2.name = 'Edward'
RETURN *, size(rels(t)) AS depth;