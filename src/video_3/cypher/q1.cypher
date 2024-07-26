// Find all possible direct transfers to the account owned by George
MATCH (p1:Person)-[o1:Owns]->(a1:Account)
       <-[t:Transfer]-(a2:Account)<-[o2:Owns]-(p2:Person)
WHERE p1.name = "Edward"
RETURN p2.name AS person, p2.email AS email, t.amount AS amount;