FROM python:3.11-slim

# Install ffmpeg (required for audio/video processing)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main application
COPY bhajan-mixer.py .

# Create output volume
VOLUME ["/app/output"]

# Set entrypoint to run the Python application
ENTRYPOINT ["python", "bhajan-mixer.py"]
