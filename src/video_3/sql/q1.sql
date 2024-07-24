-- Find all possible direct transfers to the account owned by George
SELECT p2.name AS person, p2.email AS email, t.amount AS amount
FROM Person p1
JOIN Account a1 ON p1.id = a1.owner
JOIN Transfer t ON a1.owner = t.target
JOIN Account a2 ON (t.source = a2.owner)
JOIN Person p2 ON a2.owner = p2.id
WHERE p1.name = 'George';