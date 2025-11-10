from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, Response
import requests
import os

app = FastAPI()

SUPABASE_URL = "https://ioxmssaxiqqvhqowrxwi.supabase.co"
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
TABLE_NAME = "Data"

@app.get("/")
async def receive_get(confirmationToken: str = Query(None)):
    # --- AWS confirmation ---
    if confirmationToken:
        print(f"✅ Received AWS confirmation token: {confirmationToken}")
        return Response(status_code=200)
    
    return Response(status_code=400)

@app.post("/")
async def receive_post(request: Request):
    # --- IoT message ---
    data = await request.json()
    print("📩 Raw IoT payload:", data)

    # Extract your actual data (inside 'message')
    payload = data.get("message", data)  # fallback if no wrapper
    print("📦 Cleaned payload to send:", payload)

    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    try:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}", headers=headers, json=payload)
        print("➡️ Supabase response:", r.status_code, r.text)
        return JSONResponse({"status": "ok", "supabase_status": r.status_code}, status_code=200)
    except Exception as e:
        print("❌ Error:", e)
        return JSONResponse({"error": str(e)}, status_code=500)
