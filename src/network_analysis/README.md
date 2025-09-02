# Network analysis tutorial

This tutorial demonstrates how to perform network analysis in Kuzu using two methods:
1. **`algo` extension**: Run graph algorithms natively in Kuzu via the [`algo` extension](https://docs.kuzudb.com/extensions/)
2. **NetworkX**: Use the popular [NetworkX](https://networkx.org/documentation/stable/reference/index.html) library in Python to run almost any graph algorithm on a Kuzu subgraph

## Setup

Use uv to manage the dependencies.

```bash
uv sync
```

Install any additional dependencies as needed using the command `uv install <package_name>`.

## Create graph

A dataset of Nobel laureates is provided in the `data` directory. The script `create_graph.py` creates a Kuzu database from the dataset.

```bash
uv run create_graph.py
```
Running this script creates a mentorship graph between scholars who won Nobel prizes, as well
as other scholars who didn't win prizes but were involved in mentoring them. The edges
represent mentor-mentee relationships between the scholars.

## Run graph algorithms using Kuzu's `algo` extension

The first method to run a graph algorithm on the graph involves installing the Kuzu `algo`
extension. Run the script `algo_kuzu.py` to show the results of the top 5 scholars who
won Physics Nobel prizes, ranked by their PageRank scores.

```bash
uv run algo_kuzu.py
```
This prints the following result:
```
┌────────────────────────┬──────────┐
│ node.name              ┆ pagerank │
│ ---                    ┆ ---      │
│ str                    ┆ f64      │
╞════════════════════════╪══════════╡
│ Adam Riess             ┆ 0.00083  │
│ Nicolaas Bloembergen   ┆ 0.000696 │
│ Heike Kamerlingh Onnes ┆ 0.00056  │
│ Claude Cohen-Tannoudji ┆ 0.000456 │
│ Chen-Ning Yang         ┆ 0.000455 │
└────────────────────────┴──────────┘
```

## Run graph algorithms using NetworkX

In case the graph algorithm you're looking to run isn't yet supported by Kuzu's algo extension,
you can use NetworkX. This will be slower than using the `algo` extension in Kuzu due to Python overhead,
but the trade-off is that NetworkX supports a far larger suite of graph algorithms because it's a
mature library that's been maintained for many years, so it's a good option to know about.

```bash
uv run algo_networkx.py
```

A similar result is obtained, with the same top 5 scholars as in the Kuzu example:
```
┌────────────────────────┬────────────┐
│ s.name                 ┆ s.pagerank │
│ ---                    ┆ ---        │
│ str                    ┆ f64        │
╞════════════════════════╪════════════╡
│ Adam Riess             ┆ 0.001657   │
│ Nicolaas Bloembergen   ┆ 0.001402   │
│ Heike Kamerlingh Onnes ┆ 0.001153   │
│ Claude Cohen-Tannoudji ┆ 0.00092    │
│ Chen-Ning Yang         ┆ 0.000913   │
└────────────────────────┴────────────┘
```
