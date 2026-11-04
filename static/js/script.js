
// =========================================================
// WEATHER FORECASTING SYSTEM - COMPLETE CORRECTED JAVASCRIPT
// =========================================================

let currentWeatherData = null;

// ---------------------------------------------------------
// HELPER FUNCTION
// ---------------------------------------------------------

function showError(message) {
    const errorElement = document.getElementById("error");

    if (errorElement) {
        errorElement.textContent = message;
    }
}

function clearError() {
    showError("");
}

function formatValue(value, suffix = "") {
    if (value === undefined || value === null || value === "") {
        return "N/A";
    }

    return `${value}${suffix}`;
}

// ---------------------------------------------------------
// 1. SEARCH CURRENT WEATHER
// ---------------------------------------------------------

async function getWeather() {
    const cityInput = document.getElementById("cityInput");

    if (!cityInput) {
        showError("City input field was not found.");
        return;
    }

    const city = cityInput.value.trim();

    clearError();

    if (!city) {
        showError("Please enter a city name.");
        cityInput.focus();
        return;
    }

    try {
        const response = await fetch(
            `/weather?city=${encodeURIComponent(city)}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to fetch weather.");
        }

        currentWeatherData = data;

        document.getElementById("cityName").textContent =
            `${data.city || city}, ${data.country || ""}`;

        document.getElementById("weatherDescription").textContent =
            data.description || "Weather information unavailable";

        document.getElementById("temperature").textContent =
            formatValue(data.temperature, "°C");

        document.getElementById("humidity").textContent =
            formatValue(data.humidity, "%");

        document.getElementById("feelsLike").textContent =
            formatValue(data.feels_like, "°C");

        document.getElementById("pressure").textContent =
            formatValue(data.pressure, " hPa");

        document.getElementById("wind").textContent =
            formatValue(data.wind_speed, " m/s");

        const weatherIcon = document.getElementById("weatherIcon");

        if (weatherIcon && data.icon) {
            weatherIcon.src =
                `https://openweathermap.org/img/wn/${data.icon}@2x.png`;

            weatherIcon.alt = data.description || "Weather icon";
        }

        const weatherSection = document.getElementById("weatherSection");

        if (weatherSection) {
            weatherSection.classList.remove("hidden");
        }

        // Load other sections
        await Promise.allSettled([
            getForecast(city),
            loadHistory()
        ]);

    } catch (error) {
        console.error("WEATHER ERROR:", error);
        showError(error.message || "Something went wrong.");
    }
}

// ---------------------------------------------------------
// 2. FIVE-DAY WEATHER FORECAST
// ---------------------------------------------------------

async function getForecast(city) {
    const forecastContainer = document.getElementById("forecast");

    if (!forecastContainer) {
        console.error("Forecast container not found!");
        return;
    }

    forecastContainer.innerHTML = "Loading 5-day forecast...";

    try {
        const response = await fetch(
            `/forecast?city=${encodeURIComponent(city)}`
        );

        const data = await response.json();

        console.log("FORECAST RESPONSE:", data);

        if (!response.ok) {
            throw new Error(data.error || "Forecast request failed");
        }

        const forecastList = data.forecast || [];

        if (forecastList.length === 0) {
            forecastContainer.textContent = "No forecast data available.";
            return;
        }

        forecastContainer.innerHTML = "";

        // Group the 3-hour forecasts by date.
        const dailyForecast = {};

        forecastList.forEach(item => {
            if (!item.datetime) return;

            const date = item.datetime.split(" ")[0];

            if (!dailyForecast[date]) {
                dailyForecast[date] = [];
            }

            dailyForecast[date].push(item);
        });

        // Create one card per day.
        Object.keys(dailyForecast).slice(0, 5).forEach(date => {
            const items = dailyForecast[date];

            // Use the forecast closest to 12:00.
            const selected = items.reduce((best, item) => {
                const hour = Number(item.datetime.split(" ")[1].slice(0, 2));
                const bestHour = Number(best.datetime.split(" ")[1].slice(0, 2));

                return Math.abs(hour - 12) < Math.abs(bestHour - 12)
                    ? item : best;
            });

            const card = document.createElement("div");
            card.className = "forecast-card";

            const day = new Date(date + "T00:00:00")
                .toLocaleDateString("en-IN", {
                    weekday: "short",
                    day: "numeric",
                    month: "short"
                });

            const dateHeading = document.createElement("h3");
            dateHeading.textContent = day;

            const icon = document.createElement("img");
            icon.src = `https://openweathermap.org/img/wn/${selected.icon}@2x.png`;
            icon.alt = selected.description || "Weather";

            const temperature = document.createElement("h2");
            temperature.textContent = `${selected.temperature}°C`;

            const description = document.createElement("p");
            description.textContent = selected.description || "N/A";

            const humidity = document.createElement("p");
            humidity.textContent = `💧 Humidity: ${selected.humidity}%`;

            const wind = document.createElement("p");
            wind.textContent = `💨 Wind: ${selected.wind_speed} m/s`;

            card.append(
                dateHeading,
                icon,
                temperature,
                description,
                humidity,
                wind
            );

            forecastContainer.appendChild(card);
        });

    } catch (error) {
        console.error("FORECAST ERROR:", error);

        forecastContainer.textContent =
            "Unable to load forecast: " + error.message;
    }
}

// ---------------------------------------------------------
// 3. AI WEATHER TEMPERATURE PREDICTION
// ---------------------------------------------------------

async function predictWeather() {
    const predictionElement =
        document.getElementById("predictionValue");

    if (!currentWeatherData) {
        if (predictionElement) {
            predictionElement.textContent =
                "Search for a city first.";
        }
        return;
    }

    if (predictionElement) {
        predictionElement.textContent = "Predicting...";
    }

    try {
        const response = await fetch("/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                temperature: Number(currentWeatherData.temperature),
                humidity: Number(currentWeatherData.humidity),
                pressure: Number(currentWeatherData.pressure),
                wind_speed: Number(currentWeatherData.wind_speed)
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "AI prediction failed."
            );
        }

        if (predictionElement) {
            predictionElement.textContent =
                data.prediction !== undefined
                    ? `${data.prediction}°C`
                    : "Prediction unavailable";
        }

    } catch (error) {
        console.error("PREDICTION ERROR:", error);

        if (predictionElement) {
            predictionElement.textContent = error.message;
        }
    }
}

// ---------------------------------------------------------
// 4. LOAD SEARCH HISTORY
// ---------------------------------------------------------

async function loadHistory() {
    const container = document.getElementById("historyTable");

    if (!container) {
        return;
    }

    container.textContent = "Loading history...";

    try {
        const response = await fetch("/history");
        const history = await response.json();

        if (!response.ok) {
            throw new Error(
                history.error || "Unable to load history."
            );
        }

        container.innerHTML = "";

        if (!Array.isArray(history) || history.length === 0) {
            container.textContent = "No recent search history.";
            return;
        }

        history.forEach(item => {
            const row = document.createElement("div");
            row.className = "history-row";

            const details = document.createElement("div");
            details.className = "history-details";

            const city = document.createElement("strong");
            city.textContent = item.city || "Unknown city";

            const info = document.createElement("span");

            info.textContent =
                `${formatValue(item.temperature, "°C")} | ` +
                `${item.description || "N/A"} | ` +
                `${item.searched_at || ""}`;

            const deleteButton = document.createElement("button");

            deleteButton.textContent = "🗑 Delete";
            deleteButton.className = "delete-history-btn";

            deleteButton.addEventListener("click", () => {
                deleteHistory(item.id);
            });

            details.append(city, info);
            row.append(details, deleteButton);
            container.appendChild(row);
        });

    } catch (error) {
        console.error("HISTORY ERROR:", error);
        container.textContent = "Unable to load history.";
    }
}

// ---------------------------------------------------------
// 5. DELETE INDIVIDUAL HISTORY RECORD
// ---------------------------------------------------------

async function deleteHistory(id) {
    if (!confirm("Are you sure you want to delete this record?")) {
        return;
    }

    try {
        const response = await fetch(
            `/delete-history/${encodeURIComponent(id)}`,
            {
                method: "DELETE"
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.message || "Unable to delete history."
            );
        }

        await loadHistory();

    } catch (error) {
        console.error("DELETE HISTORY ERROR:", error);
        alert(error.message);
    }
}

// ---------------------------------------------------------
// 6. CLEAR ALL SEARCH HISTORY
// ---------------------------------------------------------

async function clearHistory() {
    if (!confirm("Delete all search history?")) {
        return;
    }

    try {
        const response = await fetch("/clear-history", {
            method: "DELETE"
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.message || "Unable to clear history."
            );
        }

        await loadHistory();

        alert("Search history cleared successfully.");

    } catch (error) {
        console.error("CLEAR HISTORY ERROR:", error);
        alert(error.message);
    }
}

// ---------------------------------------------------------
// 7. ENTER KEY SEARCH SUPPORT
// ---------------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {

    const cityInput = document.getElementById("cityInput");

    if (cityInput) {
        cityInput.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                getWeather();
            }
        });
    }

    // Load previous searches when the page opens.
    loadHistory();

});

// =========================================================
// END OF WEATHER FORECASTING SYSTEM JAVASCRIPT
// =========================================================
