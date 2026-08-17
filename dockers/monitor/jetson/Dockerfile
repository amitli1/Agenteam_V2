FROM dustynv/pytorch:2.7-r36.4.0
WORKDIR /app

RUN pip install --no-cache-dir --ignore-installed Flask==3.0.3 Werkzeug==3.0.3 \
    --index-url https://pypi.org/simple


COPY project_code/monitor/app ./app

EXPOSE 7031

ENV PORT=7031 \
    HOST=0.0.0.0

CMD ["python3", "-m", "app.main"]


