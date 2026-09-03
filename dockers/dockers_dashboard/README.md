# Dockers Dashboard

A lightweight web app to monitor Docker containers running on the host:

1. **Container table** – shows the output of `sudo docker ps` (ID, name, image,
   status, ports, uptime) and auto-refreshes every few seconds.
2. **Live logs** – clicking **View Logs** on a row opens a new browser tab that
   streams `sudo docker logs -f <container>` in real time (via Server-Sent Events).
3. **Config driven** – the sudo username/password and the web server port are
   read from [`config.yaml`](./config.yaml).
4. **Port** – the app listens on the port configured in `config.yaml`
   (`web.port`, default `6179`).
5. **Dockerized** – `Dockerfile` + `docker-compose.yml` are provided to run the
   whole thing as a container.

## Files

| File               | Purpose                                                             |
|--------------------|----------------------------------------------------------------------|
| `app.py`           | Flask app: container list API, log-streaming endpoint, pages        |
| `templates/`       | `index.html` (container table), `logs.html` (live log viewer tab)   |
| `config.yaml`      | Sudo credentials, web host/port, log settings                       |
| `entrypoint.sh`    | Container entrypoint: provisions the sudo user from `config.yaml`   |
| `Dockerfile`       | Builds the app image (Python + sudo + docker CLI)                   |
| `docker-compose.yml` | Runs the app, mounting the host docker socket and config file     |

## Configuration (`config.yaml`)

```yaml
sudo:
  username: "your_sudo_user"
  password: "your_sudo_password"

web:
  port: 6179
  host: "0.0.0.0"

docker:
  refresh_seconds: 5
  log_tail_lines: 200
```

- `sudo.username` / `sudo.password`: credentials used to authenticate the
  `sudo -S docker ...` commands the app runs internally.
- `web.port`: port the Flask server listens on. **Keep this in sync** with the
  port mapping in `docker-compose.yml` (`ports: - "6179:6179"`).
- `docker.refresh_seconds`: how often the container table auto-refreshes.
- `docker.log_tail_lines`: number of trailing log lines fetched when a log tab
  first opens.

## Running locally (without Docker)

```bash
cd dockers/dockers_dashboard
pip install -r requirements.txt
python3 app.py
```

The app itself runs `sudo -S docker ps` / `sudo -S docker logs -f ...` under
the hood, so the machine running it must have `sudo` and `docker` installed,
and the credentials in `config.yaml` must be valid for that machine's sudo user.

## Running with Docker

```bash
cd dockers/dockers_dashboard
# Edit config.yaml with real sudo credentials first!
docker compose up -d --build
```

Then open `http://<host>:6179`.

Notes about the container setup:
- The host's `/var/run/docker.sock` is mounted into the container so the
  containerized `docker` CLI can control containers running on the host.
- On startup, `entrypoint.sh` creates/updates a Linux user inside the
  container matching `sudo.username`/`sudo.password` from `config.yaml`, adds
  it to the `sudo` group, relaxes permissions on the mounted docker socket,
  and finally runs the Flask app as that user — so `sudo docker ...` works
  exactly as requested.
- The compose service runs `privileged: true` so the entrypoint can manage
  users and adjust the socket permissions reliably across different hosts.

## Security note

This app executes `sudo` shell commands using a plaintext password stored in
`config.yaml`. Treat this file as a secret (restrict its permissions, don't
commit real credentials to git) and only expose the dashboard on trusted
networks.

