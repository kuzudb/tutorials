-- Find important accounts that have received the most dollars.
WITH IncomingTransfers AS (
    SELECT t.target AS account_id, SUM(t.amount) AS total_amount
    FROM Transfer t
    GROUP BY t.target
),
TopAccount AS (
    SELECT it.account_id, it.total_amount
    FROM IncomingTransfers it
    ORDER BY it.total_amount DESC
    LIMIT 3
)
SELECT p.name AS person, a.account_id AS accountID, p.email AS email, ta.total_amount
FROM TopAccount ta
JOIN Account a ON ta.account_id = a.id
JOIN Person p ON a.owner = p.id
ORDER BY ta.total_amount DESC;