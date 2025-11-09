#!/bin/bash

# Gunicorn web sunucusunu arka planda başlat
echo "Starting Gunicorn web server in the background..."
gunicorn app:app --bind 0.0.0.0:$PORT &

# Worker sürecini ön planda başlat
echo "Starting worker process in the foreground..."
python worker.py
