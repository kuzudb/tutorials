import polars as pl


df1 = pl.read_csv("data/csv/person.csv", has_header=True)
print(df1)
df1.write_parquet("data/parquet/person.parquet")

df2 = pl.read_csv("data/csv/product.csv", has_header=True)
df2.write_parquet("data/parquet/product.parquet")

df3 = pl.read_csv("data/csv/purchased.csv", has_header=True)
df3.write_parquet("data/parquet/purchased.parquet")
