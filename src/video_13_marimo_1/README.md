# Using Kuzu and Polars in Marimo notebooks

Source code for the YouTube video using Polars and Kuzu in [marimo](https://docs.marimo.io/)
(open source, reactive notebooks for Python).

## Setup

We recommend using the `uv` package manager
to manage dependencies.

```bash
# Uses the local pyproject.toml to add dependencies
uv sync
# Or, add them manually
uv add marimo kuzu polars pyarrow
```

## Run the code

marimo simultaneously serves three functions. You can run Python code as a script, a notebook, or as an app!

### Run as a notebook

You can manually activate the local uv virtual environment and run marimo as follows:
```bash
# Activate the virtual environment
source .venv/bin/activate
# Open a marimo notebook in edit mode
marimo edit eda.py
```
Or, you can simply use uv to run marimo:
```bash
uv run marimo edit eda.py
```

### Run as an app

To run marimo in app mode, use the `run` command.

```bash
uv run marimo run eda.py
```

### Run as a script

Each cell block in a marimo notebook is encapsulated into functions, so you can reuse them in other
parts of your codebase. You can also run the marimo file (which is a `*.py` Python file) as you
would any other script:

```bash
uv run eda.py
```
Returns:
```
726 laureate nodes ingested
399 prize nodes ingested
739 laureate prize awards ingested
```

Depending on the stage of your project and who is consuming your code and data, each mode can be
useful in its own right. Have fun using marimo and Kuzu!

