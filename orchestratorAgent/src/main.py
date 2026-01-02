"""Main entry point for the Orchestrator Agent."""

from dotenv import load_dotenv

# Load environment variables before importing anything else
load_dotenv()

from src.api.app import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
