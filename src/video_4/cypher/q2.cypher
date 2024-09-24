// Find all direct transfers to the account owned by Edward
MATCH (p1:Person)-[o1:OWNS]->(a1:Account)<-[t:TRANSFER]-(a2:Account)<-[o2:OWNS]-(p2:Person)
WHERE p1.name = "Edward"
RETURN *;