<div align="center">
<p align="center">

<img width="275" alt="Kùzu logo" src="https://kuzudb.com/img/kuzu-logo.png">

**An embedded graph database built for query speed and scalability**

[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/VtX2gw9Rug)
[![Twitter](https://img.shields.io/badge/Twitter-%231DA1F2.svg?style=for-the-badge&logo=Twitter&logoColor=white)](https://twitter.com/kuzudb)
</p>

</div>

# Tutorials

This repo contains sample code to reproduce the material covered in Kùzu's YouTube tutorials.

## Setting up Kùzu

Kùzu is an embedded graph database that runs in-process, so there's no server to set up. Simply install the client library for your language of choice and you're ready to go! A couple of examples are shown below.

### CLI

It's recommended to install Kùzu CLI on macOS via Homebrew using the following command:

```bash
brew install kuzu
```

To install the CLI on Linux or Windows systems, see the specific installation instructions on
[our website](https://kuzudb.com/#download).

### Python

For Python users using Jupyter notebooks or Python scripts, it's recommended to
install Kùzu in a virtual environment via Astral's [`uv` package installer](https://github.com/astral-sh/uv)
as follows:

```bash
uv venv
source .venv/bin/activate
uv pip install kuzu
```

### JavaScript

For Node.js users, install the `kuzu` package via `npm`.

```bash
# Assuming Node.js 19+ is installed
npm install kuzu
```

See the [docs](https://docs.kuzudb.com/client-apis/) for more information on how to interact
with Kùzu using other languages.