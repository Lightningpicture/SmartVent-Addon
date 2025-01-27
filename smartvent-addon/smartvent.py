
import requests
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MinMaxScaler
from flask import Flask, render_template, jsonify
import logging
import time

# Konfiguration
HA_IP = "http://192.168.x.x"  # Ersetzen Sie dies durch die IP-Adresse von Home Assistant
MIN_HUMIDITY = 60
MAX_HUMIDITY = 70
MIN_TEMPERATURE = 18
MAX_TEMPERATURE = 22
LEARN_RATE = 0.01
PORT = 8088

# Beispiel für sensorbezogene Daten
humidity_data = []

# Flask App für Webinterface
app = Flask(__name__)

# Funktion, um Sensorwerte zu holen
def get_sensor_data(sensor_id):
    try:
        response = requests.get(f'{HA_IP}/api/states/{sensor_id}', timeout=10)
        response.raise_for_status()
        return response.json()['state']
    except requests.exceptions.RequestException as e:
        logging.error(f"Fehler beim Abrufen von {sensor_id}: {e}")
        return None

# Funktion zur Entscheidungsfindung (Lüftung an oder aus)
def should_activate_ventilation(humidity, temperature, person_home):
    if humidity > MAX_HUMIDITY or (humidity > MIN_HUMIDITY and temperature > MAX_TEMPERATURE):
        return True
    if person_home:
        return humidity > MIN_HUMIDITY
    return False

# Hauptlogik für das Lernen und die Steuerung
def ventilation_control(person_home):
    humidity = get_sensor_data('sensor.humidity_livingroom')
    temperature = get_sensor_data('sensor.temp_livingroom')

    if humidity is None or temperature is None:
        return

    # Entscheidung treffen, ob die Lüftung aktiviert werden soll
    ventilation_on = should_activate_ventilation(humidity, temperature, person_home)

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
        logging.info(f"Ventilation {'On' if prediction[0] else 'Off'}")

        # Lüftung steuern
        control_ventilation(prediction[0])

# Funktion zur Steuerung der Lüftungseinheit
def control_ventilation(ventilation_on):
    entity_ids = ["switch.lueftung_badezimmer", "switch.lueftung_kuche"]
    for entity_id in entity_ids:
        try:
            action = 'turn_on' if ventilation_on else 'turn_off'
            response = requests.post(f'{HA_IP}/api/services/switch/{action}', json={"entity_id": entity_id})
            response.raise_for_status()
            logging.info(f"{entity_id} wurde {'eingeschaltet' if ventilation_on else 'ausgeschaltet'}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Fehler beim Steuern der Lüftungseinheit {entity_id}: {e}")

# Webroute für das Frontend
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data')
def get_data():
    humidity = get_sensor_data('sensor.humidity_livingroom')
    temperature = get_sensor_data('sensor.temp_livingroom')
    if humidity is not None and temperature is not None:
        return jsonify({"humidity": humidity, "temperature": temperature, "humidity_data": humidity_data})
    return jsonify({"error": "Daten konnten nicht abgerufen werden"}), 500

# Starte den Flask Webserver
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(port=PORT, host="0.0.0.0")
