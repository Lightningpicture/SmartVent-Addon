
import requests
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MinMaxScaler
from flask import Flask, render_template, jsonify
import logging

# Configuration
HA_IP = "http://192.168.x.x"  # Replace with Home Assistant's IP address
MIN_HUMIDITY = 60
MAX_HUMIDITY = 70
MIN_TEMPERATURE = 18
MAX_TEMPERATURE = 22
LEARN_RATE = 0.01
PORT = 8088

# Example for sensor-related data
humidity_data = []

# Flask app for the web interface
app = Flask(__name__)

# Function to get sensor data
def get_sensor_data(sensor_id):
    try:
        response = requests.get(f'{HA_IP}/api/states/{sensor_id}', timeout=10)
        response.raise_for_status()
        return response.json()['state']
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {sensor_id}: {e}")
        return None

# Function to make a decision about ventilation (on or off)
def should_activate_ventilation(humidity, temperature, person_home):
    if humidity > MAX_HUMIDITY or (humidity > MIN_HUMIDITY and temperature > MAX_TEMPERATURE):
        return True
    if person_home:
        return humidity > MIN_HUMIDITY
    return False

# Main logic for learning and control
def ventilation_control(person_home):
    humidity = get_sensor_data('sensor.humidity_livingroom')
    temperature = get_sensor_data('sensor.temp_livingroom')

    if humidity is None or temperature is None:
        return

    # Make a decision whether to activate the ventilation
    ventilation_on = should_activate_ventilation(humidity, temperature, person_home)

    # Collect data for training
    humidity_data.append(humidity)

    # Improve the model with machine learning
    if len(humidity_data) > 30:
        df = pd.DataFrame(humidity_data, columns=["humidity"])
        X = df[["humidity"]]
        y = [ventilation_on for _ in range(len(X))]

        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)

        model = LogisticRegression()
        model.fit(X_scaled, y)

        # Make prediction for the next data point
        prediction = model.predict([scaler.transform([[humidity]])])
        logging.info(f"Ventilation {'On' if prediction[0] else 'Off'}")

        # Control the ventilation unit
        control_ventilation(prediction[0])

# Function to control the ventilation unit
def control_ventilation(ventilation_on):
    entity_ids = ["switch.lueftung_badezimmer", "switch.lueftung_kuche"]
    for entity_id in entity_ids:
        try:
            action = 'turn_on' if ventilation_on else 'turn_off'
            response = requests.post(f'{HA_IP}/api/services/switch/{action}', json={"entity_id": entity_id})
            response.raise_for_status()
            logging.info(f"{entity_id} turned {'on' if ventilation_on else 'off'}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error controlling ventilation unit {entity_id}: {e}")

# Web route for the frontend
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data')
def get_data():
    humidity = get_sensor_data('sensor.humidity_livingroom')
    temperature = get_sensor_data('sensor.temp_livingroom')
    if humidity is not None and temperature is not None:
        return jsonify({"humidity": humidity, "temperature": temperature, "humidity_data": humidity_data})
    return jsonify({"error": "Data could not be retrieved"}), 500

# Start the Flask web server
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(port=PORT, host="0.0.0.0")
