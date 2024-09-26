import asyncio
import csv
from typing import Any, Dict

import asyncpg
from asyncpg.pool import Pool

Record = Dict[str, Any]
PG_URI = "postgresql://postgres:testpassword@localhost:5432/postgres"


# Import CSV as a list of dictionaries
def import_csv(file_path: str) -> list[Record]:
    with open(file_path) as file:
        reader = csv.DictReader(file)
        return list(reader)


async def truncate_tables(pool: Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE customer, purchased;")


async def create_customer_table(pool: Pool):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS customer (
                name VARCHAR(50),
                city VARCHAR(50)
            )
            """
        )


async def create_purchase_table(pool: Pool):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS purchased (
                customer VARCHAR(50),
                product VARCHAR(50),
                quantity INT
            )
            """
        )


async def insert_customer_record(pool: Pool, record: Record):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO customer (name, city)
            VALUES ($1, $2);
            """,
            record["name"],
            record["city"],
        )


async def insert_purchase_record(pool: Pool, record: Record):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO purchased (customer, product, quantity)
            VALUES ($1, $2, $3);
            """,
            record["customer"],
            record["product"],
            int(record["quantity"]),
        )


async def main():
    customer_records = import_csv("raw/customer.csv")
    purchase_records = import_csv("raw/purchased.csv")

    async with asyncpg.create_pool(PG_URI, min_size=5, max_size=20) as pool:
        # Create tables asynchronously using a connection pool
        await create_customer_table(pool)
        await create_purchase_table(pool)
        # Truncate tables before inserting data
        await truncate_tables(pool)
        # Insert records asynchronously
        await asyncio.gather(*[insert_customer_record(pool, record) for record in customer_records])
        print(f"Inserted {len(customer_records)} customer records")

        await asyncio.gather(*[insert_purchase_record(pool, record) for record in purchase_records])
        print(f"Inserted {len(purchase_records)} purchase records")


if __name__ == "__main__":
    asyncio.run(main())
