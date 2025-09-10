# Hybrid (graph + vector) RAG and tool-calling with DSPy

Source code for the YouTube video building a hybrid graph + vector RAG pipeline with tool-calling
using Kuzu, [DSPy](https://dspy.ai/) and [marimo](https://docs.marimo.io/) (open source, reactive notebooks for Python).

## Setup

We recommend using the `uv` package manager to manage dependencies.

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
uv run create_nobel_api_graph.py.py
```

Alternatively, you can open the script as a marimo notebook and run each cell individually to
go through the entire workflow step by step.

```bash
uv run marimo run create_nobel_api_graph.py
```

The above script builds a graph of Nobel laureates and their mentorship, as we well as a host of
other relationships. In addition, it also creates a vector index of the Nobel prize motivations
that can be queried using Kuzu's native [vector index extension](https://docs.kuzudb.com/extensions/vector/).

### Run the RAG app

The tool-calling hybrid RAG app works as follows:
1. The user asks a question
2. Depending on the nature of the question, an LLM makes a decision on whether to route the query to
to a vector search tool or a graph query tool
    - If the question is about Nobel prizes and the scholars who won them, it is routed to the vector search tool
    - If the question is about mentorship relationships, it is routed to the graph query tool
3. The relevant tool is called and the results are returned to the user

Each of these steps is built using a custom DSPy module, and the workflow is interactively built and
tested end-to-end in a marimo notebook.

To run the tool-calling RAG application in notebook mode, open the following marimo file:

```bash
uv run marimo run rag.py
```

To run in app mode, use the following command:

```bash
uv run marimo edit rag.py
```

Have fun iterating on the notebook and extending the app!
