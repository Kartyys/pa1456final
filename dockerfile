# Use Python 3.9 slim image as the base
FROM python:3.9-slim

# Install system dependencies: Git, Docker
RUN apt-get update && apt-get install -y \
    git \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install Gitleaks
RUN curl -sSL https://github.com/zricethezav/gitleaks/releases/download/v8.7.0/gitleaks-linux-amd64 -o /usr/local/bin/gitleaks \
    && chmod +x /usr/local/bin/gitleaks

# Install Python dependencies (if any)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your script to the Docker container
COPY code.py .

# Set the working directory
WORKDIR /app

# Command to run the script
CMD ["python", "code.py"]
