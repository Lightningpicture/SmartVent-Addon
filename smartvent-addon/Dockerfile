
# Basis-Image für Python
FROM python:3.10-slim

# Setzt das Arbeitsverzeichnis
WORKDIR /app

# Kopiert die benötigten Dateien
COPY . .

# Installiert die Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Exponiert den Port
EXPOSE 8088

# Startet das Skript
CMD ["python", "smartvent.py"]
