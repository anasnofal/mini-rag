APP_NAME="mini-RAG"
APP_VERSION="0.1"
FILE_ALLOWED_TYPES=["text/plain","application/pdf"]
FILE_MAX_SIZE=10
FILE_DEFAULT_CHUNK_SIZE=512000 # 512KB


#=====================PostgreSQL Database config========================
POSTGRES_USERNAME=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_MAIN_DB=

#=====================llm config========================
GENERATION_BACKEND= "gemini" # OPENAI, COHERE
EMBEDDING_BACKEND= "cohere" # OPENAI, COHERE

OPENAI_API_KEY= 
OPENAI_API_URL= #"http://localhost:11434/v1" 
COHERE_API_KEY=
GEMINI_API_KEY=

#=====================llm model config========================
GENERATION_MODEL_ID_LITERALS = ["command-light", "qwen3:4b-q4_K_M", "gpt-3.5-turbo-0125", "gemini-2.0-flash-lite"]
GENERATION_MODEL_ID=  "gemini-2.0-flash-lite" # "qwen3:4b-q4_K_M"  "gpt-3.5-turbo-0125"  "gemini-2.0-flash-lite"

EMBEDDING_MODEL_ID="embed-multilingual-v3.0" #gemini-embedding-001
EMBEDDING_MODEL_SIZE=1024  # 3072 for Gemini, 384 for Cohere light, 1024 for Cohere multilingual

INPUT_DEFAULT_MAX_CHARACTERS=1024
GENERATION_DEFAULT_MAX_TOKENS=200
GENERATION_DEFAULT_TEMPERATURE=0.1
#=====================vectordb config========================
VECTOR_DB_BACKEND_LITERALS = ["qdrant", "pgvector"]
VECTOR_DB_BACKEND="pgvector" # QDRANT, pgvector
VECTOR_DB_PATH="qdrant_db"
VECTOR_DB_DISTANCE_METHOD="cosine" # cosine, dot, euclidean
VECTOR_DB_PGVEC_INDEX_THRESHOLD=500

#=====================Template config========================
PRIMARY_LANGUAGE="en"
DEFAULT_LANGUAGE="en"