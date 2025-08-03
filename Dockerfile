# --- Stage 1: The "Builder" ---
# This stage installs all tools and dependencies
FROM python:3.11-slim-bookworm as builder

# Set the working directory
WORKDIR /wheels

# Install the necessary build tools (like gcc)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential

# Copy only the requirements file first to leverage Docker's layer caching
COPY requirements.txt .

# Build all dependencies into ".whl" files (wheels).
# This compiles scikit-surprise and other libraries.
RUN pip wheel --no-cache-dir -r requirements.txt


# --- Stage 2: The "Final" Lean Production Image ---
# This stage is a fresh, clean image with NO build tools.
FROM python:3.11-slim-bookworm

# Set the working directory
WORKDIR /app

# It's good practice to run as a non-root user for security
RUN useradd --create-home appuser
USER appuser

# Copy ONLY the pre-built wheels from the builder stage
COPY --from=builder /wheels /wheels

# Install the wheels from the local folder. This is fast and requires no tools.
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*

# Copy your application code and the essential models/data folders
COPY --chown=appuser:appuser . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "04_recommendation_api:app", "--host", "0.0.0.0", "--port", "8000"]