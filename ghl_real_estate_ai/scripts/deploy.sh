#!/bin/bash
# GHL Real Estate AI - Deployment Script

set -e

echo "🚀 Starting deployment..."

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🗄️  Running migrations..."
# python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
# python manage.py collectstatic --no-input

# Restart services
echo "🔄 Restarting services..."
# systemctl restart ghl-api
# systemctl restart ghl-worker

echo "✅ Deployment complete!"
