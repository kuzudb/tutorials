# Full-text search with Kuzu

Source code for the YouTube video on using Kùzu's full-text search feature.

## Setup

The minimum recommended Python version is 3.10+. We also recommend using the `uv` package manager
to manage dependencies. You can install `uv` using the following commands:

```bash
# On macOS via Homebrew
brew install uv

# On Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

It's also recommended to set up a clean virtual environment before installing any dependencies.

```bash
# Create a virtual environment at .venv
uv venv

# On macOS and Linux
source .venv/bin/activate

# On Windows
.venv\Scripts\activate
```

Once you have the virtual environment set up, you can install the dependencies using
the provided `requirements.txt` file.

```bash
uv pip install -r requirements.txt
```

## Visualization

Graph visualization is a great method to understand the structure and the "connectedness" of your data.
We will be visualizing graphs in Kùzu using its browser-based UI,
[Kùzu Explorer](https://docs.kuzudb.com/visualization/). Docker is required to run Kùzu Explorer.
You can run the latest version of Kùzu Explorer by pulling the image from DockerHub provided using
the provided `docker-compose.yml` file.

Run the following commands in the directory where the `docker-compose.yml` is:

```bash
docker compose up
```

Alternatively, you can type in the following command in your terminal:

```bash
docker run -p 8000:8000 \
           -v ./ex_kuzu_db:/database
           -e MODE=READ_WRITE \
           --rm kuzudb/explorer:latest
```

This will download and run the Kùzu Explorer image, and you can access the UI at `http://localhost:8000`.

Enter the following Cypher query in the shell editor to visualize the graph:

```cypher
MATCH (a)-[b]->(c)
RETURN *
LIMIT 100
```

![](./assets/person_product_graph.png)

## Steps

### Download the data

The dataset used in this example is the [WANDS benchmark](https://github.com/wayfair/WANDS).
Clone the repository and navigate to the `dataset` directory.

```bash
git clone https://github.com/wayfair/WANDS.git
cd WANDS/dataset
```

The file `product.csv` is the dataset of retail products that contain ~42k records of products
and their associated metadata.

### Generate the artificial data

We will be combining the `product.csv` dataset with a dataset of 1000 persons generated on the fly
showing which products they purchased, and where they live.

Test the data generation script as follows:
```bash
python generate_data.py
```

### Create the graph

Create a Kùzu database that uses the products and the generated person data as follows:

```bash
python create_graph.py
```

This will create a Kùzu database in the `ex_kuzu_db` directory, create an FTS index on the required
columns and run a test query that queries the FTS index.

We are now ready to explore the graph!