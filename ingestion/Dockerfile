FROM python:3.12-slim

WORKDIR /app

# Copy project files and install
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

CMD ["uvicorn", "worldview_ingestion.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
