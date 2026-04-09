FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY alembic ./alembic
COPY docs ./docs

ENV PORT=3000

CMD ["python", "app/run_api.py"]
