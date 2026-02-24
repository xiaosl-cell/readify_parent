FROM ghcr.io/astral-sh/uv:0.5.22 AS uv

FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /usr/local/bin/

COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .
RUN mkdir -p app/static

EXPOSE 8081
CMD ["python", "main.py"]
