// Influential nodes
// Find important accounts that have received the most dollars.
MATCH (a0:Account)-[t:Transfer]->(a:Account)
WITH a, SUM(t.amount) AS total_amount
ORDER BY total_amount DESC
LIMIT 3
MATCH (a)<-[o:Owns]-(p:Person)
RETURN p.name AS person, a.account_id AS accountID, p.email AS email, total_amount;