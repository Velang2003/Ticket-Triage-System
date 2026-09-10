# Software Requirements Specification
## AI-Powered Support Ticket Triage System

| Field | Detail |
|---|---|
| Document Type | Software Requirements Specification (SRS) |
| Project | AI-Powered Support Ticket Triage System |
| Prepared By | Ashwamedha (Velan G) |
| Purpose | Portfolio project demonstrating Python, FastAPI, SQL, REST APIs, LLM/RAG integration, and test automation |
| Version | 1.0 |

---

## 1. Introduction

### 1.1 Purpose
This document defines the requirements and design of an AI-Powered Support Ticket Triage System. The system accepts incoming support tickets, classifies them by category and priority using a language model, and suggests a resolution by retrieving relevant knowledge-base articles before an agent responds. The project is built to demonstrate backend engineering, API design, database usage, AI/LLM integration, and automated testing in a single, coherent application.

### 1.2 Scope
The system covers ticket intake, automatic classification, knowledge-base retrieval (RAG), resolution suggestion, and reporting on triage outcomes. It does not cover live chat, voice support, or direct customer-facing communication — it is a backend decision-support layer that a support team or a downstream application would sit on top of.

### 1.3 Intended Audience
Written for engineers building or reviewing the system, and for anyone evaluating this project as part of a technical portfolio.

---

## 2. Functional Requirements

| ID | Requirement | Description |
|---|---|---|
| FR-1 | Ticket Intake | The system shall accept a new support ticket via a REST API, capturing subject, description, and submitter details. |
| FR-2 | Automatic Classification | The system shall classify each ticket into a category (e.g., Billing, Technical, Account) and a priority level (Low, Medium, High, Critical) using an LLM with a defined prompt template. |
| FR-3 | Knowledge Retrieval | The system shall retrieve the most relevant articles from a knowledge base using vector similarity search (RAG) based on ticket content. |
| FR-4 | Resolution Suggestion | The system shall generate a suggested resolution summary by combining retrieved articles with the ticket context, using the LLM. |
| FR-5 | Ticket Status Management | The system shall allow a ticket's status to be updated (Open, In Progress, Resolved, Closed) via an API call. |
| FR-6 | Ticket Retrieval | The system shall allow tickets to be fetched individually by ID or as a filtered, paginated list (by status, category, or priority). |
| FR-7 | Knowledge Base Management | The system shall allow knowledge-base articles to be added and updated, with each new article automatically re-indexed for retrieval. |
| FR-8 | Validation | The system shall reject ticket submissions that are empty, exceed a defined length, or are missing required fields, returning a clear error message. |
| FR-9 | Audit Logging | The system shall record which classification and suggestion were generated for each ticket, along with a timestamp, for later review. |
| FR-10 | Reporting | The system shall expose an endpoint summarizing ticket volume by category, priority, and status over a given time range. |

---

## 3. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-1 | Performance | A ticket classification response shall be returned within 3 seconds under normal load, excluding external LLM provider latency spikes. |
| NFR-2 | Reliability | If the LLM provider is unavailable, the system shall still accept and store the ticket, marking classification as pending rather than failing the request. |
| NFR-3 | Scalability | The API layer shall be stateless so multiple instances can run behind a load balancer without shared in-memory state. |
| NFR-4 | Data Integrity | All ticket and classification records shall be persisted transactionally so a partial failure never leaves an inconsistent record. |
| NFR-5 | Security | All API endpoints shall require an API key or token; sensitive fields (submitter email) shall not appear in logs. |
| NFR-6 | Testability | Every endpoint shall have automated functional, edge-case, and error-path test coverage, plus a Postman collection for manual verification. |
| NFR-7 | Maintainability | Code shall be organized into clearly separated layers (API, service, data access) so components can be modified independently. |
| NFR-8 | Observability | The system shall log each classification request, its latency, and outcome, to support later performance and accuracy review. |
| NFR-9 | Portability | The system shall run identically in a local environment and inside a Docker container, with configuration supplied via environment variables. |

---

## 4. Core Entities

### 4.1 Ticket

| Field | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique identifier for the ticket |
| subject | Text | Short ticket title |
| description | Text | Full ticket body submitted by the customer |
| submitter_email | Text | Contact email of the person raising the ticket |
| category | Enum | Assigned by the classifier — Billing, Technical, Account, Other |
| priority | Enum | Assigned by the classifier — Low, Medium, High, Critical |
| status | Enum | Open, In Progress, Resolved, Closed |
| created_at / updated_at | Timestamp | Record lifecycle timestamps |

### 4.2 Classification

| Field | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique identifier for the classification record |
| ticket_id | UUID (FK) | Ticket this classification belongs to |
| predicted_category | Enum | Category returned by the LLM |
| predicted_priority | Enum | Priority returned by the LLM |
| confidence_note | Text | Short model-generated rationale for the classification |
| created_at | Timestamp | When the classification was generated |

### 4.3 KnowledgeArticle

| Field | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique identifier for the article |
| title | Text | Article title |
| content | Text | Full article body used for retrieval |
| embedding | Vector | Stored embedding used for similarity search |
| category | Enum | Which ticket category the article is relevant to |
| updated_at | Timestamp | Last time the article was edited or re-indexed |

### 4.4 ResolutionSuggestion

| Field | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique identifier for the suggestion |
| ticket_id | UUID (FK) | Ticket the suggestion applies to |
| suggested_text | Text | LLM-generated resolution summary |
| source_article_ids | Array | IDs of knowledge articles used to generate the suggestion |
| created_at | Timestamp | When the suggestion was generated |

### 4.5 AuditLog

| Field | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique identifier for the log entry |
| ticket_id | UUID (FK) | Ticket the event relates to |
| event_type | Text | e.g., classified, suggestion_generated, status_changed |
| details | JSON | Structured detail of what happened |
| created_at | Timestamp | When the event occurred |

---

## 5. API Gateway and Endpoints

All endpoints are served behind a single FastAPI gateway, versioned under `/api/v1`. Every request requires an API key passed via the `X-API-Key` header. Responses follow a consistent JSON envelope with a `status` field and a `data` or `error` field.

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v1/tickets | Create a new ticket; triggers async classification and suggestion generation |
| GET | /api/v1/tickets/{id} | Fetch a single ticket with its latest classification and suggestion |
| GET | /api/v1/tickets | List tickets with filters: status, category, priority, page, page_size |
| PATCH | /api/v1/tickets/{id}/status | Update a ticket's status |
| POST | /api/v1/tickets/{id}/classify | Manually re-trigger classification for a ticket |
| GET | /api/v1/tickets/{id}/suggestion | Fetch the latest resolution suggestion for a ticket |
| POST | /api/v1/knowledge-articles | Add a new knowledge-base article; triggers embedding and indexing |
| PUT | /api/v1/knowledge-articles/{id} | Update an existing article; triggers re-indexing |
| GET | /api/v1/knowledge-articles | List knowledge-base articles, optionally filtered by category |
| GET | /api/v1/reports/summary | Return ticket volume grouped by category, priority, and status for a date range |
| GET | /api/v1/health | Health check endpoint for uptime monitoring |

### 5.1 Standard Response Envelope

```json
{
  "status": "success | error",
  "data": {},
  "error": {"code": "string", "message": "string"}
}
```

---

## 6. Technology Stack

| Layer | Choice |
|---|---|
| Language | Python 3.11 |
| API Framework | FastAPI |
| Database | PostgreSQL (relational data) + pgvector extension (embeddings) |
| LLM Provider | Gemini API (or OpenAI-compatible endpoint), configurable via environment variable |
| Embeddings | Sentence-transformer or provider embedding endpoint, for RAG retrieval |
| ORM / Data Access | SQLAlchemy |
| Testing | pytest (functional, edge-case, error-path tests) + Postman/Newman (API contract tests) |
| API Documentation | OpenAPI/Swagger, auto-generated by FastAPI |
| Containerization | Docker + docker-compose (API service + PostgreSQL) |
| CI | GitHub Actions — runs lint and pytest suite on every push |
| Logging | Structured JSON logging via Python's logging module |

---

## 7. High-Level Design

The system follows a layered architecture: an API layer handles requests and validation, a service layer contains business logic and orchestrates the AI pipeline, and a data layer handles persistence. The AI pipeline itself is a separate internal module so the classification and retrieval logic can be tested and swapped independently of the web layer.

```
+-------------+      +------------------+      +----------------------+
|   Client    | ---> |   API Gateway    | ---> |    Service Layer     |
| (Postman /  |      |   (FastAPI)      |      | - Ticket Service     |
|  downstream |      |  - Auth (API Key)|      | - Classification Svc |
|  app)       | <--- |  - Validation    | <--- | - RAG / Suggestion   |
+-------------+      +------------------+      +-----------+----------+
                                                            |
                        +-----------------------------------+-----------------------------+
                        |                                    |                             |
                        v                                    v                             v
              +-------------------+              +-------------------+        +-------------------------+
              |   PostgreSQL      |              |   Vector Store     |        |   LLM Provider (API)     |
              |   (tickets,       |              |   (pgvector -      |        |   - Classification call  |
              |    audit log)     |              |   article embeds)  |        |   - Suggestion generation|
              +-------------------+              +-------------------+        +-------------------------+
```
*Figure 7.1 — High-level component diagram*

### 7.1 Component Responsibilities

| Component | Responsibility |
|---|---|
| API Gateway | Authentication, request validation, routing, response formatting |
| Ticket Service | Create/read/update tickets, enforce status transition rules |
| Classification Service | Builds the classification prompt, calls the LLM, parses and stores the result |
| RAG / Suggestion Service | Embeds ticket text, retrieves similar articles, generates a suggested resolution |
| PostgreSQL | Persists tickets, classifications, suggestions, and audit logs |
| Vector Store (pgvector) | Stores knowledge-article embeddings for similarity search |
| LLM Provider | External API used for both classification and suggestion generation |

### 7.2 Primary Flow — Ticket Submission to Suggestion

1. Client submits a ticket via `POST /api/v1/tickets`.
2. API Gateway validates the payload and persists the ticket with status `Open`.
3. Ticket Service passes the ticket text to the Classification Service.
4. Classification Service calls the LLM with a structured prompt and stores category + priority.
5. RAG Service embeds the ticket text and retrieves the top-matching knowledge articles.
6. RAG Service calls the LLM again with the ticket and retrieved articles to generate a suggestion.
7. Classification and suggestion are persisted; an audit log entry is written for each step.
8. Client fetches the enriched ticket via `GET /api/v1/tickets/{id}`.

---

## 8. Low-Level Design

### 8.1 Module Breakdown

| Module | Contents |
|---|---|
| app/api/ | FastAPI route definitions for tickets, knowledge articles, and reports |
| app/schemas/ | Pydantic request/response models used for validation and serialization |
| app/services/ | Business logic — ticket_service.py, classification_service.py, rag_service.py |
| app/models/ | SQLAlchemy ORM models mapping to database tables |
| app/repositories/ | Data-access functions isolating raw SQL/ORM calls from service logic |
| app/llm/ | LLM client wrapper — prompt templates, request/response parsing, retry handling |
| app/core/ | Configuration, authentication middleware, logging setup |
| tests/ | pytest suites — unit, functional, and edge-case tests per module |
| postman/ | Exported Postman collection and environment for manual/CI API verification |

### 8.2 Classification Service — Internal Logic

1. Receive `ticket_id` and ticket text from the Ticket Service.
2. Build a prompt combining the ticket text with a fixed instruction template and a list of valid categories/priorities.
3. Call the LLM client with the prompt and a low temperature setting for consistent output.
4. Parse the LLM response into category, priority, and a short rationale; validate against the allowed enum values.
5. On parse failure, retry once with a stricter format instruction; on repeated failure, mark classification as pending and log the error.
6. Persist the Classification record and write an AuditLog entry.

### 8.3 RAG Retrieval — Internal Logic

1. Generate an embedding vector for the ticket's combined subject and description.
2. Query pgvector for the top-k knowledge articles ranked by cosine similarity, filtered by the ticket's predicted category.
3. Construct a suggestion prompt containing the ticket text and the retrieved article excerpts.
4. Call the LLM to generate a concise suggested resolution referencing the source articles.
5. Persist the ResolutionSuggestion record with the list of source article IDs, and write an AuditLog entry.

### 8.4 Database Schema Overview

```
tickets                     classifications              resolution_suggestions
+--------------+            +--------------------+       +---------------------------+
| id (PK)      |<---+       | id (PK)            |       | id (PK)                   |
| subject      |    +-------| ticket_id (FK)     |       | ticket_id (FK) ------------+--> tickets.id
| description  |    +-------| predicted_category |       | suggested_text            |
| submitter_...|    |       | predicted_priority |       | source_article_ids        |
| category     |    |       | confidence_note    |       | created_at                |
| priority     |    |       | created_at         |       +---------------------------+
| status       |    |       +--------------------+
| created_at   |    |
| updated_at   |    |       knowledge_articles            audit_log
+--------------+    |       +--------------------+        +---------------------+
                     +------>| id (PK)            |        | id (PK)             |
                             | title              |        | ticket_id (FK)      |
                             | content            |        | event_type          |
                             | embedding (vector) |        | details (JSON)      |
                             | category           |        | created_at          |
                             | updated_at         |        +---------------------+
                             +--------------------+
```
*Figure 8.1 — Entity relationship overview*

### 8.5 Error Handling Strategy

| Scenario | HTTP Status | Handling |
|---|---|---|
| Invalid/missing ticket fields | 400 | Field-level validation error listing which fields failed |
| Ticket not found | 404 | Standard not-found error with the requested ID |
| LLM provider timeout or failure | 202 (accepted, pending) | Ticket saved; classification marked pending; retried asynchronously |
| Invalid status transition | 409 | Conflict error explaining the allowed transitions |
| Unauthorized request | 401 | Missing or invalid API key |
| Unexpected server error | 500 | Generic error response; full detail captured in server logs only |

### 8.6 Test Coverage Plan

| Test Type | Coverage |
|---|---|
| Functional | Each endpoint returns correct status and payload for valid input |
| Edge case | Empty ticket body, oversized text, missing required fields, unknown category filter |
| Error handling | LLM provider failure, database unavailability, invalid status transition |
| Integration | Full flow from ticket creation through classification to suggestion generation |
| Contract (Postman) | Request/response schema validation for every endpoint, run via Newman in CI |
