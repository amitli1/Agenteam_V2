FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 7031

ENV PORT=7031 \
    HOST=0.0.0.0

CMD ["python", "-m", "app.main"]

