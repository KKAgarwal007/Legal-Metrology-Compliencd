#!/bin/sh
set -e

# Ensure required persistent storage directories exist
mkdir -p /app/uploads/crops /app/reports /app/instance

# Automatically initialize SQLite database and default users if not initialized
python -c "
import os
from app import app, db, User, init_db_and_seed
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        init_db_and_seed()
"

# Execute container CMD (e.g. gunicorn or python app.py)
exec "$@"
