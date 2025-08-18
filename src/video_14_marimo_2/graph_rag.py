import marimo

__generated_with = "0.14.17"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Graph RAG workflow using Kuzu, DSPy and marimo
    In this notebook, we'll show how to build a Graph RAG workflow that leverages a DSPy pipeline on top of Kuzu. The retrieval workflow uses the following steps:

    1. Get the schema (representing the data model) from the graph database
    2. Prune the schema based on the question asked by the user, in alignment with the schema
    3. Run Text2Cypher, where a LM generates a valid Cypher query
    4. Use the LM-generated Cypher query to retieve results from the Kuzu database
    5. Pass the retrieved results as context to another LM that answers the user's question in natural language
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Walkthrough

    The cells below showcase the methodology and go through the code in more detail.
    First, lets create a Kuzu database connection.
    """
    )
    return


@app.cell
def _(kuzu):
    db_name = "nobel.kuzu"
    db = kuzu.Database(db_name, read_only=True)
    conn = kuzu.Connection(db)
    return (conn,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Get graph schema
    To get the LM to write the correct Cypher query that answers the question, it's important to obtain the schema from the graph. The schema informs the LM what nodes and edges exist, and what properties it can query on to answer the question.
    """
    )
    return


@app.cell
def _(kuzu):
    def get_schema_dict(conn:kuzu.Connection) -> dict[str, list[dict]]:
        response = conn.execute("CALL SHOW_TABLES() WHERE type = 'NODE' RETURN *;")
        nodes = [row[1] for row in response]  # type: ignore
        response = conn.execute("CALL SHOW_TABLES() WHERE type = 'REL' RETURN *;")
        rel_tables = [row[1] for row in response]  # type: ignore
        relationships = []
        for tbl_name in rel_tables:
            response = conn.execute(f"CALL SHOW_CONNECTION('{tbl_name}') RETURN *;")
            for row in response:
                relationships.append({"name": tbl_name, "from": row[0], "to": row[1]})  # type: ignore
        schema = {"nodes": [], "edges": []}

        for node in nodes:
            node_schema = {"label": node, "properties": []}
            node_properties = conn.execute(f"CALL TABLE_INFO('{node}') RETURN *;")
            for row in node_properties:  # type: ignore
                node_schema["properties"].append({"name": row[1], "type": row[2]})  # type: ignore
            schema["nodes"].append(node_schema)

        for rel in relationships:
            edge = {
                "label": rel["name"],
                "from": rel["from"],
                "to": rel["to"],
                "properties": [],
            }
            rel_properties = conn.execute(f"""CALL TABLE_INFO('{rel["name"]}') RETURN *;""")
            for row in rel_properties:  # type: ignore
                edge["properties"].append({"name": row[1], "type": row[2]})  # type: ignore
            schema["edges"].append(edge)
        return schema
    return (get_schema_dict,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Below is a helper function to display the schema so that it's easier to read. A sample of the full graph schema is shown immediately after.""")
    return


@app.function
def display_schema(schema: dict[str, list[dict]]) -> None:
    for item in schema.items():
        for sub_item in item[1]:
            print(sub_item)


@app.cell
def _(conn, get_schema_dict):
    full_schema = get_schema_dict(conn)
    display_schema(full_schema)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""By default, the full schema can be quite verbose and complex, so pruning it can help narrow down the context for the LM to better interpret in a way that aligns with the question.""")
    return


@app.cell
def _(dspy, load_dotenv, os):
    load_dotenv()

    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

    # Using OpenRouter. Switch to another LLM provider as needed
    lm = dspy.LM(
        model="openrouter/google/gemini-2.0-flash-001",
        api_base="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    dspy.configure(lm=lm)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Define data models
    Let's first define Pydantic data models that represent the graph schema and the generated Cypher query in a structured form with type validation.
    """
    )
    return


@app.cell
def _(BaseModel, Field):
    class Query(BaseModel):
        query: str = Field(description="Valid Cypher query with no newlines")

    class Property(BaseModel):
        name: str
        type: str = Field(description="Data type of the property")

    class Node(BaseModel):
        label: str
        properties: list[Property] | None

    class Edge(BaseModel):
        label: str = Field(description="Relationship label")
        from_: Node = Field(alias="from", description="Source node label")
        to: Node = Field(alias="from", description="Target node label")
        properties: list[Property] | None

    class GraphSchema(BaseModel):
        nodes: list[Node]
        edges: list[Edge]
    return GraphSchema, Query


@app.cell
def _(mo):
    mo.md(
        r"""
    ## DSPy Signature for schema pruning
    The following signature describes the logic for pruning schema by conditioning the output on the given question from the user. The output is a much smaller, context-rich schema for the Cypher-generating LM downstream.
    """
    )
    return


@app.cell
def _(GraphSchema, dspy):
    class PruneSchema(dspy.Signature):
        """
        Understand the given labelled property graph schema and the given user question. Your task
        is to return ONLY the subset of the schema (node labels, edge labels and properties) that is
        relevant to the question.
          - The schema is a list of nodes and edges in a property graph.
          - The nodes are the entities in the graph.
          - The edges are the relationships between the nodes.
          - Properties of nodes and edges are their attributes, which helps answer the question.
        """

        question: str = dspy.InputField()
        input_schema: str = dspy.InputField()
        pruned_schema: GraphSchema = dspy.OutputField()
    return (PruneSchema,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Example question
    We can define the following question to demonstrate the sequence of steps.
    """
    )
    return


@app.cell
def _(mo):
    sample_question_ui = mo.ui.text(value="Which scholars won prizes in Physics and were affiliated with University of Cambridge?", full_width=True)
    return (sample_question_ui,)


@app.cell
def _(sample_question_ui):
    sample_question_ui
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Use DSPy's Predict Module
    DSPY's simplest module is `Predict`, which produces a prediction, given a prompt as input. The prompt is auto-generated by DSPy and uses information that we declared in the Signature.
    """
    )
    return


@app.cell
def _(PruneSchema, conn, dspy, get_schema_dict, sample_question_ui):
    # Get input schema
    input_schema = get_schema_dict(conn)
    sample_question = sample_question_ui.value

    # Run Module
    prune = dspy.Predict(PruneSchema)
    r = prune(question=sample_question, input_schema=input_schema)
    pruned_schema = r.pruned_schema.model_dump()

    # Display each item for easier understanding
    display_schema(pruned_schema)
    return pruned_schema, sample_question


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""We can see that the returned schema is much more concise and useful for the question that was asked. Nice!""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## DSPy Signature for Text2Cypher
    The Text2Cypher stage uses the pruned schema from the previous step and a list of domain-specific instructions to generate a valid Cypher query (that as far as possible, respects the schema and correctly retrieves from the graph database).
    """
    )
    return


@app.cell
def _(Query, dspy):
    class Text2Cypher(dspy.Signature):
        """
        Translate the question into a valid Cypher query that respects the graph schema.

        <SYNTAX>
        - When matching on Scholar names, ALWAYS match on the `knownName` property
        - For countries, cities, continents and institutions, you can match on the `name` property
        - Use short, concise alphanumeric strings as names of variable bindings (e.g., `a1`, `r1`, etc.)
        - Always strive to respect the relationship direction (FROM/TO) using the schema information.
        - When comparing string properties, ALWAYS do the following:
          - Lowercase the property values before comparison
          - Use the WHERE clause
          - Use the CONTAINS operator to check for presence of one substring in the other
        - DO NOT use APOC as the database does not support it.
        </SYNTAX>

        <RETURN_RESULTS>
        - If the result is an integer, return it as an integer (not a string).
        - When returning results, return property values rather than the entire node or relationship.
        - Do not attempt to coerce data types to number formats (e.g., integer, float) in your results.
        - NO Cypher keywords should be returned by your query.
        </RETURN_RESULTS>
        """

        question: str = dspy.InputField()
        input_schema: str = dspy.InputField()
        query: Query = dspy.OutputField()
    return (Text2Cypher,)


@app.cell
def _(Text2Cypher, dspy, pruned_schema, sample_question):
    text2cypher = dspy.Predict(Text2Cypher)

    text2cypher_result = text2cypher(question=sample_question, input_schema=pruned_schema)
    cypher_query = text2cypher_result.query.query
    cypher_query
    return (text2cypher,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Run the Cypher query on the database

    Next, we run the Cypher query on the database.

    Depending on the complexity of the question and the LM's knowledge of Cypher, the query may or may not be correct. What constitutes a "correct" query can be thought of in two ways:
    - Syntax: Does the Cypher query even compile and is it valid?
    - Semantics: Does the query actually retrieve the right data, and has it interpreted the direction of the relationship correctly?

    ### Agent workflows can help!
    In the real world, this sort of Text2Cypher workflow would need fallbacks and some degree of query rewriting to be more robust to failure. However, for this demo, we can see that for even some non-trivial questions, the queries returned are really good in many cases.
    """
    )
    return


@app.cell
def _(kuzu, text2cypher):
    def run_query(conn: kuzu.Connection, question: str, input_schema: str):
        """
        Run a Cypher query on the Kuzu database and gather the results.
        """
        text2cypher_result = text2cypher(question=question, input_schema=input_schema)
        query = text2cypher_result.query.query
        print(query)
        try:
            # Run the query on the database
            result = conn.execute(query)
            results = [item for row in result for item in row]
        except RuntimeError as e:
            print(f"Error running query: {e}")
            results = None
        return query, results
    return (run_query,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ## DSPy Signature for answer generation
    We now need another DSPy signature for generating an answer in natural langauge from the given result as context.
    """
    )
    return


@app.cell
def _(dspy):
    class AnswerQuestion(dspy.Signature):
        """
        - Use the provided question, the generated Cypher query and the context to answer the question.
        - If the context is empty, state that you don't have enough information to answer the question.
        """

        question: str = dspy.InputField()
        cypher_query: str = dspy.InputField()
        context: str = dspy.InputField()
        response: str = dspy.OutputField()
    return (AnswerQuestion,)


@app.cell
def _(AnswerQuestion, conn, dspy, pruned_schema, run_query, sample_question):
    answer_generator = dspy.ChainOfThought(AnswerQuestion)

    query, context = run_query(conn, sample_question, pruned_schema)
    print(context)
    if context is None:
        print("Empty results obtained from the graph database. Please retry with a different question.")
    else:
        answer = answer_generator(
            question=sample_question, cypher_query=query, context=str(context)
        )
        print(answer)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""The query successfully retrieves data from the Kuzu database, and a `ChainOfThought` module in DSPy is called to reason over this context, to generate an answer in natural language. It's also possible to use a simple `Predict` module to achieve the same outcome. The idea behind this example is that it's quite simple and straightforward to begin ideating and testing your ideas in code, using marimo notebooks in this way.""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Conclusions
    This demo showed how to build a multi-stage AI workflow for Graph RAG using Kuzu and marimo. Give it a try and write your own queries to explore the data further!
    """
    )
    return


@app.cell
def _():
    import os
    import marimo as mo
    import kuzu
    import dspy
    from typing import Any
    from pydantic import BaseModel, Field
    from dotenv import load_dotenv
    return BaseModel, Field, dspy, kuzu, load_dotenv, mo, os


if __name__ == "__main__":
    app.run()
