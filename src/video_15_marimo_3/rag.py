import marimo

__generated_with = "0.15.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Graph + Vector RAG in Kuzu

    Let's look at an example of combining graph and vector retrievals to build a hybrid RAG system with tool calling. Kuzu provides a native HNSW vector index that you can use for vector retrievals, alongside fast graph traversals.

    In this notebook, we'll showcase how you can build a custom tool-calling module in DSPy that can pick between one of two tools: a vector search tool and a graph query tool. The vector embeddings are on the "motivation" property of the `Prize` node in the existing graph.

    > Powered by Kuzu, DSPy and marimo
    """
    )
    return


@app.cell
def _(mo):
    text_ui = mo.ui.text(value="When and where was Albert Einstein born?", full_width=True)
    return (text_ui,)


@app.cell
def _(text_ui):
    text_ui
    return


@app.cell
def _(mo, rag, text_ui):
    with mo.status.spinner(title="Generating answer...") as _spinner:
        result = rag(text_ui.value)

    question = result['question']
    query = ""
    if result.get('query'):
        query = result['query']
    answer = result['answer']
    return answer, query, result


@app.cell
def _(answer, mo, query, result):
    if not query:
        display_field = mo.md(f"""#### Answer\n{answer}""")
    else:
        display_field = mo.hstack([mo.md(f"""#### Query\n```{query}```"""), mo.md(f"""#### Answer\n{answer}""")])

    mo.vstack([
        mo.md(f"""#### Tool used: {result['tool_used']}"""),
        display_field,
    ])
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Connect to Kuzu database
    The workflow starts with us defining the Kuzu database connection and the DSPy language model settings as follows.
    """
    )
    return


@app.cell
def _(BAMLAdapter, OPENROUTER_API_KEY, dspy, kuzu):
    db_name = "nobel.kuzu"
    db = kuzu.Database(db_name)
    conn = kuzu.Connection(db)
    conn.execute("INSTALL vector; LOAD vector;")

    # Using OpenRouter. Switch to another LLM provider as needed
    lm = dspy.LM(
        model="openrouter/openai/gpt-4.1-mini",
        api_base="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    dspy.configure(lm=lm, adapter=BAMLAdapter())
    return (conn,)


@app.cell
def _(mo):
    mo.md(
        r"""
    Next, we define the necessary DSPy signatures for Graph RAG. These will be used to run the Text2Cypher pipeline that retrieve from the K
    Kuzu database.
    """
    )
    return


@app.cell
def _(GraphSchema, Query, dspy):
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


    class AnswerQuestion(dspy.Signature):
        """
        - Use the provided question, the generated Cypher query and the context to answer the question.
        - If the context is empty, state that you don't have enough information to answer the question.
        """

        question: str = dspy.InputField()
        cypher_query: str = dspy.InputField()
        context: str = dspy.InputField()
        response: str = dspy.OutputField()
    return AnswerQuestion, PruneSchema, Text2Cypher


@app.cell
def _(kuzu):
    def get_schema_dict(conn: kuzu.Connection) -> dict[str, list[dict]]:
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


@app.cell
def _(mo):
    mo.md(r"""## Graph RAG class""")
    return


@app.cell
def _(AnswerQuestion, Any, PruneSchema, Query, Text2Cypher, conn, dspy):
    class GraphRAG(dspy.Module):
        """
        DSPy custom module that applies Text2Cypher to generate a query and run it
        on the Kuzu database, to generate a natural language response.
        """

        def __init__(self):
            self.prune = dspy.Predict(PruneSchema)
            self.text2cypher = dspy.ChainOfThought(Text2Cypher)
            self.generate_answer = dspy.Predict(AnswerQuestion)

        def get_cypher_query(self, question: str, input_schema: str) -> Query:
            prune_result = self.prune(question=question, input_schema=input_schema)
            schema = prune_result.pruned_schema
            text2cypher_result = self.text2cypher(question=question, input_schema=schema)
            cypher_query = text2cypher_result.query
            return cypher_query

        def run_query(self, question: str, input_schema: str) -> tuple[str, list[Any] | None]:
            """
            Run a query synchronously on the database.
            """
            result = self.get_cypher_query(question=question, input_schema=input_schema)
            query = result.query
            try:
                # Run the query on the database
                result = conn.execute(query)
                results = [item for row in result for item in row]
            except RuntimeError as e:
                print(f"Error running query: {e}")
                results = None
            return query, results

        def forward(self, question: str, input_schema: str):
            """
            Contains the full pipeline logic that we can then use downstream to optimize (if we wish).
            """
            final_query, final_context = self.run_query(question, input_schema)
            if final_context is None:
                print("Empty results obtained from the graph database. Please retry with a different question.")
                return {}
            else:
                answer = self.generate_answer(
                    question=question, cypher_query=final_query, context=str(final_context)
                )
                response = {
                    "question": question,
                    "query": final_query,
                    "answer": answer.response,
                }
                return response
    return (GraphRAG,)


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
        to: Node = Field(description="Target node label")
        properties: list[Property] | None


    class GraphSchema(BaseModel):
        nodes: list[Node]
        edges: list[Edge]
    return GraphSchema, Query


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Graph RAG function for tool calling
    The Graph RAG function that will be used as a tool call in DSPy is defined below.
    """
    )
    return


@app.cell
def _(GraphRAG, conn, get_schema_dict):
    def run_graph_rag(question: str):
        graph_rag = GraphRAG()
        schema_dict = get_schema_dict(conn)
        response = graph_rag(question, input_schema=schema_dict)
        return response

    q1 = "In which city and country was Enrico Fermi born?"
    run_graph_rag(q1)
    return (run_graph_rag,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Vector RAG

    The next step is to define the query functions that retrieve from the vector index. This uses the same embedding model and retriever that was defined during vector index creation.
    """
    )
    return


@app.cell
def _(conn, ollama, pl):
    def embed_texts(texts: list[str], embed_model: str = "nomic-embed-text") -> list[list[float]]:
        """
        Embed a list of texts using the specified embedding model
        """
        response = ollama.embed(model=embed_model, input=texts)
        return response.embeddings

    def query_vector_index_prizes(query: str, limit: int = 5) -> pl.DataFrame:
        query_vector = embed_texts([query])[0]

        res_vector_query = conn.execute(
            """
            CALL QUERY_VECTOR_INDEX('Prize', 'prize_index', $query_vector, $limit)
            WITH node AS n, distance
            MATCH (n)<-[r:WON]-(q:Scholar)
            RETURN n.prize_id AS prize_id, n.motivation AS motivation, q.id AS scholar_id, q.knownName AS scholar_name
            ORDER BY distance
            LIMIT $limit
            """,
            {"query_vector": query_vector, "limit": limit})
        return res_vector_query.get_as_pl()
    return (query_vector_index_prizes,)


@app.cell
def _(mo):
    mo.md(r"""We can now defined a signature to answer the question based on vector search. This is required because the response from the vector search function that will be used as a tool below depends on this signature.""")
    return


@app.cell
def _(dspy):
    class AnswerQuestionVectorRAG(dspy.Signature):
        """
        You are a helpful assistant that answers questions using the provided context.
        - Use your best judgment to align the question to the terms in the context. Always strive to produce helpful answers.
        - If the context is empty, state that you don't have enough information to answer the question.
        """
        question: str = dspy.InputField()
        context: str = dspy.InputField()
        answer: str = dspy.OutputField()
    return (AnswerQuestionVectorRAG,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Vector RAG function for tool calling
    Similar to the Graph RAG utility, the function that will be used as a tool call for vector similarity-based retreival in DSPy is defined below. It uses a `dspy.Predict` module under the hood.
    """
    )
    return


@app.cell
def _(AnswerQuestionVectorRAG, Any, dspy, query_vector_index_prizes):
    def run_vector_rag(question: str, limit: int = 5) -> dict[str, Any]:
        response = query_vector_index_prizes(question, limit=limit)
        context = str(response.to_dicts())
        answer_question = dspy.Predict(AnswerQuestionVectorRAG)
        rag_response = answer_question(question=question, context=context)
        return {
            "question": question,
            "answer": rag_response.answer,
        }
    return (run_vector_rag,)


@app.cell
def _(run_vector_rag):
    q2 = "Who won prizes related to the discovery of radioactivity?"
    vector_response = run_vector_rag(q2)
    vector_response
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Tool definition

    We can now define our tool calling signature. We simply declare our vector & graph retrieval functions as tools, and reference them in the input field of the signature that is used to pick the appropriate tool.
    """
    )
    return


@app.cell
def _(dspy, run_graph_rag, run_vector_rag):
    # Create tool instances
    tools = {
        "run_vector_rag": dspy.Tool(run_vector_rag),
        "run_graph_rag": dspy.Tool(run_graph_rag)
    }

    class PickTool(dspy.Signature):
        """
        Pick the most appropriate tool to answer the question.
        - If the question is asking about Nobel prizes, pick the vector search tool
        - If the question is asking about anything other than prizes, pick the graph search tool
        """
        question: str = dspy.InputField()
        tools: list[dspy.Tool] = dspy.InputField()
        outputs: dspy.ToolCalls = dspy.OutputField()
    return PickTool, tools


@app.cell
def _(mo):
    mo.md(r"""To test this, we can ask a quick couple of questions. Based on the instruction in the Tool signature's docstring, the vector search tool will be picked if the question is about Nobel prizes. If the question is about anything else than prizes, the Graph RAG tool is picked.""")
    return


@app.cell
def _(PickTool, dspy, tools):
    tool_caller = dspy.Predict(PickTool)

    t1 = tool_caller(
        question="Who won prizes related to the discovery of the electron?", 
        tools=list(tools.values())
    )
    t1
    return (tool_caller,)


@app.cell
def _(tool_caller, tools):
    # Make a prediction
    t2 = tool_caller(
            question="Where was Albert Einstein born?", 
        tools=list(tools.values())
    )
    t2
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Final DSPy program

    The DSPy program that encapsulates the vector + graph retrieval logic via tool calling is defined below. A `dspy.Predict` modules is used to pick the appropriate tool, based on the user's question. Once the tool is returned by this module, it's passes the user's question to appropriate retrieval tool and generates the response. The response can then be used in the front end as required.
    """
    )
    return


@app.cell
def _(PickTool, dspy, tools):
    class RAG(dspy.Module):
        def __init__(self):
            self.tool_caller = dspy.Predict(PickTool)

        def forward(self, question: str):
            tool_chosen = self.tool_caller(
                question=question,
                tools=list(tools.values()),
            )
            result = {}
            for call in tool_chosen.outputs.tool_calls:
                if call.name in tools:
                    result = tools[call.name](**call.args)
                    result = result | {"tool_used": tools[call.name].name}
            return result

    rag = RAG()
    return (rag,)


@app.cell(hide_code=True)
def _(rag):
    t3 = rag("Who won prizes related to the discovery of weak nuclear forces?")
    t3
    return


@app.cell
def _(rag):
    t4 = rag("In which country and city was Enrico Fermi born?")
    t4
    return


@app.cell
def _(rag):
    t5 = rag("Who won prizes related to the discovery of Polonium?")
    t5
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Conclusions
    That's it! In this notebook, we defined a simple tool-calling module that can decide when to query a vector or graph retriever function using DSPy. More elaborate instructions can be provided that help handle a broader variety of questions than this simple example. More error handling fallback methods can also be implemented.

    Using marimo and DSPy in combination with Kuzu's vector and graph traversal abilities, you can test out other ways to do hybrid RAG!
    """
    )
    return


@app.cell
def _():
    import marimo as mo
    import os
    from textwrap import dedent
    from typing import Any

    import dspy
    import kuzu
    import ollama
    import polars as pl
    from dotenv import load_dotenv
    from baml_adapter import BAMLAdapter
    from pydantic import BaseModel, Field

    load_dotenv()

    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    return (
        Any,
        BAMLAdapter,
        BaseModel,
        Field,
        OPENROUTER_API_KEY,
        dspy,
        kuzu,
        mo,
        ollama,
        pl,
    )


if __name__ == "__main__":
    app.run()
