FROM python:3.11.2-slim-buster

WORKDIR /usr/src/app

# Install poetry
RUN pip install poetry

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* ./
# Copy .env file
COPY ./.env .

# Configure poetry to not use a virtual environment since Docker is already isolated
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --without dev --no-interaction

EXPOSE 8000

# Copy the rest of the application code
COPY . .

# Run the application with poetry
# CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop", "--http", "httptools", "--backlog", "2048", "--reload"]
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "6", "--loop", "uvloop", "--http", "httptools", "--backlog", "2048"]