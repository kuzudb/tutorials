import kuzu
import shutil

shutil.rmtree("./ex_db_kuzu", ignore_errors=True)
db = kuzu.Database("./ex_db_kuzu")
conn = kuzu.Connection(db)

# Create node tables
conn.execute(
    """
    CREATE NODE TABLE Person (
        id INT64,
        name STRING,
        state STRING,
        zip INT64,
        email STRING,
        PRIMARY KEY (id)
    )
    """
)

conn.execute(
    """
    CREATE NODE TABLE Address (
        address STRING,
        PRIMARY KEY (address)
    )
    """
)


conn.execute(
    """
    CREATE NODE TABLE Account (
        id INT64,
        account_id STRING,
        balance DOUBLE,
        PRIMARY KEY (id)
    )
    """
)

# Create rel tables
conn.execute("CREATE REL TABLE Owns (FROM Person TO Account)")
conn.execute("CREATE REL TABLE LivesIn (FROM Person TO Address)")
conn.execute(
    "CREATE REL TABLE Transfer (FROM Account TO Account, amount DOUBLE, transaction_id STRING)"
)

# --- NODES ---
conn.execute("""
    COPY Person FROM
        (
            LOAD FROM 'data/person.csv' (
                header = true,
                delim = ",",
                escape = '"'
            )
            RETURN CAST(id, "INT64"), name, state, CAST(zipcode, "INT64"), email
        )
    """)

conn.execute(
    """
    COPY Account FROM
        (
            LOAD FROM 'data/account.csv' (header = true)
            RETURN CAST(id, "INT64"), account_id, CAST(balance, "DOUBLE")
        )
    """
)

conn.execute(
    """
    COPY Address FROM
        (
            LOAD FROM 'data/person.csv' (
                header = true,
                delim = ",",
                escape = '"'
            )
            RETURN DISTINCT address
        )
    """
)

# --- RELS ---

conn.execute(
    """
    COPY Owns FROM
        (
            LOAD FROM 'data/account.csv' (
                header = true,
                delim = ",",
                escape = '"'
            )
            RETURN CAST(owner, "INT64"), CAST(id, "INT64")
        )
    """
)

conn.execute(
    """
    COPY LivesIn FROM
        (
            LOAD FROM 'data/person.csv' (
                header = true,
                delim = ",",
                escape = '"'
            )
            RETURN CAST(id, "INT64"), address
        )
    """
)

conn.execute(
    """
    COPY Transfer FROM (
        LOAD FROM 'data/transfer.csv' (header = true)
        RETURN CAST(source, "INT64"), CAST(target, "INT64"), CAST(amount, "DOUBLE"), transaction_id
    )
    """
)
