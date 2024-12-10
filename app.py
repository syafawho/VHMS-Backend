from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import datetime
import sqlite3
import csv
import os

app = Flask(__name__)

# Update CORS to allow only your Netlify frontend
CORS(app, origins=["https://your-netlify-url.netlify.app"])

# Path to SQLite database (absolute path for deployment)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vehicle_data.db")

# Initialize the database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
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
    print(f"[{datetime.datetime.now()}] Received Data: {data}")

    data_with_timestamp = {
        "timestamp": datetime.datetime.now().isoformat(),
        **data
    }

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

    return jsonify({
        "status": "success",
        "message": "Data received and saved to database!",
        "received": data_with_timestamp
    }), 200

# API to retrieve data logs
@app.route("/api/log", methods=["GET"])
def get_log():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data_log ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()

    data = [
        {
            "id": row[0],
            "timestamp": row[1],
            "latitude": row[2],
            "longitude": row[3],
            "flame": row[4],
            "smoke": row[5],
            "distance": row[6],
            "acc_x": row[7],
            "acc_y": row[8],
            "acc_z": row[9]
        } for row in rows
    ]
    return jsonify(data), 200

# API to download logs as a CSV
@app.route("/api/download_csv", methods=["GET"])
def download_csv():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data_log ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()

    # Prepare CSV data
    output = [["ID", "Timestamp", "Latitude", "Longitude", "Flame", "Smoke", "Distance", "Acc X", "Acc Y", "Acc Z"]]
    output.extend(rows)

    # Convert to CSV format
    csv_data = "\n".join([",".join(map(str, row)) for row in output])

    # Return as a file
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=historical_data.csv"}
    )

@app.route("/")
def home():
    return "ESP32 Flask Backend with SQLite is running!"

if __name__ == "__main__":
    app.run(debug=True)
