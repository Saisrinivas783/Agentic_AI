# app.py

from fastapi import FastAPI
from schemas.api import InvocationRequest, InvocationResponse
from agent import OrchestratorAgent

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Orchestrator Agent", version="0.1")

# Create a single agent instance (loads registry + compiles graph once)
agent = OrchestratorAgent(registry_path="registry/tools-config.yaml")


@app.get("/ping")
def ping():
    return {"status": "ok"}


@app.post("/invocations", response_model=InvocationResponse)
def invocations(payload: InvocationRequest):
    return agent.handle_invocation(payload)
