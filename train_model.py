import os
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

import joblib


# =========================================================
# CREATE MODEL DIRECTORY
# =========================================================

os.makedirs("models", exist_ok=True)


# =========================================================
# SAMPLE WEATHER DATA
#
# Features:
# humidity
# pressure
# wind speed
# current temperature
#
# Target:
# next temperature
# =========================================================

data = {

    "humidity": [
        40, 45, 50, 55, 60,
        65, 70, 75, 80, 85,
        42, 48, 53, 58, 63,
        68, 73, 78, 83, 88,
        45, 52, 59, 66, 72,
        77, 82, 87, 90, 95
    ],

    "pressure": [
        1005, 1008, 1010, 1012, 1014,
        1010, 1008, 1006, 1004, 1002,
        1015, 1013, 1011, 1009, 1007,
        1005, 1003, 1001, 999, 998,
        1018, 1016, 1014, 1012, 1010,
        1008, 1006, 1004, 1002, 1000
    ],

    "wind_speed": [
        1, 2, 3, 4, 5,
        6, 7, 8, 9, 10,
        2, 3, 4, 5, 6,
        7, 8, 9, 10, 11,
        1, 3, 5, 7, 9,
        2, 4, 6, 8, 10
    ],

    "temperature": [
        30, 31, 32, 33, 34,
        33, 32, 31, 30, 29,
        35, 34, 33, 32, 31,
        30, 29, 28, 27, 26,
        36, 35, 34, 33, 32,
        31, 30, 29, 28, 27
    ],

    "next_temperature": [
        31, 32, 33, 34, 34,
        32, 31, 30, 29, 28,
        34, 33, 32, 31, 30,
        29, 28, 27, 26, 25,
        35, 34, 33, 32, 31,
        30, 29, 28, 27, 26
    ]
}


df = pd.DataFrame(data)


# =========================================================
# FEATURES AND TARGET
# =========================================================

X = df[
    [
        "humidity",
        "pressure",
        "wind_speed",
        "temperature"
    ]
]

y = df["next_temperature"]


# =========================================================
# SPLIT DATA
# =========================================================

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,
    test_size=0.2,
    random_state=42
)


# =========================================================
# TRAIN RANDOM FOREST
# =========================================================

model = RandomForestRegressor(

    n_estimators=100,

    max_depth=8,

    random_state=42

)


model.fit(
    X_train,
    y_train
)


# =========================================================
# TEST
# =========================================================

predictions = model.predict(X_test)

error = mean_absolute_error(
    y_test,
    predictions
)


print("=" * 60)
print("       WEATHER ML MODEL TRAINING")
print("=" * 60)

print(
    "Mean Absolute Error:",
    round(error, 2)
)


# =========================================================
# SAVE MODEL
# =========================================================

model_path = "models/weather_model.pkl"

joblib.dump(
    model,
    model_path
)


print()
print("Model successfully trained.")
print("Saved:", model_path)

print("=" * 60)