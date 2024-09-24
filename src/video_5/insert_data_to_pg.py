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
        await conn.execute("TRUNCATE TABLE person, product, purchased;")


async def create_person_table(pool: Pool):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS person (
                name VARCHAR(50),
                age INT
            )
            """
        )


async def create_account_table(pool: Pool):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product (
                product VARCHAR(50),
                price DOUBLE PRECISION
            )
            """
        )


async def create_transfer_table(pool: Pool):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS purchased (
                person VARCHAR(50),
                product VARCHAR(50),
                quantity INT
            )
            """
        )


async def insert_person_record(pool: Pool, record: Record):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO person (name, age)
            VALUES ($1, $2);
            """,
            record["name"],
            int(record["age"]),
        )


async def insert_product_record(pool: Pool, record: Record):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO product (product, price)
            VALUES ($1, $2);
            """,
            record["product"],
            float(record["price"]),
        )


async def insert_transfer_record(pool: Pool, record: Record):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO purchased (person, product, quantity)
            VALUES ($1, $2, $3);
            """,
            record["name"],
            record["product"],
            int(record["quantity"]),
        )


async def main():
    person_records = import_csv("data/csv/person.csv")
    product_records = import_csv("data/csv/product.csv")
    purchase_records = import_csv("data/csv/purchased.csv")

    async with asyncpg.create_pool(PG_URI, min_size=5, max_size=20) as pool:
        # Create tables asynchronously using a connection pool
        await create_person_table(pool)
        await create_account_table(pool)
        await create_transfer_table(pool)
        # Truncate tables before inserting data
        await truncate_tables(pool)
        # Insert records asynchronously
        await asyncio.gather(*[insert_person_record(pool, record) for record in person_records])
        print(f"Inserted {len(person_records)} person records")

        await asyncio.gather(*[insert_product_record(pool, record) for record in product_records])
        print(f"Inserted {len(product_records)} product records")

        await asyncio.gather(*[insert_transfer_record(pool, record) for record in purchase_records])
        print(f"Inserted {len(purchase_records)} purchase records")


if __name__ == "__main__":
    asyncio.run(main())
