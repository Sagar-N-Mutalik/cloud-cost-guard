# Use official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies (required for some Python packages)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . /app/

# Collect static files (Whitenoise will serve them)
RUN python manage.py collectstatic --noinput

# Run migrations AND start the Gunicorn server
CMD sh -c "python manage.py migrate && gunicorn --bind 0.0.0.0:80 --timeout 300 costguard_project.wsgi:application"