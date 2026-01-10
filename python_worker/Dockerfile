FROM python:3.11-slim

# 1. Installazione dipendenze: ffmpeg, nodejs, curl e unzip
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 2. Installazione Deno (per risolvere le JS challenges di YouTube)
RUN curl -fsSL https://deno.land/x/install/install.sh | DENO_INSTALL=/usr/local sh

# 3. Creazione utente e cartelle (creiamo esplicitamente /app e /data)
RUN useradd -u 1000 -m workeruser && \
    mkdir -p /app /data && \
    chown -R workeruser:workeruser /app /data

# 4. Setup ambiente di lavoro
WORKDIR /app

# Installazione librerie Python (incluse le ultime versioni di yt-dlp e flask)
COPY requirements.txt .
RUN pip install --no-cache-dir -U yt-dlp flask -r requirements.txt || \
    pip install --no-cache-dir -U yt-dlp flask

COPY main.py .

# Esecuzione come utente non privilegiato
USER workeruser

EXPOSE 5000
CMD ["python", "main.py"]