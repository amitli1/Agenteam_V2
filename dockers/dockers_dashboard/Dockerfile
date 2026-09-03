FROM python:3.11-slim

# sudo: to run "sudo docker ..." as configured
# docker.io: pulls in containerd/runc dependencies for the docker stack
# docker-cli: the actual "docker" client binary (only a "Recommends" of
#             docker.io, so it must be installed explicitly) - this is what
#             talks to the mounted host docker.sock, we don't need dockerd itself.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        sudo \
        docker.io \
        docker-cli \
    && rm -rf /var/lib/apt/lists/* \
    && which docker

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY config.yaml .
COPY templates/ ./templates/
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 6179

ENTRYPOINT ["./entrypoint.sh"]

