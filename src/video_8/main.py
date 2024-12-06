import os
import shutil
from typing import Literal

import kuzu
import nest_asyncio
from dotenv import load_dotenv
from llama_index.core import PropertyGraphIndex, SimpleDirectoryReader
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor
from llama_index.core.graph_stores.types import Relation, EntityNode
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.graph_stores.kuzu import KuzuPropertyGraphStore
from llama_index.llms.openai import OpenAI

nest_asyncio.apply()
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
assert OPENAI_API_KEY is not None, "OPENAI_API_KEY is not set"
SEED = 42

# --- Stage 1: Indexing ---

shutil.rmtree("ex_kuzu_db", ignore_errors=True)
db = kuzu.Database("ex_kuzu_db")

# Set up the embedding model and LLM
embed_model = OpenAIEmbedding(model_name="text-embedding-3-small")
extraction_llm = OpenAI(model="gpt-4o-mini", temperature=0.0, seed=SEED)
generation_llm = OpenAI(model="gpt-4o-mini", temperature=0.3, seed=SEED)

# Load the dataset on Marie Curie
documents = SimpleDirectoryReader("./data").load_data()

# Define the allowed entities and relationships
entities = Literal["PERSON", "NOBELPRIZE", "DISCOVERY"]
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

# # If we already have a graph store, we can load the index from it
# kg_index = PropertyGraphIndex.from_existing(
#     property_graph_store=graph_store,
# )

# --- Stage 2: Retrieval and Querying ---

# Create a LlamaIndex query engine so we can query the graph
kg_query_engine = kg_index.as_query_engine(llm=generation_llm)

questions = [
    "Who discovered Radium?",
    "Who did Paul Langevin work with?",
]

for question in questions:
    print(f"Question: {question}")
    # Generate a response to the question
    response = kg_query_engine.query(question)
    print(f"Response: {str(response)}\n---\n")

kg_query_engine.retrieve(questions[1])[-1].text

# Augment the graph with additional nodes and relationships

graph_store.upsert_nodes(
    [
        EntityNode(label="PERSON", name="Henri Becquerel"),
    ]
)

graph_store.delete(entity_names=["Nobel Prize"], relation_names=["IS_MARRIED_TO"])

graph_store.upsert_relations(
    [
        Relation(
            label="WORKED_WITH",
            source_id="Paul Langevin",
            target_id="Pierre Curie",
        ),
        Relation(
            label="IS_MARRIED_TO",
            source_id="Pierre Curie",
            target_id="Marie Curie",
        ),
        Relation(
            label="DISCOVERED",
            source_id="Pierre Curie",
            target_id="Radium",
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

# Let's run the queries again
questions = [
    "Who discovered Radium?",
    "Who did Paul Langevin work with?",
]

for question in questions:
    print(f"---\nQuestion: {question}")
    # Generate a response to the question
    response = kg_query_engine.query(question)
    print(f"Response: {str(response)}\n\n")
    for item in kg_query_engine.retrieve(question):
        print(f"Retrieved triple: {item.text}")

