from flask import Flask, request, render_template_string, jsonify
import requests
from datetime import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

def process_input(s):
    s = ' '.join(s.split()).replace(',', ' , ').replace(' , ', ',')
    s = s.strip(',').strip()
    if "," in s:
        words = [part.strip() for part in s.split(",", 1)]
    else:
        parts = s.split()
        if len(parts) > 1:
            words = [parts[0], " ".join(parts[1:])]
        else:
            words = [s, ""]
    if len(words) == 1:
        words.append("")
    return words

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        cityinp = request.form.get("city")
        words = process_input(cityinp)
        if words:
            city, country = words
            apikey = "a49297340003b7cce8a38cbc1c3ee9de"
            
            # Handle cases where country is not provided
            if country:
                query = f"{city},{country}"
            else:
                query = city

            # Current weather data
            current_weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={query}&appid={apikey}&units=metric"
            current_weather_response = requests.get(current_weather_url)
            
            # 5-day forecast data
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={query}&appid={apikey}&units=metric"
            forecast_response = requests.get(forecast_url)
            
            if current_weather_response.status_code == 200 and forecast_response.status_code == 200:
                try:
                    current_weather_data = current_weather_response.json()
                    forecast_data = forecast_response.json()

                    # Log the API responses to help with debugging
                    app.logger.debug(f"Current weather response: {current_weather_data}")
                    app.logger.debug(f"Forecast response: {forecast_data}")

                    # Process forecast data to get daily forecasts
                    daily_forecasts = process_forecast_data(forecast_data)
                    
                    return jsonify({
                        "current_weather": current_weather_data,
                        "forecast": daily_forecasts
                    })
                except Exception as e:
                    app.logger.error(f"Error processing API response: {str(e)}")
                    return jsonify({"error_message": "Error processing weather data. Please try again."})
            else:
                app.logger.error(f"API request failed. Current weather status: {current_weather_response.status_code}, Forecast status: {forecast_response.status_code}")
                app.logger.error(f"Current weather error: {current_weather_response.json()}")
                app.logger.error(f"Forecast error: {forecast_response.json()}")
                return jsonify({"error_message": f"Failed to fetch weather data. Please try again. Status codes: {current_weather_response.status_code}, {forecast_response.status_code}"})
        else:
            return jsonify({"error_message": "Invalid input."})

    # Load index.html as a string
    with open("index.html") as f:
        html_content = f.read()

    return render_template_string(html_content)

def process_forecast_data(forecast_data):
    daily_forecasts = []
    current_date = None

    for item in forecast_data['list']:
        date = datetime.fromtimestamp(item['dt']).date()

        if len(daily_forecasts) < 5:
            # Ensure no duplicate entries for the same day
            if not any(f['date'] == date.strftime('%Y-%m-%d') for f in daily_forecasts):
                daily_forecasts.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'temp': item['main']['temp'],
                    'description': item['weather'][0]['description'],
                    'icon': item['weather'][0]['icon']
                })
    
    return daily_forecasts

if __name__ == "__main__":
    app.run(debug=True)
