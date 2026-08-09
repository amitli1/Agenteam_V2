FROM python:3.11-slim

# NOTE: this Dockerfile is built with the repo root as the build context
# (see docker-compose.yml "context: ../../.."), because Docker COPY does not
# allow paths outside of the build context (e.g. "../../../project_code").

WORKDIR /app

COPY dockers/monitor/intel/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY project_code/monitor/app ./app

EXPOSE 7031

ENV PORT=7031 \
    HOST=0.0.0.0

CMD ["python", "-m", "app.main"]

