#!/bin/bash

# Set default environment variables if not provided
export FLASK_DEBUG=${FLASK_DEBUG:-0}
export RUN_UPDATER=${RUN_UPDATER:-1}
export PORT=${PORT:-10000}

# Start the application with gunicorn
exec gunicorn --config gunicorn.conf.py app:app