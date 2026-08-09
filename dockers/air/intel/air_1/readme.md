# Air service (Intel/CPU) Docker image

Runs `project_code/air/main_air.py` in a container.

## Build & run
```
sudo docker compose -f docker-compose.air-intel.yml up --build
sudo docker compose -f docker-compose.air-intel.yml up
```

## Master / Slave
The container patches `general.run_as_master` in `app_config/conf.yaml` at
start-up based on the `RUN_AS_MASTER` environment variable set in
`docker-compose.air-intel.yml` (`true` -> master drone, `false` -> slave drone).

To run as a slave instead, edit `docker-compose.air-intel.yml`:
```yaml
    environment:
      - RUN_AS_MASTER=false
```

## Networking
The service uses `network_mode: host` since it communicates with the ground,
quad and vision services over `127.0.0.1` (as configured in `conf.yaml`).

`project_code/utils/utils.py:get_running_ip()` resolves to `host.docker.internal`
whenever the code detects it's running inside a container (used to reach the
quad-api websocket/http server). That hostname is normally only injected
automatically when using Docker's default bridge networking - since this
container uses `network_mode: host` (no bridge/gateway), `host.docker.internal`
is mapped explicitly to `127.0.0.1` via `extra_hosts` in
`docker-compose.air-intel.yml`. Without this, the websocket connect in
`quad_manager.py` (`receive_drone_status`) will silently fail to connect
(only when running inside Docker; running the script directly on the host
works fine because `get_running_ip()` just returns `127.0.0.1` there).

