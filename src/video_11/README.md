# Interactive graph visualization in Jupyter notebooks

Source code for the YouTube video using yFiles Jupyter Graphs' Kuzu integration to visualize your
Kuzu graphs in Jupyter notebooks (or, via ipykernel, in VS Code and Cursor).

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

## Run the code

### Interactively in VS Code or Cursor

Run the code provided in `run_in_ide.py` interactively using `ipykernel` to fire the yFiles Jupyter Graphs
widget in your VS Code or Cursor IDE.

### In a Jupyter notebook

Alternatively, you can run the code provided in `run_in_notebook.py` in Jupyter Lab as follows.

```bash
# Ensure the virtual environment is activated
source .venv/bin/activate

# Run Jupyter Lab
jupyter lab
```

Then, open the `run_in_notebook.ipynb` file in Jupyter Lab and run all the cells.
