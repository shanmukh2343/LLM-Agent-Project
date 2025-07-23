from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import get_db
from app.llm_interface import ask_llm

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    return FileResponse("static/index.html")


class QuestionRequest(BaseModel):
    question: str


@app.post("/ask")
def ask_question(request: QuestionRequest, db: Session = Depends(get_db)):
    """
    Accepts a natural language question, sends it to LLM to generate SQL,
    executes SQL, and returns the result.
    """
    question = request.question
    sql_query = ask_llm(question)

    if not sql_query:
        return JSONResponse(content={
            "question": question,
            "sql": "",
            "answer": "Failed to generate SQL for your question."
        })

    try:
        result = db.execute(text(sql_query)).fetchall()
        if not result:
            answer = "No data found."
        else:
            answer = "\n".join(str(row) for row in result)

        return {
            "question": question,
            "sql": sql_query,
            "answer": answer
        }

    except Exception as e:
        return {
            "question": question,
            "sql": sql_query,
            "answer": f"Error executing SQL: {e}"
        }


@app.post("/chart")
def chart_question(request: QuestionRequest, db: Session = Depends(get_db)):
    """
    Similar to /ask but formats data to support frontend charts.
    It assumes the SQL returns 2 columns: label, value
    """
    question = request.question
    sql_query = ask_llm(question)

    if not sql_query:
        return {
            "question": question,
            "sql": "",
            "labels": [],
            "values": [],
            "error": "Failed to generate SQL for your question."
        }

    try:
        result = db.execute(text(sql_query)).fetchall()
        if not result:
            return {
                "question": question,
                "sql": sql_query,
                "labels": [],
                "values": [],
                "error": "No data found."
            }

        labels, values = zip(*result)

        return {
            "question": question,
            "sql": sql_query,
            "labels": list(labels),
            "values": list(values)
        }

    except Exception as e:
        return {
            "question": question,
            "sql": sql_query,
            "labels": [],
            "values": [],
            "error": f"Error executing SQL: {e}"
        }
