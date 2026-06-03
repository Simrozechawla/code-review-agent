import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from analyzer import analyze_code, format_analysis_for_prompt
from reviewer import call_ollama

load_dotenv()

app = FastAPI(title="Code Review Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CodePayload(BaseModel):
    code: str
    filename: str = "submitted_code.py"


@app.get("/")
def root():
    return {
        "service": "Code Review Agent",
        "status": "running",
        "model": os.getenv("OLLAMA_MODEL", "llama3.2")
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
        "backend": "ollama (local)"
    }


@app.post("/review")
def review_code(payload: CodePayload):
    if not payload.code.strip():
        raise HTTPException(
            status_code=400,
            detail="Code cannot be empty"
        )
    if len(payload.code) > 50_000:
        raise HTTPException(
            status_code=400,
            detail="File too large. Max 50,000 characters."
        )

    analysis = analyze_code(payload.code)
    report = format_analysis_for_prompt(analysis, payload.code)

    try:
        review = call_ollama(payload.code, report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "filename": payload.filename,
        "score": review.get("score"),
        "summary": review.get("summary"),
        "issues": review.get("issues", []),
        "positives": review.get("positives", []),
        "recommended_next_steps": review.get("recommended_next_steps", []),
        "static_issues": analysis.get("issues_detected", [])
    }


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)