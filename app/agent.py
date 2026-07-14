"""
The agentic core of Melt Risk.

This is NOT a single "send question to LLM, get answer" call. It is a proper
agent LOOP:
  1. PLAN   - the LLM decides which tool(s) it needs (or that it can answer directly)
  2. ACT    - we execute the chosen tool(s) in Python against DuckDB
  3. OBSERVE - tool results are fed back to the LLM
  4. RESPOND - the LLM produces a final natural-language answer, grounded in real data

Tools exposed to the agent:
  - run_sql_query: lets the agent write and execute its own SQL against the warehouse
  - get_melt_risk_shipments: pre-built tool for "what's at risk of melting" questions
  - get_understocked_products: pre-built tool for stock-out risk
  - simple_demand_forecast: naive moving-average forecast tool (no ML infra needed,
    but demonstrates the agent choosing a *computation* tool, not just SQL)

Model: Groq's llama-3.3-70b-versatile - free tier, OpenAI-compatible tool-calling API.
"""
import os
import json
import duckdb
from groq import Groq

DB_PATH = os.environ.get(
    "MELT_RISK_DB_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "warehouse.duckdb")),
)
MODEL = "llama-3.3-70b-versatile"

# ---------- Tool implementations ----------

def run_sql_query(sql: str) -> str:
    """Execute a read-only SQL query against the warehouse and return results as JSON."""
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        df = con.execute(sql).fetchdf()
        return df.head(50).to_json(orient="records")
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        con.close()


def get_melt_risk_shipments(risk_level: str = "HIGH") -> str:
    """Get shipments at a given melt-risk level. risk_level can be LOW, MEDIUM, HIGH, or CRITICAL."""
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        df = con.execute(f"""
            select warehouse_name, product_name,
                   strftime(ship_date, '%Y-%m-%d') as ship_date, delay_hours,
                   melt_tolerance_hours, melt_risk_level, shipment_value
            from mart_melt_risk_shipments
            where melt_risk_level ilike '{risk_level}%'
            order by shipment_value desc
            limit 20
        """).fetchdf()
        return df.to_json(orient="records")
    finally:
        con.close()


def get_understocked_products() -> str:
    """Get products/warehouses currently understocked or with cold-chain issues."""
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        df = con.execute("""
            select warehouse_name, product_name, stock_on_hand, reorder_point,
                   freezer_temp_c, inventory_status
            from mart_inventory_health
            where inventory_status != 'OK'
            order by inventory_status, stock_on_hand asc
            limit 20
        """).fetchdf()
        return df.to_json(orient="records")
    finally:
        con.close()


def simple_demand_forecast(product_id: str, warehouse_id: str) -> str:
    """Naive 14-day moving average forecast for a product at a warehouse."""
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        df = con.execute(f"""
            select order_date, total_units_ordered
            from mart_demand_trends
            where product_id = '{product_id}' and warehouse_id = '{warehouse_id}'
            order by order_date desc
            limit 14
        """).fetchdf()
        if df.empty:
            return json.dumps({"error": "no data for this product/warehouse combination"})
        avg = float(df["total_units_ordered"].mean())
        return json.dumps({
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "last_14_day_avg_daily_demand": round(avg, 1),
            "simple_forecast_next_7_days_total": round(avg * 7, 0),
        })
    finally:
        con.close()


TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "run_sql_query",
            "description": "Run a read-only SQL query against the DuckDB warehouse. Tables available: stg_products, stg_warehouses, stg_orders, stg_inventory, stg_shipments, mart_melt_risk_shipments, mart_inventory_health, mart_demand_trends. Use this for any question not covered by the other specific tools.",
            "parameters": {
                "type": "object",
                "properties": {"sql": {"type": "string", "description": "A valid DuckDB SQL SELECT query."}},
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_melt_risk_shipments",
            "description": "Get shipments at risk of melting/spoiling due to transit delays or refrigeration failure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"], "description": "Minimum risk level to filter for."}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_understocked_products",
            "description": "Get products/warehouses that are understocked or have cold-chain (freezer temperature) issues right now.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "simple_demand_forecast",
            "description": "Get a simple 7-day demand forecast for a specific product at a specific warehouse, based on trailing 14-day average.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "e.g. IC001"},
                    "warehouse_id": {"type": "string", "description": "e.g. CW01"},
                },
                "required": ["product_id", "warehouse_id"],
            },
        },
    },
]

AVAILABLE_FUNCTIONS = {
    "run_sql_query": run_sql_query,
    "get_melt_risk_shipments": get_melt_risk_shipments,
    "get_understocked_products": get_understocked_products,
    "simple_demand_forecast": simple_demand_forecast,
}

SYSTEM_PROMPT = """You are "Melt Risk Agent", a supply chain analyst for an ice cream cold-chain
distribution business. You have access to real data via tools: product catalog, cold-storage
warehouses, daily demand, current inventory (with freezer temps), and shipments (with transit
delays and refrigeration failure flags).

Always use a tool to get real data before answering factual questions - never guess numbers.
When you get results back, explain them in clear, business-friendly language (not raw JSON).
If something looks risky (melt risk, stock-out, warm freezer), call it out clearly and suggest
a concrete action. Keep answers concise and practical, like a sharp analyst briefing a manager.
"""


def run_agent(user_message: str, history: list[dict]) -> tuple[str, list[dict]]:
    """
    Runs one turn of the agent loop. Returns (final_answer, updated_history).
    history is a list of {"role": ..., "content": ...} dicts (excluding system prompt).
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set. Get a free key at https://console.groq.com/keys")

    client = Groq(api_key=api_key)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [
        {"role": "user", "content": user_message}
    ]

    # --- PLAN + ACT loop (max 4 hops to avoid infinite tool loops) ---
    for _ in range(4):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS_SPEC,
            tool_choice="auto",
            temperature=0.2,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            # RESPOND - agent decided it has enough info
            final_text = msg.content
            updated_history = history + [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": final_text},
            ]
            return final_text, updated_history

        # ACT - execute every requested tool call
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
        })
        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments or "{}")
            if fn_args is None:
                fn_args = {}
            fn = AVAILABLE_FUNCTIONS.get(fn_name)
            result = fn(**fn_args) if fn else json.dumps({"error": f"unknown tool {fn_name}"})
            # OBSERVE - feed tool result back into the conversation
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": fn_name,
                "content": result,
            })

    # Safety fallback if the loop didn't converge
    fallback = "I gathered some data but couldn't finalize an answer - could you rephrase your question?"
    return fallback, history + [{"role": "user", "content": user_message}, {"role": "assistant", "content": fallback}]
