from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

# Import the modern LangChain Ollama library
from langchain_ollama import OllamaLLM

app = FastAPI(title="AI PMO Control Tower API")

# Allow your future React frontend to talk to this backend safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Relative paths to your CSV data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_PATH = os.path.join(BASE_DIR, "../data/tasks.csv")
RESOURCES_PATH = os.path.join(BASE_DIR, "../data/resources.csv")

# Load data safely
tasks = pd.read_csv(TASKS_PATH)
resources = pd.read_csv(RESOURCES_PATH)

# Initialize your local AI model (using the llama3.2 model you downloaded)
# Note: If you downloaded a different model, change the string below!
llm = OllamaLLM(model="llama3.2")

@app.get("/")
def home():
    return {"message": "AI PMO Control Tower running"}

@app.get("/tasks")
def get_tasks():
    return tasks.to_dict(orient="records")

@app.get("/resources")
def get_resources():
    return resources.to_dict(orient="records")

def calculate_health():
    overdue = tasks[tasks["progress"] < 100]
    overloaded = resources[resources["allocated"] > resources["capacity"]]
    
    score = 100
    score -= len(overdue) * 10
    score -= len(overloaded) * 15
    return max(score, 0)

@app.get("/health")
def health():
    return {"health_score": calculate_health()}

def detect_risks():
    risks_list = []
    overdue = tasks[tasks["progress"] < 100]
    overloaded = resources[resources["allocated"] > resources["capacity"]]
    
    if not overdue.empty:
        risks_list.append("Tasks are delayed")
    if not overloaded.empty:
        risks_list.append("Resources are overloaded")
    return risks_list

@app.get("/risks")
def risks():
    return detect_risks()

# === NEW: AI ADVISOR ENDPOINT ===
@app.get("/advisor")
def advisor():
    # 1. Gather current live data from our calculation engines
    score = calculate_health()
    active_risks = detect_risks()
    
    # 2. Design the prompt for our local AI
    prompt = f"""
    You are an expert AI PMO Assistant (Project Management Office).
    
    Analyze the following project metrics:
    - Overall Project Health Score: {score}/100
    - Identified Risks: {active_risks}
    
    Provide a professional, brief, and actionable project summary for the Project Manager.
    Include:
    1. A quick assessment of the current state ("What is happening and why")
    2. Concrete, step-by-step actions they should take immediately to resolve the resource overload and task delays.
    
    Keep the response concise, realistic, and highly practical.
    """
    
    # 3. Ask the local LLM to think and return its answer
    response = llm.invoke(prompt)
    
    return {
        "health_score": score,
        "risks": active_risks,
        "recommendation": response
    }

@app.get("/dependencies")
def dependencies():
    dependent_tasks = tasks[tasks["dependency"].notna()]
    
    blocked = []
    for _, row in dependent_tasks.iterrows():
        dep_id = row["dependency"]
        dep_task = tasks[tasks["task_id"] == dep_id]
        if not dep_task.empty and dep_task.iloc[0]["progress"] < 100:
            blocked.append({
                "task_id": int(row["task_id"]),
                "task_name": str(row["task_name"]),
                "blocked_by": str(dep_task.iloc[0]["task_name"]),
                "blocked_by_progress": int(dep_task.iloc[0]["progress"])
            })
    return {"blocked_tasks": blocked}
