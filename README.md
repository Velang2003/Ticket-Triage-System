# AI-Powered Ticket Triage System

![Python](https://img.shields.io/badge/Python-3.14-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-316192.svg)
![pgvector](https://img.shields.io/badge/pgvector-Supported-blueviolet)
![Gemini](https://img.shields.io/badge/Google%20GenAI-Gemini%203.6%20Flash-orange)
![Test Coverage](https://img.shields.io/badge/Test%20Coverage-100%25-brightgreen.svg)

An intelligent, asynchronous support ticket triage system that leverages **Google Gemini (GenAI)** to automatically classify, prioritize, and suggest resolutions for customer support requests.

---

##  Overview

Customer support teams often spend countless hours manually reading, tagging, and routing incoming tickets. The **Ticket Triage System** automates this bottleneck using advanced Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG). 

When a user submits a ticket, the system asynchronously:
1. **Classifies** the ticket into the correct category (e.g., Billing, Technical, Account).
2. **Prioritizes** the issue based on urgency and sentiment (Low, Medium, High, Critical).
3. **Suggests** a resolution by finding relevant articles in the internal knowledge base using vector similarity search (`pgvector`), then generates a custom response for the agent.

##  Key Features

- **Automated LLM Triage:** Uses `gemini-3.6-flash` for zero-shot categorization and priority assignment.
- **RAG Resolution Suggestions:** Generates support responses using `gemini-embedding-2` and `pgvector` cosine similarity search over a vector database of knowledge articles.
- **Resilient Architecture:** Implements graceful degradation. If the LLM API is down, tickets are securely saved with a "pending" status and can be re-triggered later.
- **Audit Logging:** Every ticket transition and LLM classification is permanently recorded.
- **Reporting Analytics:** Group volume by category, priority, and status using fast SQL aggregations.
- **Hybrid Testing:** Pytest suite runs instantly using an in-memory SQLite database via a custom `FlexibleVector` fallback, while Newman verifies live API contracts against PostgreSQL.

##  Use Cases

- **IT Service Desks:** Automatically route "Cannot connect to VPN" tickets to the Network team with a "High" priority, while suggesting troubleshooting steps from the internal wiki.
- **SaaS Customer Support:** Instantly provide billing agents with a drafted response for "Refund request" tickets based on company policy articles.
- **E-Commerce:** Triage missing order inquiries and generate empathetic, context-aware responses citing shipping FAQs.

##  Tech Stack

- **Backend Framework:** FastAPI, Uvicorn
- **Language:** Python 3.14
- **Database:** PostgreSQL 16 + `pgvector` extension
- **ORM / Migrations:** SQLAlchemy 2.0 (Async), Alembic
- **AI / Embeddings:** Google GenAI SDK (`google-genai`), Gemini 3.6 Flash, Gemini Embedding 2
- **Testing:** Pytest (Unit/Functional), Postman/Newman (Contract/Integration)
- **Containerization:** Docker Compose

---

##  Getting Started

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Docker Desktop (for PostgreSQL)
- Node.js & npm (for Newman contract tests)
- A Google Gemini API Key

### 2. Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/Velang2003/Ticket-Triage-System.git
cd "Ticket Triage System"

python -m venv .venv
# Activate the virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the root directory (you can copy `.env.example` if available) and update it:

```env
APP_NAME="Ticket Triage System"
APP_ENV=development
API_KEY=triage-secret-key-2026

# Database configuration
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ticket_triage
SYNC_DATABASE_URL=postgresql://postgres:password@localhost:5432/ticket_triage

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
```

### 4. Database Setup

Start the PostgreSQL database with the `pgvector` extension enabled using Docker Compose:

```bash
docker-compose up -d
```

Run Alembic to apply all database migrations and create the tables:

```bash
alembic upgrade head
```

### 5. Running the Server

Start the FastAPI application:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The interactive API documentation will be available at: **http://localhost:8000/docs**

---

##  Working with the Project (API Demonstration)

To test the AI triage, you must authenticate requests by passing the `X-API-Key` header matching your `.env` file (e.g., `X-API-Key: triage-secret-key-2026`).

### Step 1: Add a Knowledge Article
First, populate the Knowledge Base so the RAG system has context. This automatically creates a 768-dimensional vector embedding.

**`POST /api/v1/knowledge-articles`**
```json
{
  "title": "How to reset your billing password",
  "content": "To reset your password, navigate to the login portal and click 'Forgot Password'. You will receive an email with a secure reset link. Ensure you check your spam folder.",
  "category": "Account"
}
```

### Step 2: Submit a Ticket
Submit a ticket. The system will synchronously contact Gemini to classify the ticket and generate a resolution suggestion.

**`POST /api/v1/tickets`**
```json
{
  "subject": "Cannot access billing portal",
  "description": "I click on billing but get a 403 error every time. I forgot my password but the reset isn't working.",
  "submitter_email": "user@example.com"
}
```

**Expected AI Response Data:**
```json
{
  "status": "success",
  "data": {
    "id": "712f6b8f-6fb0...",
    "category": "Billing",
    "priority": "High",
    "status": "Open",
    ...
  }
}
```

### Step 3: Fetch the RAG Suggestion
Fetch the LLM-generated resolution suggestion for the agent to review before responding to the customer.

**`GET /api/v1/tickets/{ticket_id}/suggestion`**

**Expected Response:**
```json
{
  "status": "success",
  "data": {
    "id": "...",
    "suggested_text": "Hello, I understand you are getting a 403 error and having trouble resetting your password. As per our knowledge base, please ensure you check your spam folder for the secure reset link...",
    "source_article_ids": ["article-uuid-here"]
  }
}
```

---

##  Testing

The project uses a dual-testing strategy.

### Unit & Functional Tests (Pytest)
Tests run seamlessly against an in-memory SQLite database. Vector operations are safely degraded to JSON text to allow full ORM testing without requiring a PostgreSQL instance.

```bash
pytest tests/ -v
```

### API Contract Tests (Postman & Newman)
Integration tests verify end-to-end API correctness against a live PostgreSQL database and Gemini API.

```bash
# Ensure your local server is running (uvicorn app.main:app)
npm install -g newman

newman run postman/ticket_triage.postman_collection.json \
  -e postman/ticket_triage.postman_environment.json
```

---

##  Project Structure

```text
Ticket-Triage-System/
├── alembic/                 # Database migrations
├── app/
│   ├── api/                 # FastAPI routers (v1 endpoints)
│   ├── core/                # Configuration, auth, logging
│   ├── db/                  # Database session and base models
│   ├── llm/                 # Gemini GenAI client, prompts, embeddings
│   ├── models/              # SQLAlchemy ORM Models (Ticket, Article, etc.)
│   ├── repositories/        # Database CRUD operations
│   ├── schemas/             # Pydantic validation schemas
│   └── services/            # Business logic (Triage, RAG)
├── postman/                 # API contract tests
├── tests/                   # Pytest suite
├── docker-compose.yml       # Local PostgreSQL + pgvector cluster
└── pyproject.toml           # Dependencies & tools configuration
```

---

*Built with ❤️ utilizing FastAPI and Google GenAI.*

