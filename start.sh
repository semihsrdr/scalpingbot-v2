#!/bin/bash

# This script runs both the web server and the worker.
# It's designed to be used as the start command in Coolify
# and also works for local development.

# Define a function to be called on script exit
cleanup() {
    echo "Termination signal received. Shutting down all child processes..."
    # A SIGTERM is sent to all processes in the process group.
    kill 0
    echo "Shutdown complete."
}

# Set the trap: when the script receives SIGINT (Ctrl+C) or SIGTERM, run the cleanup function
trap cleanup SIGINT SIGTERM

# Start Gunicorn in the background.
# It uses the $PORT variable from Coolify, or defaults to 3000 for local use.
echo "Starting Gunicorn web server in the background..."
gunicorn app:app --bind 0.0.0.0:${PORT:-3000} &

# Start the worker process in the background
echo "Starting worker process in the background..."
python3 -u worker.py &

# Wait for all background jobs to complete.
# The script will pause here. When it receives a signal (like from Coolify's
# stop button or a new deployment), the trap will fire, killing all
# child processes, which will cause wait to return and the script to exit.
echo "Application is running. Stop with Ctrl+C (local) or via the Coolify UI (deployment)."
wait
