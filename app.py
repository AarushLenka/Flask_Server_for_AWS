from flask import Flask, request, jsonify
from supabase import create_client
import os

# --- Flask setup ---
app = Flask(__name__)

# --- Supabase setup ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "Data")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route("/", methods=["GET"])
def home():
    return "✅ Flask AWS IoT Hook active", 200


@app.route("/aws-hook", methods=["POST"])
def aws_hook():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Empty or invalid JSON"}), 400

        # Log payload for debug
        print("📩 Received payload:", data)

        # Flatten if message came inside another key like 'message'
        if "timestamp" not in data and "message" in data:
            data = data["message"]

        # Expected payload structure from your ESP32 → AWS IoT Core
        # {
        #   "timestamp": 1730640000000,
        #   "temperature_c": 36.8,
        #   "spo2": 98.1,
        #   "hr": 76.4,
        #   "spo2_valid": 1,
        #   "hr_valid": 1,
        #   "ecg": [0.82, 0.84, 0.85, 0.81]
        # }

        required = [
            "temperature_c", "spo2_valid", "hr_valid", "ecg"
        ]
        for key in required:
            if key not in data:
                return jsonify({"error": f"Missing field: {key}"}), 400

        # Insert directly into Supabase
        response = supabase.table(SUPABASE_TABLE).insert({
            "temperature_c": data["temperature_c"],
            "spo2_valid": data["spo2_valid"],
            "hr_valid": data["hr_valid"],
            "ecg": data["ecg"]
        }).execute()

        if response.data:
            print("✅ Supabase insert success:", response.data)
            return jsonify({"status": "success", "data": response.data}), 200
        else:
            print("⚠️ Supabase insert failed:", response)
            return jsonify({"error": "Insert failed"}), 500

    except Exception as e:
        print("❌ Exception:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
