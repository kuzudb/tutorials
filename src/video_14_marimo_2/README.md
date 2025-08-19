# Graph RAG with Kuzu, DSPy and marimo

Source code for the YouTube video building a Graph RAG with Kuzu, [DSPy](https://dspy.ai/) and [marimo](https://docs.marimo.io/) (open source, reactive notebooks for Python).

## Setup

We recommend using the `uv` package manager
to manage dependencies.

```bash
# Uses the local pyproject.toml to add dependencies
uv sync
# Or, add them manually
uv add marimo dspy kuzu polars pyarrow
```

## Run the code

The Graph RAG pipeline is built on top of a graph of Nobel laureates from the [previous video](../video_13_marimo_1/).

### Create the full graph
Create the required graph in Kuzu using the following script:

```bash
uv run create_graph.py
```

Alternatively, you can open the script as a marimo notebook and run each cell individually to
go through the entire workflow step by step.

```bash
uv run marimo run create_graph.py
```

### Run the Graph RAG pipeline as a notebook

To iterate on your ideas and experiment with your approach, you can work through the Graph RAG
notebook in the following marimo file:

```bash
uv run marimo run demo_workflow.py
```

The purpose of this file is to demonstrate the workflow in distinct stages, making it easier to
understand and modify each part of the process in marimo.

### Run the Graph RAG app

A demo app is provided in `app.py` for reference. It's very basic (just question-answering), but the
idea is general and this can be extended to include advanced retrieval workflows (vector + graph),
interactive graph visualizations via anywidget, and more. More on this in future tutorials!

```bash
uv run marimo run graph_rag.py
```
