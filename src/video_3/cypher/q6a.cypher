// Influential nodes
// Find important accounts that have the highest number of incoming transactions.
MATCH (a0:Account)-[t:Transfer]->(a:Account)
WITH a, COUNT(t) AS in_degree
ORDER BY in_degree DESC
LIMIT 3
MATCH (a)<-[o:Owns]-(p:Person)
RETURN p.name AS person, a.account_id AS accountID, p.email AS email, in_degree;