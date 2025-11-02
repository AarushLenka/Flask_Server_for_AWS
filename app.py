from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

SUPABASE_URL = "https://ioxmssaxiqqvhqowrxwi.supabase.co"
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
TABLE_NAME = "Data"

@app.route("/", methods=["GET", "POST"])
def receive():
    # --- AWS confirmation ---
    if request.method == "GET" and "confirmationToken" in request.args:
        token = request.args.get("confirmationToken")
        print(f"✅ Received AWS confirmation token: {token}")
        return "", 200

    # --- IoT message ---
    if request.method == "POST":
        data = request.get_json(force=True)
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
            return jsonify({"status": "ok", "supabase_status": r.status_code}), 200
        except Exception as e:
            print("❌ Error:", e)
            return jsonify({"error": str(e)}), 500

    return "", 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
