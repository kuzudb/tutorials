import marimo

__generated_with = "0.14.17"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(
        rf"""
    # Graph RAG using Text2Cypher

    This is a demo app in marimo that allows you to query the Nobel laureate dataset in natural language. A language model takes in the question you enter, translates it to Cypher via a custom Graph RAG pipeline built using DSPy and Kuzu. The response retrieved from the graph database is then used as context to formulate the answer to the question.

    > Powered by Kuzu, DSPy and marimo
    """
    )
    return


@app.cell
def _(mo):
    text_ui = mo.ui.text(value="Which scholars won prizes in Physics and were affiliated with University of Cambridge?", full_width=True)
    return (text_ui,)


@app.cell
def _(text_ui):
    text_ui
    return


@app.cell
def _(KuzuDatabaseManager, mo, run_graph_rag, text_ui):
    db_name = "nobel.kuzu"
    db_manager = KuzuDatabaseManager(db_name)

    question = text_ui.value

    with mo.status.spinner(title="Generating answer...") as _spinner:
        result = run_graph_rag([question], db_manager)[0]

    query = result['query']
    answer = result['answer'].response
    mo.hstack([mo.md(f"### Query\n```\n{query}```"), mo.md(f"### Answer\n{answer}")])
    return


@app.cell
def _():
    import marimo as mo
    from helpers import run_graph_rag, KuzuDatabaseManager
    return KuzuDatabaseManager, mo, run_graph_rag


if __name__ == "__main__":
    app.run()
