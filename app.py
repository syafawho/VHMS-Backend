from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import datetime
import csv
import io  # For in-memory file handling

app = Flask(__name__)
#CORS(app, origins=["https://up2242015-finalproject.netlify.app"])
CORS(app)

# In-memory storage (can replace with database later)
data_log = []

# Default route to check server status
@app.route("/")
def home():
    return "ESP32 Flask Backend is running!"

# API endpoint to receive data from ESP32
@app.route("/api/data", methods=["POST"])
def receive_data():
    # Parse the incoming JSON payload
    data = request.get_json()

    # Log received data to console
    print(f"[{datetime.datetime.now()}] Received Data: {data}")

    # Add timestamp to the received data
    data_with_timestamp = {
        "timestamp": datetime.datetime.now().isoformat(),
        **data
    }

    # Store in in-memory log (you can later store in a file or database)
    data_log.append(data_with_timestamp)

    # Send a response back to the ESP32
    return jsonify({
        "status": "success",
        "message": "Data received!",
        "received": data_with_timestamp
    }), 200

# API endpoint to retrieve the data log (for debugging or front-end)
@app.route("/api/log", methods=["GET"])
def get_log():
    return jsonify(data_log), 200

# API endpoint to download the data log as CSV
@app.route("/api/download_csv", methods=["GET"])
def download_csv():
    # Create an in-memory file
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["timestamp"] + list(data_log[0].keys() if data_log else []))
    
    # Write header and rows
    writer.writeheader()
    writer.writerows(data_log)

    # Prepare the response
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=historical_data.csv"}
    )

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
