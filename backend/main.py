from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

app = FastAPI(title="AI PMO Control Tower API")

# CRITICAL FOR WEEK 3: This allows your React frontend to talk to your backend safely
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
    # Overdue tasks = anything not 100% complete
    overdue = tasks[tasks["progress"] < 100]
    # Overloaded resources = allocated hours exceed capacity hours
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