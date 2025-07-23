import requests
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

DB_USER = "root"
DB_PASSWORD = "yourpassword"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "ecommerce"

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"


DB_SCHEMA = """
Database: ecommerce

Tables:
1. product_total_sales_metrics
    - date
    - item_id
    - total_sales
    - total_units_ordered

2. product_ad_sales_metrics
    - date
    - item_id
    - ad_sales
    - impressions
    - ad_spend
    - clicks
    - units_sold

3. product_eligibility
    - eligibility_datetime_utc
    - item_id
    - eligibility (string: 'TRUE' or 'FALSE')
    - message
"""

def ask_llm(question: str) -> str | None:
    """
    Send question & schema to Llama3 and get SQL query.
    """
    prompt = f"""
You are a professional SQL generator.

Given this MySQL schema:
{DB_SCHEMA}

Rules:
- Only use the tables and columns exactly as defined above.
- Do not invent any columns or tables.
- If asked for CPC (Cost Per Click), compute it as: ad_spend / clicks.
- If asked for ROAS (Return on Ad Spend), compute it as: ad_sales / ad_spend.
- If asked for a product with highest CPC, return the item_id with maximum CPC.
- Always write a valid MySQL SELECT statement.

Only output the SQL query. Do NOT explain it or wrap it in markdown.

Question: {question}

SQL:
"""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        sql = data.get("response", "").strip()

        # Cleanup if needed
        sql = sql.replace("```sql", "").replace("```", "").strip()

        if not sql.lower().startswith("select"):
            print("LLM did not generate a valid SELECT query.")
            return None

        return sql

    except Exception as e:
        print(f"Error communicating with LLM: {e}")
        return None


def execute_sql(sql: str) -> str:
    """
    Execute SQL and return formatted result.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            if not rows:
                return "No results found."
            output = []
            for row in rows:
                output.append(", ".join(str(col) for col in row))
            return "\n".join(output)
    except SQLAlchemyError as e:
        return f"SQL Execution error: {e}"


def run_agent():
    """
    Main loop to ask → generate SQL → execute → answer.
    """
    while True:
        question = input("\nEnter your question (or type 'exit' to quit): ").strip()
        if question.lower() in ["exit", "quit"]:
            print("Goodbye.")
            break

        sql = ask_llm(question)
        if sql:
            print(f"\nGenerated SQL:\n{sql}")
            answer = execute_sql(sql)
            print(f"\nAnswer:\n{answer}")
        else:
            print("Failed to generate a valid SQL query.")


if __name__ == "__main__":
    run_agent()
