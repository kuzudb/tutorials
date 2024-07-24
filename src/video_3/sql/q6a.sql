--- Find important accounts that have the highest number of incoming transactions.
WITH IncomingTransfers AS (
    SELECT t.target AS account_id, COUNT(*) AS in_degree
    FROM Transfer t
    GROUP BY t.target
),
TopAccount AS (
    SELECT it.account_id, it.in_degree
    FROM IncomingTransfers it
    ORDER BY it.in_degree DESC
    LIMIT 3
)
SELECT p.name AS person, a.account_id AS accountID, p.email AS email, ta.in_degree
FROM TopAccount ta
JOIN Account a ON ta.account_id = a.id
JOIN Person p ON a.owner = p.id;