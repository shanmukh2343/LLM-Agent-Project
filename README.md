# AI Data Agent

## Description
A local agent that uses Llama3 via Ollama to generate SQL queries for MySQL and visualize the answers.

## Setup
- Install Ollama & pull `llama3`.
- Start Ollama:
  ollama serve
- Create `.env` with DB credentials.
- Install dependencies:
  pip install -r requirements.txt
- Start API:
  uvicorn app.api:app --reload
- Visit: http://127.0.0.1:8000