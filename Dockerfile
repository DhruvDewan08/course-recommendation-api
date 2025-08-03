# --- Stage 1: The "Builder" ---
    FROM python:3.11-slim-bookworm as builder

    # Set the working directory for this stage
    WORKDIR /app  # <-- CHANGED: Use a consistent /app directory
    
    # Install build-time dependencies
    RUN apt-get update && apt-get install -y --no-install-recommends build-essential
    
    # Copy only the requirements file first
    COPY requirements.txt .
    
    # Build all dependencies into ".whl" files and store them in a /wheels directory
    RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt
    
    
    # --- Stage 2: The "Final" Lean Production Image ---
    FROM python:3.11-slim-bookworm
    
    # Set the working directory for the final application
    WORKDIR /app
    
    # Create and switch to a non-root user
    RUN useradd --create-home appuser
    USER appuser
    
    # Copy ONLY the pre-built wheels from the 'builder' stage's /wheels folder
    COPY --from=builder /wheels /wheels
    
    # Install the wheels from the local folder.
    RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*
    
    # Copy your application code and model artifacts
    COPY --chown=appuser:appuser . .
    
    # Expose the port
    EXPOSE 8000
    
    # Command to run the application
    CMD ["/home/appuser/.local/bin/uvicorn", "04_recommendation_api:app", "--host", "0.0.0.0", "--port", "8000"]