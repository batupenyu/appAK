#!/bin/bash
# Build script for Vercel deployment

# Install dependencies
pip install -r requirements.txt

# Run Django migrations
python manage.py migrate --no-input

# Collect static files
python manage.py collectstatic --no-input

echo "Build completed successfully!"