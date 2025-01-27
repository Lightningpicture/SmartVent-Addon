
# Use a Python slim image as base
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the necessary files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for the web interface
EXPOSE 8088

# Start the app
CMD ["python", "smartvent.py"]
