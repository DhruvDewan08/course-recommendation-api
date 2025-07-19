# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# --- ADDED SECTION TO INSTALL BUILD TOOLS ---
# First, update the package list, then install 'build-essential' which includes gcc
# and 'python3-dev' which contains headers needed to compile against Python.
# Finally, clean up the apt cache to keep the image size down.
RUN apt-get update && apt-get install -y build-essential python3-dev && rm -rf /var/lib/apt/lists/*
# --- END ADDED SECTION ---

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# The host 0.0.0.0 makes the server accessible from outside the container
CMD ["uvicorn", "04_recommendation_api:app", "--host", "0.0.0.0", "--port", "8000"]