# =========================================================
# AI PMO CONTROL TOWER — BACKEND (main.py)
# Fully commented version for learning purposes
# =========================================================

# --- FastAPI: the web framework that turns our Python functions into API endpoints ---
from fastapi import FastAPI

# --- CORS middleware: lets a browser-based frontend (like React) call this API ---
# Without this, browsers block requests from a different "origin" (domain/port) by default.
from fastapi.middleware.cors import CORSMiddleware

# --- pandas: used to load and query our CSV files like little databases ---
import pandas as pd

# --- os: used to build file paths that work regardless of which machine/OS runs this ---
import os

# --- LangChain's Ollama wrapper: lets us "talk" to a local LLM (e.g. llama3.2) running via Ollama ---
from langchain_ollama import OllamaLLM

# --- chromadb: a local vector database we use to remember past AI advisor responses ---
import chromadb

# --- datetime: used to timestamp each piece of memory we save ---
from datetime import datetime


# =========================================================
# APP SETUP
# =========================================================

# Create the FastAPI application object. "title" just shows up in the auto-generated docs.
app = FastAPI(title="AI PMO Control Tower API")

# Add CORS middleware so a frontend (e.g. React running on a different port) can call this API.
# allow_origins=["*"] means "allow requests from any website" — fine for local development,
# but you'd lock this down to your actual frontend's URL before deploying publicly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATA LOADING
# =========================================================

# BASE_DIR = the folder this file (main.py) lives in.
# Using this instead of a hardcoded path means the code works no matter where the project
# folder is located on disk (your machine, a teammate's machine, a server, etc.).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Build full paths to the CSV files, which live one folder up, inside "data/".
TASKS_PATH = os.path.join(BASE_DIR, "../data/tasks.csv")
RESOURCES_PATH = os.path.join(BASE_DIR, "../data/resources.csv")

# Load both CSVs into pandas DataFrames (table-like objects) when the app starts.
# NOTE: this means the data is loaded ONCE at startup — if you edit the CSV files while
# the server is running, you won't see the changes until you restart the server.
tasks = pd.read_csv(TASKS_PATH)
resources = pd.read_csv(RESOURCES_PATH)


# =========================================================
# AI MODEL SETUP
# =========================================================

# Create a connection to the local LLM running through Ollama.
# "llama3.2" must match a model you've already pulled via `ollama pull llama3.2`.
# This object is what we call later to generate text (llm.invoke(...)).
llm = OllamaLLM(model="llama3.2")


# =========================================================
# MEMORY SETUP (Chroma)
# =========================================================

# Create a persistent Chroma client. "Persistent" means the data is saved to disk
# (inside data/chroma_memory) so it survives server restarts — unlike an in-memory-only DB.
chroma_client = chromadb.PersistentClient(
    path=os.path.join(BASE_DIR, "../data/chroma_memory")
)

# Get (or create, if it doesn't exist yet) a "collection" — think of this like a table
# specifically for storing past advisor runs (the AI's recommendations over time).
memory_collection = chroma_client.get_or_create_collection(name="advisor_history")


# =========================================================
# BASIC ROUTES
# =========================================================

# A simple "is it alive" endpoint. Visiting http://127.0.0.1:8000/ should show this message.
@app.get("/")
def home():
    return {"message": "AI PMO Control Tower running"}


# Returns every row of tasks.csv as JSON.
# .to_dict(orient="records") converts the DataFrame into a list of dictionaries,
# e.g. [{"task_id": 1, "task_name": "Define scope", ...}, {...}, ...]
@app.get("/tasks")
def get_tasks():
    return tasks.to_dict(orient="records")


# Same idea, but for resources.csv.
@app.get("/resources")
def get_resources():
    return resources.to_dict(orient="records")


# =========================================================
# HEALTH SCORE ENGINE
# =========================================================

# This is plain Python/pandas logic — NOT AI. It just counts problems and subtracts points.
def calculate_health():
    # Filter tasks down to only rows where progress is less than 100 (i.e. not finished).
    overdue = tasks[tasks["progress"] < 100]

    # Filter resources down to only rows where allocated hours exceed their capacity.
    overloaded = resources[resources["allocated"] > resources["capacity"]]

    # Start from a perfect score and subtract points for each problem found.
    score = 100
    score -= len(overdue) * 10       # -10 points per unfinished task
    score -= len(overloaded) * 15    # -15 points per overloaded resource

    # Never let the score go below 0.
    return max(score, 0)


# Endpoint that exposes the health score calculation above as JSON.
@app.get("/health")
def health():
    return {"health_score": calculate_health()}


# =========================================================
# RISK ENGINE
# =========================================================

# Also plain logic — flags risk categories based on the same filters as above.
def detect_risks():
    risks_list = []

    overdue = tasks[tasks["progress"] < 100]
    overloaded = resources[resources["allocated"] > resources["capacity"]]

    # .empty is True if the filtered table has zero rows.
    # So "not overdue.empty" means "there IS at least one overdue task".
    if not overdue.empty:
        risks_list.append("Tasks are delayed")
    if not overloaded.empty:
        risks_list.append("Resources are overloaded")

    return risks_list


@app.get("/risks")
def risks():
    return detect_risks()


# =========================================================
# AI ADVISOR ENDPOINT
# =========================================================

@app.get("/advisor")
def advisor():
    # --- Step 1: Gather real findings from our own (non-AI) logic ---
    score = calculate_health()
    active_risks = detect_risks()

    # =========================================================
    # NEW — Step 1.5: RETRIEVE past recommendations (the RAG read step)
    # =========================================================
    # We build a short text description of the CURRENT situation, then ask Chroma
    # to find the past recommendations most SIMILAR IN MEANING to it.
    # Chroma embeds this query string automatically and compares it against the
    # embeddings of everything we've stored — returning the closest matches.
    # This is the "retrieval" in Retrieval-Augmented Generation.
    current_situation = f"Health score {score}. Risks: {active_risks}"

    # Ask Chroma for the 2 most semantically similar past entries.
    # n_results=2 keeps the prompt short; raise it once you have more history.
    past = memory_collection.query(
        query_texts=[current_situation],
        n_results=2
    )

    # Chroma returns results in a nested structure: documents is a list-of-lists
    # (one inner list per query — we only sent one query, so we want past["documents"][0]).
    # On the very first run the DB is empty, so guard against that.
    retrieved_docs = past["documents"][0] if past["documents"] else []

    # Turn the retrieved past recommendations into a readable block for the prompt.
    # If there's no history yet, say so plainly so the AI doesn't hallucinate a past.
    if retrieved_docs:
        history_context = "\n\n".join(
            f"- Previous recommendation: {doc}" for doc in retrieved_docs
        )
    else:
        history_context = "No previous recommendations on record (this is the first analysis)."

    # --- Step 2: Build the prompt — NOW AUGMENTED with retrieved history ---
    # This is the "augmented" in RAG: the retrieved context is injected into the prompt.
    prompt = f"""
    You are an expert AI PMO Assistant (Project Management Office).

    CURRENT project metrics:
    - Overall Project Health Score: {score}/100
    - Identified Risks: {active_risks}

    RELEVANT PAST RECOMMENDATIONS (retrieved from memory):
    {history_context}

    Using both the current metrics AND the past recommendations above:
    1. A quick assessment of the current state.
    2. Whether the situation appears to have improved, stayed the same, or worsened
       compared to the past recommendations — and what that implies (e.g. if the same
       risk keeps appearing, earlier advice may not have been acted on).
    3. Concrete, step-by-step actions to take immediately.

    Keep the response concise, realistic, and highly practical.
    """

    # --- Step 3: Send the augmented prompt to the local LLM ---
    response = llm.invoke(prompt)

    # --- Step 4: Save this run into Chroma (the write step — unchanged) ---
    memory_collection.add(
        documents=[response],
        metadatas=[{
            "health_score": score,
            "risks": str(active_risks),
            "timestamp": datetime.now().isoformat()
        }],
        ids=[f"advisor_{datetime.now().timestamp()}"]
    )

    # --- Step 5: Return everything (now including what we retrieved, for transparency) ---
    return {
        "health_score": score,
        "risks": active_risks,
        "recommendation": response,
        "retrieved_past_count": len(retrieved_docs)  # NEW — proves retrieval ran
    }


# =========================================================
# DEPENDENCY ENGINE
# =========================================================

@app.get("/dependencies")
def dependencies():
    # Keep only tasks that actually have a dependency listed (not blank/NaN).
    dependent_tasks = tasks[tasks["dependency"].notna()]

    blocked = []

    # Loop through each task that has a dependency.
    # "_" means we don't care about the row's index number, only its contents (row).
    for _, row in dependent_tasks.iterrows():
        dep_id = row["dependency"]

        # Find the row for the task THIS task depends on.
        dep_task = tasks[tasks["task_id"] == dep_id]

        # If that dependency task exists AND isn't finished yet (progress < 100),
        # then the current task is considered "blocked".
        if not dep_task.empty and dep_task.iloc[0]["progress"] < 100:
            blocked.append({
                # int()/str() wrap numpy types into plain Python types so FastAPI
                # can convert them to JSON without errors.
                "task_id": int(row["task_id"]),
                "task_name": str(row["task_name"]),
                "blocked_by": str(dep_task.iloc[0]["task_name"]),
                "blocked_by_progress": int(dep_task.iloc[0]["progress"])
            })

    return {"blocked_tasks": blocked}