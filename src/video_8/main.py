import os
import shutil
from typing import Literal

import kuzu
import nest_asyncio
from dotenv import load_dotenv
from llama_index.core import PropertyGraphIndex, Settings, SimpleDirectoryReader
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor
from llama_index.core.graph_stores.types import Relation, EntityNode
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.graph_stores.kuzu import KuzuPropertyGraphStore
from llama_index.llms.openai import OpenAI

nest_asyncio.apply()
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
assert OPENAI_API_KEY is not None, "OPENAI_API_KEY is not set"

# --- Stage 1: Indexing ---

shutil.rmtree("ex_kuzu_db", ignore_errors=True)
db = kuzu.Database("ex_kuzu_db")

# Set up the embedding model and LLM
embed_model = OpenAIEmbedding(model_name="text-embedding-3-small")
extraction_llm = OpenAI(model="gpt-4o-mini", temperature=0.0)
generation_llm = OpenAI(model="gpt-4o-mini", temperature=0.3)

# Load the dataset on Marie Curie
documents = SimpleDirectoryReader("./data").load_data()
documents[0].text

# Define the allowed entities and relationships
entities = Literal["PERSON", "NOBELPRIZE", "LOCATION", "DISCOVERY"]
relations = Literal["DISCOVERED", "IS_MARRIED_TO", "WORKED_WITH", "WON"]

# Define explicit relationship directions as a list of triples
# The graph extraction process will be guided by this schema
validation_schema = [
    ("PERSON", "IS_MARRIED_TO", "PERSON"),
    ("PERSON", "WORKED_WITH", "PERSON"),
    ("PERSON", "WON", "NOBELPRIZE"),
    ("PERSON", "DISCOVERED", "DISCOVERY"),
]

# Intialize graph store
graph_store = KuzuPropertyGraphStore(
    db,
    has_structured_schema=True,
    relationship_schema=validation_schema,
)

# Define schema LLM path extractor: Extract triples from text via an LLM and a provided schema
schema_path_extractor = SchemaLLMPathExtractor(
    llm=extraction_llm,
    possible_entities=entities,
    possible_relations=relations,
    kg_validation_schema=validation_schema,
    strict=True,  # if false, will allow triples outside of the schema
)

# Create property graph index from existing documents
kg_index = PropertyGraphIndex.from_documents(
    documents,
    embed_model=embed_model,
    kg_extractors=[schema_path_extractor],
    property_graph_store=graph_store,
    show_progress=True,
)

# --- Stage 2: Retrieval and Querying ---

# Choose the LLM to use for generation
Settings.llm = generation_llm

# Create a LlamaIndex retriever and query engine so we can query the graph
kg_retriever = kg_index.as_retriever()
kg_query_engine = kg_index.as_query_engine()

questions = [
    "Who discovered Radium?",
    "Who won the Nobel Prize in Physics?",
]

for question in questions:
    print(f"\n\nQuestion: {question}\n")
    response = kg_query_engine.query(question)
    print(str(response))
    # for node in kg_retriever.retrieve(question):
    #     print(f"Retrieved triple: {node.text}")

# Augment the graph with additional nodes and relationships

graph_store.upsert_nodes(
    [
        EntityNode(label="PERSON", name="Henri Becquerel"),
    ]
)

graph_store.upsert_relations(
    [
        Relation(
            label="WORKED_WITH",
            source_id="Pierre Curie",
            target_id="Paul Langevin",
        ),
        Relation(
            label="DISCOVERED",
            source_id="Pierre Curie",
            target_id="radium",
        ),
        Relation(
            label="WON",
            source_id="Pierre Curie",
            target_id="Nobel Prize in Physics",
        ),
        Relation(
            label="WON",
            source_id="Henri Becquerel",
            target_id="Nobel Prize in Physics",
        ),
    ]
)

graph_store.delete(["Nobel Prize"])

Settings.llm = generation_llm

questions = [
    "Who discovered Radium?",
    "Who won the Nobel Prize in Physics?",
]

for question in questions:
    print(f"\n\nQuestion: {question}\n")
    response = kg_query_engine.query(question)
    print(str(response))
    # for node in kg_retriever.retrieve(question):
    #     print(f"Retrieved triple: {node.text}")