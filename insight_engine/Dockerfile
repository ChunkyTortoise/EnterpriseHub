FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic

# Copy insight_engine package
COPY insight_engine/ ./insight_engine/
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

EXPOSE 8080

CMD ["uvicorn", "insight_engine.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
