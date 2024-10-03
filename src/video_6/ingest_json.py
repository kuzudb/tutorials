import shutil
import kuzu

shutil.rmtree("ex_db_kuzu", ignore_errors=True)
db = kuzu.Database("ex_db_kuzu")
conn = kuzu.Connection(db)

# Install and load the json extension
conn.execute("""
    INSTALL json;
    LOAD EXTENSION json;
""")

# --- 1. Create node and relationship tables ---

conn.execute("""
    CREATE NODE TABLE IF NOT EXISTS Patient(
        p_id STRING,
        name STRING,
        info STRUCT(
            height FLOAT,
            weight FLOAT,
            age UINT8,
            insurance_provider STRUCT(
                type STRING,
                name STRING,
                policy_number STRING
            )[]
        ),
        PRIMARY KEY (p_id)
    )
""")

conn.execute("""
    CREATE NODE TABLE IF NOT EXISTS Condition(
        c_id STRING,
        name STRING,
        description STRING,
        PRIMARY KEY (c_id)
    )
""")

conn.execute("""
    CREATE REL TABLE IF NOT EXISTS HAS_CONDITION(
        FROM Patient TO Condition,
        since UINT16
    )
""")

# --- 2. Ingest data into node and relationship tables ---

conn.execute("COPY Patient FROM 'data/patient.json'")
conn.execute("COPY Condition FROM 'data/condition.json'")
conn.execute("COPY HAS_CONDITION FROM 'data/has_condition.json'")

# --- 3. Output a query result to a JSON file using COPY TO ---

conn.execute("""
    // Write the name, age, condition, and health insurance provider for patients with diabetes to JSON file
    COPY (
        MATCH (p:Patient)-[:HAS_CONDITION]->(c:Condition)
        WHERE c.name = "Diabetes (Type 1)"
        WITH p.name AS name, p.info.age AS age, c.name AS condition, p.info.insurance_provider AS ip
        UNWIND ip AS provider
        WITH name, age, provider, condition
        WHERE provider.type = "health"
        RETURN name, age, condition, provider.name AS health_insurance_provider
    ) TO 'data/patient_conditions.json';
""")

conn.execute("""
    // Write health insurance provider information and patient names for patients with Migraine to JSON file
    COPY (
        MATCH (p:Patient)-[:HAS_CONDITION]->(c:Condition)
        WHERE c.name = "Migraine"
        WITH p.name AS name, p.info.age AS age, c.name AS condition, p.info.insurance_provider AS ip
        UNWIND ip AS provider
        WITH name, age, provider, condition
        WHERE provider.type = "health"
        RETURN name, age, condition, provider
    ) TO 'data/patient_providers.json';
""")







