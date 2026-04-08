# AutoCrew — Multi-Agent AI Research Platform

A production-grade multi-agent system that autonomously researches any topic using a pipeline of specialized AI agents. Submit a question, and four coordinated agents decompose it, search the web, analyze findings, and produce a structured report — all in real time.

---

## What It Does

AutoCrew accepts a research question and routes it through four agents in sequence:

```
Manager → Research → Analyst → Writer
```

1. **Manager** — Breaks the topic into 3-4 focused sub-questions and drafts a research plan
2. **Research** — Searches the web for each sub-question using a custom DuckDuckGo scraper (ReAct loop)
3. **Analyst** — Extracts key insights, patterns, risks, and opportunities from the raw findings
4. **Writer** — Synthesizes everything into a polished Markdown report

Results stream live to the dashboard via WebSocket as each agent completes.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (React)                   │
│         Dashboard  ←  WebSocket  ←  Redis pub/sub       │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP POST /tasks
┌────────────────────────▼────────────────────────────────┐
│                   Backend (FastAPI)                      │
│   POST /tasks → BackgroundTask → run_crew()             │
│   GET  /tasks/:id → PostgreSQL                          │
│   WS   /ws/:task_id → Redis subscriber                  │
└──────┬──────────────────────────────────┬───────────────┘
       │                                  │
┌──────▼──────┐                  ┌────────▼────────┐
│  LangGraph   │                  │    Kafka         │
│  StateGraph  │                  │  task.created   │
│  4 agents    │                  │  agent.completed│
│              │                  │  task.completed │
└──────┬───────┘                  └─────────────────┘
       │
  ┌────▼──────────────────────────────────────────┐
  │                  Agent Layer                   │
  │  manager_agent → research_agent (ReAct+DDG)   │
  │               → analyst_agent → writer_agent  │
  └────────────────────┬──────────────────────────┘
                       │
              ┌────────▼────────┐
              │    ChromaDB      │
              │  RAG: past       │
              │  research cache  │
              └─────────────────┘
```

### Data Flow (step by step)

1. User submits a task via the React dashboard
2. FastAPI creates a DB record and dispatches `run_crew()` as a `BackgroundTask`
3. Kafka receives a `task.created` event
4. LangGraph streams the `AgentState` dict through each agent node
5. After each agent completes, Redis publishes a JSON update on `task:{id}`
6. FastAPI WebSocket subscriber receives the Redis message and pushes it to the browser
7. Dashboard updates the agent card in real time (status, tokens, duration, preview)
8. When the Writer agent finishes, a `task_complete` event is published with the full report
9. The result is saved to PostgreSQL and embedded in ChromaDB for future RAG retrieval

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Docker Desktop | 4.x+ | Must be running |
| OpenAI API key | — | GPT-4o access required |
| Git | any | — |

No Python or Node installation needed — everything runs inside Docker.

---

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/your-username/AutoCrew.git
cd AutoCrew

cp .env.example .env
# Open .env and set your OpenAI API key:
# OPENAI_API_KEY=sk-proj-...
```

### 2. Start all services

```bash
docker-compose up --build
```

First build takes ~3-5 minutes (downloads images, installs Python packages). Subsequent starts are fast.

Wait until you see:
```
backend   | INFO:     Application startup complete.
frontend  | Local:   http://localhost:3000/
```

### 3. Open the app

| Service | URL | Description |
|---|---|---|
| **Dashboard** | http://localhost:3000 | Main UI — submit tasks, watch agents |
| **API docs** | http://localhost:8000/docs | FastAPI Swagger UI |
| **Kafka UI** | http://localhost:8080 | Browse topics, messages, consumers |
| **ChromaDB** | http://localhost:8001 | Vector store REST API |

### 4. Submit your first task

Go to http://localhost:3000, type a research question like:

> Compare PostgreSQL vs MySQL for high-traffic web applications

Click **Start Research** and watch the four agent cards update live.

---

## All Commands

```bash
# Start everything (builds images if needed)
make up
# or: docker-compose up --build

# Start in background
docker-compose up -d --build

# Stop all containers
make down

# Rebuild images from scratch (after dependency changes)
docker-compose build --no-cache backend

# Tail all logs
make logs
# or: docker-compose logs -f

# Tail a specific service
docker-compose logs -f backend

# Run unit tests
make test
# or: pytest tests/unit/ -v

# Run E2E tests (requires Playwright)
make test-e2e

# Lint Python code
make lint
# or: ruff check agents/ backend/ data/

# Open a shell in the backend container
docker-compose exec backend bash
```

---

## Project Structure

```
AutoCrew/
├── agents/                     # All AI agent logic
│   ├── state.py                # AgentState TypedDict (shared state)
│   ├── graph.py                # LangGraph pipeline + Redis events
│   ├── manager_agent.py        # Decomposes task into research plan
│   ├── research_agent.py       # ReAct agent with web search
│   ├── analyst_agent.py        # Extracts insights from raw research
│   ├── writer_agent.py         # Synthesizes final report
│   └── tools/
│       ├── search.py           # Custom DuckDuckGo HTTP scraper
│       └── memory.py           # ChromaDB RAG (past research)
│
├── backend/                    # FastAPI server
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # App init, DB startup
│       ├── config.py           # Settings from .env
│       ├── routers/
│       │   ├── tasks.py        # POST /tasks, GET /tasks/:id
│       │   └── ws.py           # WebSocket /ws/:task_id
│       └── db/
│           ├── postgres.py     # Schema + async queries (asyncpg)
│           └── redis_client.py # Pub/sub helpers
│
├── data/                       # Event streaming layer
│   ├── kafka_producer.py       # Publishes task/agent events
│   ├── kafka_consumer.py       # Consumes events → updates DB
│   └── schemas/
│       └── task_event.py       # Pydantic event models
│
├── frontend/                   # React + TypeScript dashboard
│   └── src/
│       ├── pages/Dashboard.tsx # Main page
│       ├── components/
│       │   ├── AgentCard.tsx   # Per-agent status card
│       │   ├── TaskInput.tsx   # Prompt input form
│       │   ├── ResultPanel.tsx # Final report display
│       │   └── MetricsBar.tsx  # Tokens + duration summary
│       ├── hooks/useWebSocket.ts
│       ├── api/client.ts
│       └── types/index.ts
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_manager.py
│   │   ├── test_research.py
│   │   ├── test_graph.py
│   │   └── test_pipeline.py
│   └── e2e/
│       └── test_dashboard.py   # Playwright tests
│
├── .github/workflows/ci.yml    # GitHub Actions CI
├── docker-compose.yml          # 8-service orchestration
├── Makefile                    # Developer shortcuts
├── pytest.ini                  # Test configuration
└── .env.example                # Environment template
```

---

## Services (Docker Compose)

| Container | Image | Port | Role |
|---|---|---|---|
| `backend` | Custom (Python 3.11) | 8000 | FastAPI app + agent runner |
| `frontend` | Custom (Node 18) | 3000 | React dashboard |
| `postgres` | postgres:15-alpine | 5432 | Task persistence |
| `redis` | redis:7-alpine | 6379 | Real-time pub/sub |
| `kafka` | cp-kafka:7.5.0 | 9092 | Event streaming |
| `zookeeper` | cp-zookeeper:7.5.0 | — | Kafka coordination |
| `kafka-ui` | provectuslabs/kafka-ui | 8080 | Kafka browser UI |
| `chromadb` | chromadb/chroma | 8001 | Vector store (RAG) |

---

## The Four Agents Explained

### Manager Agent
- **Model:** GPT-4o, temperature 0.3
- **Role:** Strategic decomposition. Takes the raw user query and produces a numbered research plan with 3-4 focused sub-questions and an approach strategy.
- **Why it exists:** Without decomposition, a single LLM call produces shallow coverage. Breaking the topic forces thorough, structured research.

### Research Agent
- **Model:** GPT-4o via ReAct loop (Reason + Act)
- **Role:** Executes web searches for each sub-question, observes results, reasons about what was found, and produces a comprehensive findings summary.
- **Pattern:** ReAct (`create_react_agent` + `AgentExecutor`) — the agent alternates between Thought/Action/Observation steps until it has enough data for a Final Answer.
- **Tool:** Custom `web_search` — POST to `https://html.duckduckgo.com/html/`, parse results with regex, strip HTML tags. Built this way because the `duckduckgo-search` library gets rate-limited inside Docker.
- **Token tracking:** Custom `_TokenCounter(BaseCallbackHandler)` using `on_llm_end` — necessary because `get_openai_callback()` doesn't work in async LangChain contexts.
- **RAG:** Before searching, queries ChromaDB for similar past research to provide as context.

### Analyst Agent
- **Model:** GPT-4o, temperature 0.3
- **Role:** Reads the raw research output and structures it into: Key Insights, Patterns & Trends, Risks & Challenges, Opportunities, Data Points.
- **Why separate from Research:** Separation of concerns — the researcher gathers data without editorializing; the analyst interprets without collecting.

### Writer Agent
- **Model:** GPT-4o, temperature 0.3
- **Role:** Has access to all prior state (original task + plan + research + analysis) and writes a professional Markdown report with Executive Summary, Key Findings, Analysis, Risks, Recommendations, and Conclusion.
- **Why last:** The writer needs the full picture before writing. This ordering ensures no section is synthesized from incomplete data.

---

## Shared State: AgentState

All agents communicate through a single `TypedDict` that LangGraph passes between nodes:

```python
class AgentState(TypedDict):
    task_id: str
    input_task: str          # Original user question
    manager_plan: str        # Set by Manager
    research_results: str    # Set by Research
    analysis_results: str    # Set by Analyst
    final_output: str        # Set by Writer
    current_agent: str       # Which agent just ran
    agent_statuses: dict     # {agent: 'waiting'|'running'|'done'|'error'}
    error: Optional[str]
    metadata: dict           # tokens_used, duration_ms per agent
```

Each agent receives the full state, adds its output fields, and returns a partial dict. LangGraph merges it back before passing to the next node.

---

## Tech Stack & Design Decisions

| Technology | Why |
|---|---|
| **LangGraph** | Explicit graph of agent nodes with typed shared state. More transparent and debuggable than AutoGen or CrewAI — you can see exactly what each agent receives and returns. |
| **FastAPI** | Async-first Python web framework. `BackgroundTasks` lets agent pipelines run without blocking the HTTP response. |
| **Redis pub/sub** | Lowest-latency broadcast mechanism for streaming updates. Each agent completion publishes to `task:{id}`; the WebSocket handler subscribes and forwards to the browser instantly. |
| **WebSocket** | Required for true real-time push. Long-polling would add 1-2s lag per update; SSE would work but WebSocket is bidirectional (future use). |
| **Kafka** | Durable, replayable event log. Every task lifecycle event (`task.created`, `agent.completed`, `task.completed`) is persisted. Enables audit trails, analytics, and retry logic without touching the main app. |
| **PostgreSQL** | Relational persistence for tasks. Stores status, agent outputs, and metadata. asyncpg gives non-blocking queries compatible with FastAPI's async loop. |
| **ChromaDB** | Embedding-based vector store for RAG. When a new task comes in, similar past research is retrieved and injected into the Research agent's prompt — improving quality without extra API calls. |
| **React + Vite + Tailwind** | Fast dev server, typed components, utility-first CSS. No heavy UI framework needed for a dashboard this size. |
| **ReAct pattern** | Interleaved reasoning and acting. The Research agent explains its thinking before each search, making failures debuggable and outputs more reliable than a single-shot prompt. |

---

## Kafka UI Guide

Open http://localhost:8080 after starting the stack.

**Topics to watch:**
- `task.created` — fires when a task is submitted
- `agent.completed` — fires after each of the 4 agents finishes
- `task.completed` — fires when the full pipeline is done

**How to use it:**
1. Click **Topics** in the left sidebar
2. Select `task.created` → **Messages** tab
3. Submit a task from the dashboard
4. Refresh — you'll see the JSON event with `task_id`, `input_task`, `timestamp`
5. Switch to `agent.completed` to see per-agent metrics (tokens, duration_ms, status)

This is how you'd build dashboards, alerting, or replay logic in a real system.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
# Required — get from platform.openai.com
OPENAI_API_KEY=sk-proj-...

# Pre-configured for Docker Compose — do not change unless running outside Docker
POSTGRES_URL=postgresql://autocrew:autocrew_secret@postgres:5432/autocrew
REDIS_URL=redis://redis:6379
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
CHROMA_HOST=chromadb
CHROMA_PORT=8000
```

Only `OPENAI_API_KEY` needs to be set. All other values point to Docker Compose service names and work out of the box.

---

## Running Tests

```bash
# Unit tests (no Docker needed — all LLM calls are mocked)
pytest tests/unit/ -v

# Or via Make
make test
```

Test coverage:
- `test_manager.py` — plan generation, token tracking, error handling
- `test_research.py` — web search results, RAG context injection, empty RAG fallback
- `test_graph.py` — full pipeline execution with fake async stream
- `test_pipeline.py` — Kafka event schema validation, serialization

---

## CI/CD

GitHub Actions runs on every push and PR to `main`:

- **test-backend** — spins up Postgres + Redis services, runs `pytest tests/unit/`
- **test-frontend** — `npm install` → `npm run build` → `tsc --noEmit`
- **lint** — `ruff check agents/ backend/ data/`

See [.github/workflows/ci.yml](.github/workflows/ci.yml).

---

## Troubleshooting

**Docker won't start / permission errors**
Make sure Docker Desktop is running and you have file sharing enabled for the project directory.

**`OPENAI_API_KEY` errors**
Confirm `.env` exists (not just `.env.example`) and the key starts with `sk-`.

**Backend rebuilds don't pick up new packages**
Run `docker-compose build --no-cache backend` to bypass the layer cache after changing `requirements.txt`.

**Research agent is slow (~30-60s)**
This is normal. The ReAct loop makes multiple GPT-4o calls plus web requests. Token usage is displayed in the Metrics bar when it completes.

**Kafka UI shows no topics**
Topics are created on first use. Submit at least one task from the dashboard, then refresh Kafka UI.

---

## Goals of This Project

AutoCrew was built as a portfolio project to demonstrate:

- **Multi-agent orchestration** — how specialized agents with narrow roles outperform a single general-purpose prompt
- **Real-time event-driven architecture** — combining Redis pub/sub, WebSockets, and Kafka in a single coherent system
- **Production patterns** — async Python, typed state, dependency health checks, CI/CD, unit tests with mocked LLMs
- **RAG in practice** — ChromaDB vector search improving agent output over time without retraining

---

*Built with LangGraph, FastAPI, React, Kafka, Redis, PostgreSQL, and ChromaDB.*
