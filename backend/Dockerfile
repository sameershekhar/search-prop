FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first for Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies from lock file
RUN uv sync --frozen --no-dev

# Copy application code
COPY app ./app
COPY data ./data

# Copy test files only if you want them available inside the image
# COPY tests ./tests

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]