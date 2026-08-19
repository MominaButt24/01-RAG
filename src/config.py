# --- Paths ---
UPLOAD_DIR = "data/uploads"
MILVUS_DB_PATH = "rag_milvus.db"

# --- Chunking ---
CHUNK_CHAR_CAP = 5000  # same cap used for pages, slides, and rows

# --- Embedding model ---
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_DIMENSION = 384

# --- Milvus ---
COLLECTION_NAME = "page_chunks_collection"

# --- LLM (Groq) ---
# GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
GROQ_MODEL_NAME = "qwen-2.5-32b"
LLM_TEMPERATURE = 0.2
SYSTEM_INSTRUCTION = """You are an accurate, factual AI document assistant.
Answer the user's question using ONLY the provided document context.
If the information is not explicitly in the context, state: 'I cannot answer based on the provided document.'"""