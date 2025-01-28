import requests
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MinMaxScaler
from flask import Flask, render_template, jsonify
import logging
import os

# Flask App für das Webinterface
app = Flask(__name__)

# Konfiguration (dynamisch aus Home Assistant)
HA_IP = os.getenv('HA_IP', 'http://homeassistant.local:8123')  # Ersetzt durch die IP-Adresse von Home Assistant
PORT = 8088
MIN_HUMIDITY = 60
MAX_HUMIDITY = 70
MIN_TEMPERATURE = 18
MAX_TEMPERATURE = 22
LEARN_RATE = 0.01

# Beispiel für Sensordaten
humidity_data = []

# Hole die Optionen für das Addon (dynamisch aus den Home Assistant Einstellungen)
def get_addon_config():
    try:
        # Hole die Addon-Konfiguration (mit deinem Addon-Token)
        response = requests.get(f'{HA_IP}/api/hassio/addons/config/{addon_slug}')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching addon config: {e}")
        return {}

# Funktion, um Sensordaten zu holen
def get_sensor_data(sensor_id):
    try:
        response = requests.get(f'{HA_IP}/api/states/{sensor_id}', timeout=10)
        response.raise_for_status()
        return response.json()['state']
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {sensor_id}: {e}")
        return None

# Funktion zur Entscheidung, ob die Lüftung aktiviert werden soll
def should_activate_ventilation(humidity, temperature, person_home):
    if humidity > MAX_HUMIDITY or (humidity > MIN_HUMIDITY and temperature > MAX_TEMPERATURE):
        return True
    if person_home:
        return humidity > MIN_HUMIDITY
    return False

# Hauptlogik für das Lernen und die Steuerung
def ventilation_control(person_home):
    # Hole die dynamische Konfiguration
    addon_config = get_addon_config()
    
    if not addon_config:
        logging.error("Could not retrieve configuration for addon")
        return

    # Hole die Entitäten aus der Konfiguration
    humidity_sensor_id = addon_config.get("humidity_sensor_id", ["sensor.humidity_livingroom"])[0]  # Standardwert für den Fall
    temperature_sensor_id = addon_config.get("temperature_sensor_id", ["sensor.temp_livingroom"])[0]  # Standardwert

    # Hole die Sensordaten
    humidity = get_sensor_data(humidity_sensor_id)
    temperature = get_sensor_data(temperature_sensor_id)

    if humidity is None or temperature is None:
        return

    # Entscheidet, ob die Lüftung aktiviert werden soll
    ventilation_on = should_activate_ventilation(humidity, temperature, person_home)

    # Sammelt Daten für das Lernen
    humidity_data.append(humidity)

    # Verbessert das Modell mit maschinellem Lernen
    if len(humidity_data) > 30:
        df = pd.DataFrame(humidity_data, columns=["humidity"])
        X = df[["humidity"]]
        y = [ventilation_on for _ in range(len(X))]

        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)

        model = LogisticRegression()
        model.fit(X_scaled, y)

        # Vorhersage für den nächsten Datenpunkt
        prediction = model.predict([scaler.transform([[humidity]])])
        logging.info(f"Ventilation {'On' if prediction[0] else 'Off'}")

        # Steuert die Lüftungseinheit
        control_ventilation(prediction[0], addon_config)

# Funktion zur Steuerung der Lüftungseinheit
def control_ventilation(ventilation_on, addon_config):
    for entity_id in addon_config.get("ventilation_id", []):  # Hole dynamisch die Lüftungs-Entitäten
        try:
            action = 'turn_on' if ventilation_on else 'turn_off'
            response = requests.post(f'{HA_IP}/api/services/switch/{action}', json={"entity_id": entity_id})
            response.raise_for_status()
            logging.info(f"{entity_id} turned {'on' if ventilation_on else 'off'}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error controlling ventilation unit {entity_id}: {e}")

# Webroute für das Frontend
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data')
def get_data():
    # Hole die dynamische Konfiguration
    addon_config = get_addon_config()

    if not addon_config:
        return jsonify({"error": "Configuration could not be retrieved"}), 500

    humidity_sensor_id = addon_config.get("humidity_sensor_id", ["sensor.humidity_livingroom"])[0]
    temperature_sensor_id = addon_config.get("temperature_sensor_id", ["sensor.temp_livingroom"])[0]

    humidity = get_sensor_data(humidity_sensor_id)
    temperature = get_sensor_data(temperature_sensor_id)

    if humidity is not None and temperature is not None:
        return jsonify({"humidity": humidity, "temperature": temperature, "humidity_data": humidity_data})
    return jsonify({"error": "Data could not be retrieved"}), 500

# Startet den Flask Webserver
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(port=PORT, host="0.0.0.0")
