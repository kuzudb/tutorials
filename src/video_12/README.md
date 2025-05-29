# Walkthrough of Kuzu's integration with G.V()

Source code for the YouTube video using Kuzu's integration with G.V() for fast, snappy visualizations
of your Kuzu graphs via WebGL. Suitable for visulizing large graphs while rendering thousands of
nodes and edges.

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

Run the code in `main.py` to create the Kuzu database and populate it with data from the wine
and cheese dataset in `video_11/data`. Then, follow the steps shown in the video to query the
graph in G.V().
