# Start from an official Python 3.11 "slim" image.
# "slim" = smaller base image, like buying just the kitchen essentials
# instead of furnishing the whole house.
FROM python:3.11-slim

# Set the working directory inside the container.
# Everything from here on happens in /app.
WORKDIR /app

# Copy requirements FIRST (before code).
# Why? Docker caches layers. If requirements.txt hasn't changed,
# Docker skips the slow pip install step — like mise en place.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# NOW copy the rest of the code
COPY . .

# Tell Docker this container listens on port 8000
EXPOSE 8000

# The command to run when the container starts.
# uvicorn is the server; app.main:app is "in app/main.py, use the 'app' object"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
