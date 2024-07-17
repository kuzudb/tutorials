MATCH (c:City)
WHERE c.population > 1000000
RETURN c.name AS city, c.population AS population
ORDER BY population DESC