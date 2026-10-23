import chromadb

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings


# ============================================================
# 1. LOAD THE DOCUMENT
# ============================================================

loader = TextLoader("documents/return_policy.txt")
documents = loader.load()

print("Document loaded successfully!")


# ============================================================
# 2. SPLIT THE DOCUMENT INTO SMALL CHUNKS
# ============================================================

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=20
)

chunks = text_splitter.split_documents(documents)

print("Number of chunks:", len(chunks))


# ============================================================
# 3. CREATE THE EMBEDDING MODEL
# ============================================================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("Embedding model loaded successfully!")


# ============================================================
# 4. CREATE CHROMA
# ============================================================

client = chromadb.Client()

print("Chroma client created!")


# Create a collection for our return policy
collection = client.get_or_create_collection(
    name="return_policy"
)

print("Collection created!")


# ============================================================
# 5. GET THE TEXT FROM EACH CHUNK
# ============================================================

texts = [chunk.page_content for chunk in chunks]

print("Texts prepared:", len(texts))


# ============================================================
# 6. CREATE EMBEDDINGS FOR THE CHUNKS
# ============================================================

vectors = embeddings.embed_documents(texts)

print("Chunk embeddings created!")


# ============================================================
# 7. STORE CHUNKS + EMBEDDINGS IN CHROMA
# ============================================================

collection.add(
    ids=[f"chunk_{i}" for i in range(len(texts))],
    documents=texts,
    embeddings=vectors
)

print("Documents stored successfully!")

print("Documents in Chroma:", collection.count())


# ============================================================
# 8. CREATE A REUSABLE SEARCH FUNCTION
# ============================================================

def search_return_policy(query):

    # Convert the customer's question into an embedding
    query_embedding = embeddings.embed_query(query)

    # Search Chroma for the most relevant chunks
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=2
    )

    # Return the actual text of the matching chunks
    return results["documents"][0]


# ============================================================
# 9. TEST THE SEARCH FUNCTION
# ============================================================

query = "How long do customers have to return a product?"

results = search_return_policy(query)

print("\nSearch results:")

for document in results:
    print("-", document)