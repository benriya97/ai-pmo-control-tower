# AI PMO Control Tower

An **AI-assisted Project Management Office (PMO) decision-support system** with a scheduled automation layer. It analyzes project data, uses a local LLM to generate recommendations that reason over their own history (via RAG), surfaces everything in an interactive dashboard, and automatically alerts when a project is at risk.

Built as a hands-on demonstration of **AI workflow automation** — connecting a local LLM, a vector database, a REST API, and a scheduled workflow engine into one working pipeline.

> **Honest scope:** this is a decision-support dashboard plus an automation loop, not a chatbot. See [Where the AI Is (and Isn't)](#where-the-ai-is-and-isnt) for a precise breakdown — the AI *generates* recommendations and the automation *acts on* them, but the routing decisions themselves are deterministic business rules.

---

## What It Does

1. **Analyzes project state** — automated engines compute a health score, detect risks, and find blocked tasks from task and resource data.
2. **Generates AI recommendations** — a local LLM (llama3.2 via Ollama) writes natural-language advice based on the findings.
3. **Remembers its own history (RAG)** — each recommendation is stored in a Chroma vector database; new runs retrieve the most semantically-relevant past recommendations and feed them back into the prompt, so the AI can say things like *"this risk persists — earlier advice wasn't acted on."*
4. **Displays everything live** — an interactive React dashboard shows tasks, resources, health, risks, and dependencies. Update a task's progress and watch every metric cascade in real time.
5. **Automates alerting** — a scheduled n8n workflow calls the advisor each morning, checks the health score against a threshold, and posts a Discord alert only when the project is at risk.

---

## Architecture

```
                         ┌─────────────────────────────────────────┐
                         │              FastAPI Backend             │
   ┌──────────┐          │                                          │
   │  SQLite  │◄────────►│  Analysis engines (health/risk/deps)     │
   │  pmo.db  │  read/   │             │                            │
   └──────────┘  write   │             ▼                            │
                         │      /advisor endpoint                   │
   ┌──────────┐          │        │         ▲                       │
   │  Chroma  │◄─write───│  llm.invoke()    │ retrieve past recs    │
   │ (vectors)│──read───►│        │         │ (RAG)                 │
   └──────────┘          │        ▼         │                       │
        ▲                │   Ollama (llama3.2, local LLM)           │
        │                └─────────────────────────────────────────┘
     embeddings                   ▲                    ▲
                                  │ HTTP               │ HTTP
                        ┌─────────┴──────┐   ┌─────────┴─────────┐
                        │ React Dashboard│   │  n8n (scheduled)  │
                        │ (view + update)│   │  IF risk → Discord│
                        └────────────────┘   └───────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python) |
| Data store | SQLite (via pandas) |
| Local LLM | Ollama + llama3.2 |
| LLM wrapper | LangChain (`langchain_ollama`) |
| Vector DB / RAG | ChromaDB |
| Frontend | React (Vite) |
| Automation | n8n |
| Alerting | Discord webhook |

---

## Key Features

- **RAG pipeline** — recommendations are embedded and stored in Chroma; retrieval is by semantic similarity, giving the LLM memory of its own prior advice.
- **SQLite-backed REST API** — full read *and* write endpoints; data updates through the API, not by editing files.
- **Interactive dashboard** — live-updating tables with color-coded status and resource-overload flags; changing project data cascades through health, risks, dependencies, and AI advice.
- **Scheduled conditional automation** — n8n runs the advisor on a clock and fires an alert only when a condition is met (health below threshold).

---

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/tasks` | GET | All tasks |
| `/resources` | GET | All resources |
| `/health` | GET | Project health score |
| `/risks` | GET | Detected risk categories |
| `/dependencies` | GET | Blocked tasks (unfinished tasks with incomplete dependencies) |
| `/advisor` | GET | RAG-augmented AI recommendation |
| `/tasks/update-progress` | POST | Update a task's progress (status derived automatically) |
| `/resources/update-allocation` | POST | Update a resource's allocated hours |

---

## Running Locally

**Prerequisites:** Python 3, Node.js, [Ollama](https://ollama.com) with `llama3.2` pulled (`ollama pull llama3.2`), and n8n (`npx n8n`).

```bash
# 1. Seed the database from the CSV source (first time only)
cd backend
python seed_db.py

# 2. Start the backend (terminal 1)
uvicorn main:app --reload            # http://127.0.0.1:8000  (docs at /docs)

# 3. Start the frontend (terminal 2)
cd frontend
npm install
npm run dev                          # http://localhost:5173

# 4. (Optional) Start n8n for scheduled alerting (terminal 3)
npx n8n                              # http://localhost:5678
```

To reset all project data to its original values, re-run `python seed_db.py`.

---

## Where the AI Is (and Isn't)

Being precise about this matters more than buzzwords:

- **AI generation** — the LLM writes the recommendations (`/advisor`). ✅
- **RAG** — past recommendations are retrieved by semantic similarity and fed back into the prompt, giving the AI memory. ✅
- **Workflow automation** — n8n schedules the advisor and routes its output to a conditional alert. ✅
- **What's deterministic** — the "should we alert?" decision is a business rule (`health_score < 60`), not an AI judgment. The automation *orchestrates* an AI step; it doesn't use AI to *make* the routing decision.

This is a common, legitimate production architecture: deterministic pipes moving AI-generated content. A natural next step would be putting AI *inside* the decision logic (e.g. via LangGraph) so the model classifies the situation and the flow branches on that.

---

## Project Structure

```
ai-pmo-control-tower/
├── backend/
│   ├── main.py          # FastAPI app: engines, RAG advisor, read/write endpoints
│   ├── seed_db.py       # One-time: loads CSVs into pmo.db
│   └── check_memory.py  # Inspect Chroma vector store contents
├── data/
│   ├── tasks.csv        # Seed source (pmo.db is generated from these, gitignored)
│   └── resources.csv
└── frontend/
    └── src/App.jsx      # Interactive React dashboard
```

---

## Roadmap

- [ ] Resource-update control in the frontend UI
- [ ] Approve/Reject recommendation loop (human-in-the-loop)
- [ ] Trimmed, scannable Discord alert formatting
- [ ] Full CRUD (create/delete endpoints)
- [ ] LangGraph orchestration — AI *inside* the decision logic
