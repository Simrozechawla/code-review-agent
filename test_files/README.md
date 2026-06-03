# LLM Code Review Agent

An AI-powered Python code reviewer built with Claude API and FastAPI.
Paste any Python file and get a structured review with line numbers,
severity ratings, and concrete fixes.

## How it works

1. Static analyser reads the file using Python's AST module —
   extracts function names, line numbers, missing docstrings, unused imports
2. That structured analysis plus the raw code is sent to Claude API
3. Claude returns a JSON review with per-issue severity and fix suggestions
4. Results display as a colour-coded table in the terminal

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/code-review-agent
cd code-review-agent
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create a `.env` file with your Anthropic API key:
ANTHROPIC_API_KEY=sk-ant-your-key-here

## Usage

### CLI
```bash
python reviewer.py path/to/your_file.py
python reviewer.py path/to/your_file.py --save output.json
```

### API
```bash
python api.py
```
Then open `http://localhost:8000/docs` to test in browser.

## Tech stack

- Claude API (Anthropic) — LLM inference
- Python AST module — static code analysis
- FastAPI — REST API layer
- Rich — terminal formatting
- Pydantic — request validation