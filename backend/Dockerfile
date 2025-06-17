# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements and install dependencies
COPY pyproject.toml /app/
RUN pip install fastapi uvicorn[standard] openai qdrant-client psycopg2-binary python-dotenv tenacity redis

# Copy the application source code into the container
COPY ./app /app/app

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using uvicorn directly
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
