# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install PDM, a modern Python package manager
RUN pip install pdm

# Copy the project definition and lock file
COPY pyproject.toml pdm.lock* /app/

# Install production dependencies using PDM
# The --prod flag skips development dependencies
RUN pdm install --prod --no-lock

# Copy the application source code into the container
COPY ./app /app/app

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using uvicorn
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
