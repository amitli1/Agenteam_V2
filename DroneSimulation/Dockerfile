# Dockerfile for the drone simulation (simulation.py)
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY simulation.py /app/simulation.py
COPY simulation.yaml /app/simulation.yaml

# quad_port is read from simulation.yaml at runtime; keep EXPOSE in sync with
# the default value there.
EXPOSE 8001

CMD ["python", "simulation.py"]

