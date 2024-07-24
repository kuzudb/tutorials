import shutil
import duckdb

shutil.rmtree("ex_db.duckdb", ignore_errors=True)
conn = duckdb.connect(database="ex_db.duckdb")

# Create tables and insert data
conn.execute(
    """
    CREATE OR REPLACE TABLE Person AS
    SELECT *
    FROM read_csv(
        'data/person.csv',
        header = true,
        delim = ',',
        escape = '"'
    )
    """
)

conn.execute(
    """
    CREATE OR REPLACE TABLE Account AS
    SELECT id, account_id, owner, CAST(balance AS DOUBLE) AS balance
    FROM read_csv(
        'data/account.csv',
        header = true
    )
    """
)

conn.execute(
    """
    CREATE OR REPLACE TABLE Transfer AS
    SELECT source, target, CAST(amount AS DOUBLE) AS amount, transaction_id
    FROM read_csv('data/transfer.csv', header = true)
    """
)
