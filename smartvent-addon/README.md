
# SmartVent

**SmartVent** is an AI-powered ventilation control system designed to keep your home comfortable while preventing mold growth. It adjusts ventilation based on humidity, temperature, and weather data.

## Installation

1. Clone this repository to your Home Assistant machine.
2. Build the Docker container using the provided Dockerfile.
3. Configure the necessary sensors in Home Assistant (humidity, temperature, weather station data).
4. Set the configuration options in `addon.json` to adjust the minimum and maximum humidity and temperature thresholds.
5. Start the container and let it monitor the environment and control the ventilation.

## Configuration Options

- `humidity_sensor_id`: Sensor für Luftfeuchtigkeit
- `temperature_sensor_id`: Sensor für Temperatur
- `brightness_sensor_id`: Sensor für Helligkeit
- `heating_sensor_id`: Sensor für Heizung
- `weather_station_id`: Sensor für Wetterstation
- `person_sensor_id`: Sensor für Personen
- `min_humidity`: Mindest-Luftfeuchtigkeit
- `max_humidity`: Maximal-Luftfeuchtigkeit
- `min_temperature`: Mindest-Temperatur
- `max_temperature`: Maximal-Temperatur
- `learn_rate`: Lernrate für das Modell (Anpassungsgeschwindigkeit)

## License

MIT
                