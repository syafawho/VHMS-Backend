from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import sqlite3
import datetime
import csv
import io
import os

app = Flask(__name__)
CORS(app, origins=["https://up2242015-finalproject.netlify.app"])

# Path to SQLite database
DB_PATH = os.path.join(os.path.dirname(__file__), "vehicle_data.db")

# In-memory log for real-time data
in_memory_log = []

# Initialize the database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS data_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        flame REAL NOT NULL,
        smoke REAL NOT NULL,
        distance REAL NOT NULL,
        acc_x REAL NOT NULL,
        acc_y REAL NOT NULL,
        acc_z REAL NOT NULL
    )
    """)
    conn.commit()
    conn.close()

# Call the function to initialize the database
init_db()

# API to receive data from ESP32
@app.route("/api/data", methods=["POST"])
def receive_data():
    data = request.get_json()

    # Add timestamp to the data
    data_with_timestamp = {
        "timestamp": datetime.datetime.now().isoformat(),
        **data
    }

    # Store in in-memory log (keep only the last 10 entries for efficiency)
    in_memory_log.append(data_with_timestamp)
    if len(in_memory_log) > 10:
        in_memory_log.pop(0)

    # Also write to SQLite for persistent storage
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO data_log (timestamp, latitude, longitude, flame, smoke, distance, acc_x, acc_y, acc_z)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data_with_timestamp["timestamp"],
        data_with_timestamp.get("latitude", 0),
        data_with_timestamp.get("longitude", 0),
        data_with_timestamp.get("flame", 0),
        data_with_timestamp.get("smoke", 0),
        data_with_timestamp.get("distance", 0),
        data_with_timestamp.get("acc_x", 0),
        data_with_timestamp.get("acc_y", 0),
        data_with_timestamp.get("acc_z", 0)
    ))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "received": data_with_timestamp}), 200

# API to fetch the latest data from in-memory log
@app.route("/api/latest", methods=["GET"])
def get_latest():
    if in_memory_log:
        return jsonify(in_memory_log[-1]), 200
    else:
        return jsonify({"message": "No data found"}), 404

# API to retrieve all logs from SQLite for CSV download
@app.route("/api/download_csv", methods=["GET"])
def download_csv():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data_log ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()

    # Prepare CSV data
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp", "Latitude", "Longitude", "Flame", "Smoke", "Distance", "Acc X", "Acc Y", "Acc Z"])
    writer.writerows(rows)

    # Move to the beginning of the StringIO object
    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=historical_data.csv"}
    )

@app.route("/")
def home():
    return "ESP32 Flask Backend with In-Memory Log and SQLite!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
