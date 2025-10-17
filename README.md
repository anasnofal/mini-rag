# 🧠 Mini-RAG

A **minimal implementation of the Retrieval-Augmented Generation (RAG)** model for question answering.  
This project provides a flexible and extensible framework for building your own RAG-based applications.

---

## ✨ Features

- ⚡ **FastAPI Backend** – Modern, high-performance web framework for building APIs with Python.  
- 🧩 **Multiple LLM Providers** – Pluggable support for:
  - OpenAI
  - Cohere
  - Gemini  
- 🗃️ **Multiple Vector Database Providers** – Choose between:
  - Qdrant  
  - PGVector  
- 📂 **Flexible Data Ingestion** – Upload and process `.txt` and `.pdf` files for indexing.  
- 🐳 **Dockerized Environment** – Full containerized setup with Docker Compose.  
- 📈 **Monitoring** – Integrated with Prometheus for performance insights.  
- 🔁 **CI/CD Pipeline** – Automated deployment with GitHub Actions.

---

## 📁 Project Structure

```bash
├── .github/workflows/         # GitHub Actions CI/CD workflows
├── docker/                    # Docker configurations for all services
│   ├── minirag/               # Dockerfile and entrypoint for FastAPI app
│   ├── nginx/                 # Nginx reverse proxy configuration
│   └── prometheus/            # Prometheus monitoring configuration
├── src/                       # Main application source code
│   ├── assets/                # Storage for uploaded documents
│   ├── controllers/           # Core business logic
│   ├── helpers/               # Configuration and utility helpers
│   ├── models/                # Pydantic models and SQLAlchemy schemas
│   ├── routes/                # API endpoint definitions
│   ├── stores/                # Integrations with external services (LLMs, Vector DBs)
│   ├── utils/                 # General utility functions
│   ├── main.py                # FastAPI app entrypoint
│   └── requirements.txt       # Python dependencies
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- 🐳 Docker & Docker Compose (for containerized setup)
- 🐍 Python 3.10+ (for local development)
- 🔑 API key for your chosen LLM provider (OpenAI, Cohere, or Gemini)

---

### 🧱 Using Docker (Recommended)

The easiest way to get started is with **Docker Compose**.

```bash
# Clone the repository
git clone https://github.com/anasnofal/mini-rag.git
cd mini-rag
```

Navigate to the Docker directory and follow setup instructions:

```bash
cd docker
# Follow setup in docker/README.md
sudo docker compose up -d
```

---

### 💻 Local Development Setup

If you prefer to run locally without Docker:

```bash
# Clone and install dependencies
git clone https://github.com/anasnofal/mini-rag.git
cd mini-rag
pip install -r requirements.txt
```

Set up your environment variables:

```bash
cp .env.example .env
# Add your API keys and configurations to .env
```

Run database migrations and start the server:

```bash
alembic upgrade head
uvicorn src.main:app --reload --host 0.0.0.0 --port 5000
```

---

## 📫 Testing with Postman

A ready-to-use Postman collection is included:

[src/assets/mini-rag-app.postman_collection.json](src/assets/mini-rag-app.postman_collection.json)

Import it into Postman to test endpoints quickly.

---

## 🔌 API Endpoints

Swagger UI Documentation:

- Docker: [http://localhost:8000/docs](http://localhost:8000/docs)  
- Local: [http://localhost:5000/docs](http://localhost:5000/docs)

### 🗂️ Data Endpoints

| Method | Endpoint | Description |
|--------|-----------|-------------|
| POST | `/api/v1/data/upload/{project_id}` | Upload a file to a specific project |
| POST | `/api/v1/data/process/{project_id}` | Process uploaded files and create text chunks |

### 🧠 NLP Endpoints

| Method | Endpoint | Description |
|--------|-----------|-------------|
| POST | `/api/v1/nlp/index/push/{project_id}` | Index processed chunks into the vector database |
| GET | `/api/v1/nlp/index/info/{project_id}` | Retrieve index info for a project |
| POST | `/api/v1/nlp/index/search/{project_id}` | Search the vector DB for relevant documents |
| POST | `/api/v1/nlp/index/answer/{project_id}` | Generate an answer via the RAG pipeline |

---

## ⚙️ Configuration

Environment variables are used to configure the system.  
Key variables in `.env` include:

| Variable | Description |
|-----------|-------------|
| `GENERATION_BACKEND` | LLM provider for text generation (`openai`, etc.) |
| `EMBEDDING_BACKEND` | LLM provider for text embeddings |
| `VECTOR_DB_BACKEND` | Vector database (`qdrant` or `pgvector`) |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, etc. | Database credentials |
| `OPENAI_API_KEY`, `COHERE_API_KEY`, etc. | LLM API keys |

---

## 🛠️ Built With

- **FastAPI** – Web framework  
- **LangChain** – LLM application framework  
- **Docker** – Containerization  
- **PostgreSQL + pgvector** – Database and similarity search  
- **Qdrant** – Alternative vector DB  
- **Prometheus** – Monitoring and alerting  

---

## 📄 License

This project is licensed under the **Apache License 2.0**.  
See the [LICENSE](LICENSE) file for more details.

---

> Made with ❤️ by [Anas Nofal](https://github.com/anasnofal)
