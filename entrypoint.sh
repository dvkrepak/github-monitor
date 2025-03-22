#!/bin/sh

echo "🔄 Running migrations..."
python manage.py migrate

if [ "$DJANGO_LOAD_TEST_DATA" = "true" ]; then
  echo "📦 Loading test data..."
  python manage.py load_test_data
else
  echo "ℹ️ Skipping test data loading"
fi

echo "🚀 Starting server..."
python manage.py runserver 0.0.0.0:8000
