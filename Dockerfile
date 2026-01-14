FROM python:3.10-slim

# Install system dependencies needed for cmfrec
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY recommender_system.db .

COPY model/ ./model/

COPY Backend/ ./Backend/

WORKDIR /app/Backend

EXPOSE 8000

CMD ["python", "app.py"]