import os
import shutil

import kuzu
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_kuzu.graphs.kuzu_graph import KuzuGraph
from langchain_kuzu.chains.graph_qa.kuzu import KuzuQAChain
from langchain_openai import ChatOpenAI


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
assert OPENAI_API_KEY is not None, "OPENAI_API_KEY is not set"
SEED = 37

# --- Stage 1: Create the graph ---

shutil.rmtree("ex_kuzu_db", ignore_errors=True)
db = kuzu.Database("ex_kuzu_db")

# Define the LLMs
extraction_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, seed=SEED, api_key=OPENAI_API_KEY)
generation_llm = ChatOpenAI(model="gpt-4", temperature=0.3, seed=SEED, api_key=OPENAI_API_KEY)

# Load the dataset on Marie Curie
with open("./data/curie.txt", "r") as f:
    text = f.read()
assert text is not None, "Empty text, please check the file and try again."

# Define schema
allowed_nodes = ["Person", "NobelPrize", "Discovery"]
allowed_relationships = [
    ("Person", "IS_MARRIED_TO", "Person"),
    ("Person", "WORKED_WITH", "Person"),
    ("Person", "WON", "NobelPrize"),
    ("Person", "DISCOVERED", "Discovery"),
]

# Define the LLMGraphTransformer to extract the graph
llm_transformer = LLMGraphTransformer(
    llm=extraction_llm,
    allowed_nodes=allowed_nodes,
    allowed_relationships=allowed_relationships,
)

# Convert the given text into graph documents
documents = [Document(page_content=text)]
graph_documents = llm_transformer.convert_to_graph_documents(documents)

# Create a graph object
graph = KuzuGraph(db, allow_dangerous_requests=True)

# Add the graph document to the graph
graph.add_graph_documents(
    graph_documents,
    include_source=True,
)

# Create the KuzuQAChain with verbosity enabled to see the generated Cypher queries
chain = KuzuQAChain.from_llm(
    llm=generation_llm,
    graph=graph,
    verbose=True,
    allow_dangerous_requests=True,
)

# Query the graph
queries = [
    "Who discovered radium?",
    "Who worked with Pierre Curie?",
]

for query in queries:
    result = chain.invoke(query)
    print(f"Query: {query}\nResult: {result}\n")


# --- Stage 2: Update the graph ---

conn = kuzu.Connection(db)

conn.execute("MATCH (p:Person) WHERE p.id = 'Becquerel' DETACH DELETE p")
conn.execute("MERGE (p:Person {id: 'Henri Becquerel'}) SET p.type = 'entity'")
conn.execute(
    """
    MATCH (p:Person {id: 'Henri Becquerel'})
    MATCH (n:NobelPrize {id: 'Nobel Prize in Physics 1903'})
    MERGE (p)-[:WON]->(n)
    """
)
conn.execute(
    """
    MATCH (p:Person {id: 'Pierre Curie'})
    MATCH (n:NobelPrize {id: 'Nobel Prize in Physics 1903'})
    MERGE (p)-[:WON]->(n)
    """
)
conn.execute(
    """
    MATCH (p:Person {id: 'Pierre Curie'})
    MATCH (p2:Person {id: 'Paul Langevin'})
    MERGE (p)-[:WORKED_WITH]->(p2)
    """
)
conn.execute(
    """
    MATCH (p:Person {id: 'Pierre Curie'})
    MATCH (d:Discovery {id: 'Radium'})
    MERGE (p)-[:DISCOVERED]->(d)
    """
)
conn.close()

# --- Stage 3: Query the updated graph ---

# Query the graph
queries = [
    "Who discovered radium?",
    "Who worked with Pierre Curie?",
]

for query in queries:
    result = chain.invoke(query)
    print(f"Query: {query}\nResult: {result}\n")