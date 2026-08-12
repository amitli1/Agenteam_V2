FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8003 6000 8080

ENV POINT_PORT=8003 \
    HOLD_PORT=6000 \
    SUMMARY_PORT=8080 \
    HOST=0.0.0.0

CMD ["python", "-m", "app.main"]

