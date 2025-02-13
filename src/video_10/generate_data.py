# import shutil
# import kuzu
import random
import string
from dataclasses import dataclass

import polars as pl
from faker import Faker

fake = Faker()
Faker.seed(37)
random.seed(37)


@dataclass
class Profile:
    person_id: int
    name: str
    age: int
    city: str


@dataclass
class Purchase:
    purchase_id: int
    person_id: int
    product_id: int


def get_data():
    df = pl.read_csv("data/product.csv", separator="\t")
    product_ids = df.select("product_id").to_series().to_list()

    # Cities in US, UK and Canada
    cities = [
        # US
        "New York",
        "Miami",
        "San Francisco",
        # UK
        "London",
        "Manchester",
        "Edinburgh",
        # Canada
        "Toronto",
        "Vancouver",
        "Montreal",
    ]
    return product_ids, cities


def generate_profile(id: int, cities: list[str]) -> Profile:
    first_name = fake.first_name()
    last_letter = random.choice(string.ascii_letters)
    return Profile(
        person_id=id + 1,
        name=f"{first_name} {last_letter.capitalize()}.",
        age=random.randint(18, 55),
        city=random.choice(cities),
    )


def generate_product_purchase(id: int, profiles: list[Profile], product_ids: list[int]) -> Purchase:
    return Purchase(
        purchase_id=id + 1,
        person_id=random.choice(profiles).person_id,
        product_id=random.choice(product_ids),
    )


def get_person_profiles(num_persons: int, cities: list[str]) -> list[Profile]:
    """Generate a list of random person profiles."""
    return [generate_profile(id, cities) for id in range(num_persons)]


def get_product_purchases(
    num_purchases: int, profiles: list[Profile], product_ids: list[int]
) -> list[Purchase]:
    """Generate a list of random product purchases for given profiles."""
    return [generate_product_purchase(id, profiles, product_ids) for id in range(num_purchases)]


def generate_sample_data(num_profiles: int) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Generate sample profiles and purchases data, returning both as DataFrames."""
    product_ids, cities = get_data()
    persons = get_person_profiles(num_profiles, cities)
    purchases = get_product_purchases(num_profiles, persons, product_ids)
    # Add more purchases for specific person IDS that are prolific buyers
    persons_sampled = random.sample(persons, 10)
    # Obtain last person's person_id
    last_person_id = persons[-1].person_id
    for idx, person in enumerate(persons_sampled, last_person_id):
        purchase = Purchase(
            purchase_id=idx + last_person_id + 1,
            person_id=person.person_id,
            product_id=random.choice(product_ids),
        )
        purchases.append(purchase)
    persons_df = pl.from_records(persons)
    purchases_df = pl.from_records(purchases)
    # Remove duplicates across all columns
    purchases_df = purchases_df.unique()
    return persons_df, purchases_df


if __name__ == "__main__":
    persons_df, purchases_df = generate_sample_data(1000)
