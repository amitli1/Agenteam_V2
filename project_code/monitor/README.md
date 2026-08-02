# Monitor Web App

A small Flask web app that displays, in a scatter plot (2D or 3D), the
positions of drones and buildings/entities, and shows the raw status
messages of the master and slave drones in two tables.

## Endpoints

- `POST /get_dataset`
  - JSON body keys: `entity_type`, `entity_number`, `lat`, `lon`, `alt`, `geometry`
  - `geometry` may be:
    - a single point: `[47.6395010, -122.141538]`
    - an array of points: `[[47.6401410 -122.1415707, 47.6401410 -122.1409465, ...]]`
  - Also accepts a bulk `pandas.DataFrame.to_dict()`-style payload (column -> {index: value}),
    which is expanded into individual records server-side.
  - Points parsed from `geometry` (or, if missing, from `lat`/`lon`) are added
    to the scatter plot in **blue**. The `entity_type`/`entity_number` label is
    displayed next to the point (or next to the first point of a multi-point
    geometry), and multi-point geometries are connected with lines to outline
    the shape.

- `POST /get_master_status`
  - JSON body keys (at least): `lat`, `lon`, `alt`
  - Added to the scatter plot in **green** and appended to the master table.

- `POST /get_slave_status`
  - JSON body keys (at least): `lat`, `lon`, `alt`
  - Added to the scatter plot in **red** and appended to the slave table.

- `GET /data` - JSON snapshot of all accumulated points/history (polled by the UI).
- `GET /` - the web UI.

## UI

- Radio button to switch the scatter plot between **2D** (lat/lon) and
  **3D** (lat/lon/alt).
- White background scatter plot with a black grid.
- Two tables showing the history of `get_master_status` / `get_slave_status`
  messages.
- Old data is never cleared - new points/rows are only appended.

## Run locally

```bash
cd project_code/monitor
pip install -r requirements.txt
python -m app.main
```

The app listens on port `7031` by default (override with the `PORT` env var).

## Run with Docker

```bash
cd project_code/monitor
docker compose up --build
```

The web app will be available at `http://localhost:7031`.

## Example requests

```bash
curl -X POST http://localhost:7031/get_dataset \
  -H "Content-Type: application/json" \
  -d '{"entity_type": "building", "entity_number": "1", "geometry": "[[47.6401410 -122.1415707, 47.6401410 -122.1409465, 47.6397875 -122.1409465, 47.6397875 -122.1415707]]"}'

curl -X POST http://localhost:7031/get_master_status \
  -H "Content-Type: application/json" \
  -d '{"lat": 47.6405, "lon": -122.1410, "alt": 120}'

curl -X POST http://localhost:7031/get_slave_status \
  -H "Content-Type: application/json" \
  -d '{"lat": 47.6400, "lon": -122.1412, "alt": 100}'
```

