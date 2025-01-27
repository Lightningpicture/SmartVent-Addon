
import requests
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MinMaxScaler
from flask import Flask, render_template, jsonify
import time

# Konfiguration
MIN_HUMIDITY = 60
MAX_HUMIDITY = 70
MIN_TEMPERATURE = 18
MAX_TEMPERATURE = 22
LEARN_RATE = 0.01
PORT = 8088
HUMIDITY_SENSOR_ID = "sensor.humidity_livingroom"
TEMPERATURE_SENSOR_ID = "sensor.temp_livingroom"

# Beispiel für sensorbezogene Daten
humidity_data = []

# Flask App für Webinterface
app = Flask(__name__)

# Funktion, um Sensorwerte zu holen
def get_sensor_data():
    humidity = requests.get(f'http://homeassistant.local/api/states/{HUMIDITY_SENSOR_ID}').json()['state']
    temperature = requests.get(f'http://homeassistant.local/api/states/{TEMPERATURE_SENSOR_ID}').json()['state']
    external_humidity = requests.get(f'http://homeassistant.local/api/states/{HUMIDITY_SENSOR_ID}').json()['state']
    external_temperature = requests.get(f'http://homeassistant.local/api/states/{TEMPERATURE_SENSOR_ID}').json()['state']
    return humidity, temperature, external_humidity, external_temperature

# Funktion zur Entscheidungsfindung (Lüftung an oder aus)
def should_activate_ventilation(humidity, temperature, external_humidity, external_temperature, person_home):
    if humidity > MAX_HUMIDITY or (humidity > MIN_HUMIDITY and temperature > MAX_TEMPERATURE):
        return True
    if external_humidity < humidity and external_temperature < temperature:
        return False
    if person_home:
        return humidity > MIN_HUMIDITY
    return False

# Hauptlogik für das Lernen und die Steuerung
def ventilation_control(person_home):
    humidity, temperature, external_humidity, external_temperature = get_sensor_data()

    # Entscheidung treffen, ob die Lüftung aktiviert werden soll
    ventilation_on = should_activate_ventilation(humidity, temperature, external_humidity, external_temperature, person_home)

    # Trainingsdaten sammeln
    humidity_data.append(humidity)

    # Daten mit Machine Learning verbessern
    if len(humidity_data) > 30:
        df = pd.DataFrame(humidity_data, columns=["humidity"])
        X = df[["humidity"]]
        y = [ventilation_on for _ in range(len(X))]

        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)

        model = LogisticRegression()
        model.fit(X_scaled, y)

        # Vorhersage für die nächste Zeit
        prediction = model.predict([scaler.transform([[humidity]])])
        print(f"Ventilation {'On' if prediction[0] else 'Off'}")

# Webroute für das Frontend
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data')
def get_data():
    humidity, temperature, _, _ = get_sensor_data()
    return jsonify({"humidity": humidity, "temperature": temperature, "humidity_data": humidity_data})

# Starte den Flask Webserver
if __name__ == "__main__":
    app.run(port=PORT, host="0.0.0.0")
