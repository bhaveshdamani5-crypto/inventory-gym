FROM python:3.11-slim

WORKDIR /app

# Minimal system deps
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything
COPY . .

# Run the app
# Use uvicorn directly to avoid any python wrapper issues
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
