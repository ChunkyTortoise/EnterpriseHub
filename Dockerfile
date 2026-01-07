# Use an official lightweight Python image.
# 3.11 is stable and performant for FastAPI.
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing pyc files to disc
# PYTHONUNBUFFERED: Ensures python output is sent straight to terminal (logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (needed for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run the application using uvicorn
# main:app refers to main.py file and 'app' object
# --host 0.0.0.0 is crucial for Docker containers
# We use sh -c to allow environment variable expansion for $PORT
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
