from flask import Flask, render_template, request, jsonify
import requests
import sqlite3
import os
import joblib
from datetime import datetime
from dotenv import load_dotenv

# =========================================================
# FLASK CONFIGURATION
# =========================================================

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_NAME = os.path.join(BASE_DIR, "weather.db")

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "weather_model.pkl"
)

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv(
    os.path.join(BASE_DIR, ".env")
)

API_KEY = os.getenv("OPENWEATHER_API_KEY")

print("=" * 60)
print("WEATHER FORECASTING SYSTEM")
print("=" * 60)

print("API KEY FOUND:", bool(API_KEY))
print("API KEY LENGTH:", len(API_KEY) if API_KEY else 0)

# =========================================================
# DATABASE
# =========================================================

def init_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            pressure REAL,
            wind_speed REAL,
            description TEXT,
            searched_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# SAVE WEATHER
# =========================================================

def save_weather(
    city,
    temperature,
    humidity,
    pressure,
    wind_speed,
    description
):

    try:

        conn = sqlite3.connect(DB_NAME)

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO searches
            (
                city,
                temperature,
                humidity,
                pressure,
                wind_speed,
                description,
                searched_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            city,
            temperature,
            humidity,
            pressure,
            wind_speed,
            description,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))

        conn.commit()
        conn.close()

    except Exception as e:

        print("DATABASE SAVE ERROR:", e)


# =========================================================
# LOAD ML MODEL
# =========================================================

model = None

if os.path.exists(MODEL_PATH):

    try:

        model = joblib.load(MODEL_PATH)

        print("ML MODEL: LOADED")

    except Exception as e:

        print("ML MODEL ERROR:", e)

else:

    print("ML MODEL: NOT FOUND")
    print("Expected:")
    print(MODEL_PATH)
    print("Run: python train_model.py")


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return render_template("index.html")


# =========================================================
# WEATHER API
# =========================================================

@app.route("/weather")
def weather():

    city = request.args.get("city", "").strip()

    if not city:

        return jsonify({
            "error": "Please enter a city name."
        }), 400

    if not API_KEY:

        return jsonify({
            "error": "OpenWeather API key is missing."
        }), 500

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        print(
            "WEATHER API:",
            response.status_code,
            city
        )

        # Invalid API key
        if response.status_code == 401:

            return jsonify({
                "error": "Invalid OpenWeather API key."
            }), 401

        # City not found
        if response.status_code == 404:

            return jsonify({
                "error": "City not found."
            }), 404

        response.raise_for_status()

        data = response.json()

        weather_data = {

            "city": data.get("name"),

            "country": data.get(
                "sys",
                {}
            ).get("country", ""),

            "temperature": round(
                data["main"]["temp"],
                1
            ),

            "feels_like": round(
                data["main"]["feels_like"],
                1
            ),

            "humidity": data["main"]["humidity"],

            "pressure": data["main"]["pressure"],

            "wind_speed": data["wind"]["speed"],

            "description": data["weather"][0]["description"],

            "icon": data["weather"][0]["icon"]

        }

        # Save to database
        save_weather(
            weather_data["city"],
            weather_data["temperature"],
            weather_data["humidity"],
            weather_data["pressure"],
            weather_data["wind_speed"],
            weather_data["description"]
        )

        return jsonify(weather_data)

    except requests.exceptions.Timeout:

        return jsonify({
            "error": "Weather server took too long to respond."
        }), 504

    except requests.exceptions.ConnectionError:

        return jsonify({
            "error": "Unable to connect to OpenWeather."
        }), 503

    except requests.exceptions.RequestException as e:

        print("REQUEST ERROR:", e)

        return jsonify({
            "error": "Unable to connect to weather server."
        }), 500

    except Exception as e:

        print("WEATHER ERROR:", e)

        return jsonify({
            "error": "Weather processing error."
        }), 500


# =========================================================
# FORECAST
# =========================================================

@app.route("/forecast")
def forecast():

    city = request.args.get("city", "").strip()

    if not city:

        return jsonify({
            "error": "Please enter a city."
        }), 400

    if not API_KEY:

        return jsonify({
            "error": "OpenWeather API key is missing."
        }), 500

    url = "https://api.openweathermap.org/data/2.5/forecast"

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        print(
            "FORECAST API:",
            response.status_code,
            city
        )

        if response.status_code == 401:

            return jsonify({
                "error": "Invalid OpenWeather API key."
            }), 401

        if response.status_code == 404:

            return jsonify({
                "error": "City not found."
            }), 404

        response.raise_for_status()

        data = response.json()

        forecast_list = []

        for item in data.get("list", []):

            forecast_list.append({

                "datetime": item["dt_txt"],

                "temperature": round(
                    item["main"]["temp"],
                    1
                ),

                "feels_like": round(
                    item["main"]["feels_like"],
                    1
                ),

                "humidity": item["main"]["humidity"],

                "pressure": item["main"]["pressure"],

                "wind_speed": item["wind"]["speed"],

                "description":
                    item["weather"][0]["description"],

                "icon":
                    item["weather"][0]["icon"]

            })

        return jsonify({
            "city": city,
            "forecast": forecast_list
        })

    except Exception as e:

        print("FORECAST ERROR:", e)

        return jsonify({
            "error": "Unable to connect to weather server."
        }), 500


# =========================================================
# AI TEMPERATURE PREDICTION
# =========================================================

@app.route("/predict", methods=["POST"])
def predict():

    global model

    if model is None:

        return jsonify({
            "error":
                "ML model not found. Run train_model.py first."
        }), 500

    try:

        data = request.get_json()

        humidity = float(
            data.get("humidity", 0)
        )

        pressure = float(
            data.get("pressure", 0)
        )

        wind_speed = float(
            data.get("wind_speed", 0)
        )

        temperature = float(
            data.get("temperature", 0)
        )

        features = [[
            humidity,
            pressure,
            wind_speed,
            temperature
        ]]

        prediction = model.predict(features)

        predicted_temperature = float(
            prediction[0]
        )

        return jsonify({

            "prediction":
                round(
                    predicted_temperature,
                    1
                )

        })

    except Exception as e:

        print("PREDICTION ERROR:", e)

        return jsonify({
            "error": "Prediction failed."
        }), 500


# =========================================================
# SEARCH HISTORY
# =========================================================

@app.route("/history")
def history():

    try:

        conn = sqlite3.connect(DB_NAME)

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM searches
            ORDER BY id DESC
            LIMIT 20
        """)

        rows = cursor.fetchall()

        conn.close()

        result = []

        for row in rows:

            result.append({

                "id": row["id"],

                "city": row["city"],

                "temperature":
                    row["temperature"],

                "humidity":
                    row["humidity"],

                "pressure":
                    row["pressure"],

                "wind_speed":
                    row["wind_speed"],

                "description":
                    row["description"],

                "searched_at":
                    row["searched_at"]

            })

        return jsonify(result)

    except Exception as e:

        print("HISTORY ERROR:", e)

        return jsonify({
            "error": "Unable to load history."
        }), 500

@app.route("/clear-history", methods=["DELETE"])
def clear_history():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Correct table name
        cursor.execute("DELETE FROM searches")

        conn.commit()
        deleted_count = cursor.rowcount
        conn.close()

        return jsonify({
            "success": True,
            "message": "History deleted successfully!",
            "deleted": deleted_count
        })

    except Exception as e:
        print("CLEAR HISTORY ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
        
@app.route("/delete-history/<int:history_id>", methods=["DELETE"])
def delete_history(history_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM searches WHERE id = ?",
            (history_id,)
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted == 0:
            return jsonify({
                "success": False,
                "message": "History record not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "History deleted successfully"
        })

    except Exception as e:
        print("DELETE HISTORY ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
# =========================================================
# TEST API
# =========================================================

@app.route("/test-api")
def test_api():

    if not API_KEY:

        return jsonify({
            "status": "ERROR",
            "message": "API key is missing"
        })

    try:

        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": "Hyderabad",
                "appid": API_KEY,
                "units": "metric"
            },
            timeout=10
        )

        return jsonify({

            "status_code":
                response.status_code,

            "response":
                response.json()

        })

    except Exception as e:

        return jsonify({

            "status": "ERROR",

            "message": str(e)

        })


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    init_db()

    print("=" * 60)

    if API_KEY:

        print("OpenWeather API: CONFIGURED")

    else:

        print("OpenWeather API: MISSING")

    if model:

        print("AI MODEL: LOADED")

    else:

        print("AI MODEL: NOT LOADED")

    print("DATABASE:", DB_NAME)

    print("MODEL:", MODEL_PATH)

    print("")
    print("Open:")
    print("http://127.0.0.1:5000")

    print("=" * 60)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )