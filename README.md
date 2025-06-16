# Hardware Store AI Assistant

This project is an AI-powered assistant for a hardware store that allows users to search for products using natural language. The assistant uses embeddings and a vector database to find the most relevant products for a given query.

## Features

-   **Natural Language Search**: Find products using everyday language, not just keywords.
-   **Vector-Based Search**: Uses modern vector embeddings for semantic search.
-   **FastAPI Backend**: A robust and fast backend built with FastAPI.
-   **Dockerized Environment**: Easy to set up and run with Docker Compose.
-   **PostgreSQL Database**: For storing product information.
-   **Qdrant**: As the vector database for efficient similarity search.

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   └── utils/
│   ├── Dockerfile
│   └── pyproject.toml
├── data/
│   └── initdb/
├── docs/
│   └── esquema.txt
├── infra/
│   └── docker-compose.yml
├── .gitignore
├── LICENSE
├── makefile
└── README.md
```

## Getting Started

### Prerequisites

-   Docker and Docker Compose
-   An OpenAI API key

### Installation

1.  **Clone the repository:**

    ```sh
    git clone https://github.com/your-username/Hardware-Store-AI-Assistant.git
    cd Hardware-Store-AI-Assistant
    ```

2.  **Set up the environment variables:**

    Create a `.env` file in the `backend` directory by copying the example file:

    ```sh
    cp backend/.env.example backend/.env
    ```

    Now, edit `backend/.env` and add your credentials. At a minimum, you need to set `OPENAI_API_KEY`.

3.  **Build and run the services:**

    Use the `makefile` to bring up the Docker containers:

    ```sh
    make up
    ```

    This will start the database, the vector store, and the backend application.

## Usage

Once the services are running, you can access the API documentation at `http://localhost:8000/docs`.

To perform a search, send a POST request to the `/search` endpoint:

```sh
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "a tool to hit nails"}'
```

## Makefile Commands

-   `make up`: Start all services.
-   `make down`: Stop and remove all services.
-   `make logs`: View the logs for all services.