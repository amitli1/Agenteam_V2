import os
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _parse_geometry_points(geometry_str):
    """Extract (lat, lon) pairs from a geometry string regardless of the
    separator style used (space-separated pairs joined by commas, or a
    single comma-separated pair)."""

    numbers = re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", str(geometry_str))
    numbers = [float(n) for n in numbers]
    points = list(zip(numbers[0::2], numbers[1::2]))
    return points


def draw_location_string(building_cords):

    building = building_cords

    # Strip brackets and split into coordinate pairs
    coords_str = building.strip("[]")
    points = [p.strip().split() for p in coords_str.split(",")]
    points = [(float(lat), float(lon)) for lat, lon in points]

    lats = [p[0] for p in points]
    lons = [p[1] for p in points]

    # Close the polygon by repeating the first point at the end
    lats_closed = lats + [lats[0]]
    lons_closed = lons + [lons[0]]

    fig, ax = plt.subplots()
    ax.plot(lons_closed, lats_closed, marker="o", linestyle="-")
    ax.fill(lons_closed, lats_closed, alpha=0.2)

    for lat, lon in points:
        ax.annotate(f"({lat:.7f}, {lon:.7f})", (lon, lat), textcoords="offset points", xytext=(5, 5))

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Building Footprint")
    ax.axis("equal")
    ax.grid(True)

    plt.show()

def draw_csv_locations(csv_file):

    df = pd.read_csv(csv_file)
    df = df.dropna(subset=["lat", "lon"])
    if df.empty:
        print(f"No data to plot in {csv_file}")
        return

    # First pass: parse geometry for every row so we can compute a sensible
    # arrow length (ignoring alt, which is not plotted).
    rows_data = []
    all_lats = []
    all_lons = []
    for _, row in df.iterrows():
        points = _parse_geometry_points(row.get("geometry", ""))
        if not points:
            points = [(float(row["lat"]), float(row["lon"]))]
        rows_data.append((row, points))
        all_lats.extend(p[0] for p in points)
        all_lons.extend(p[1] for p in points)

    lat_range = (max(all_lats) - min(all_lats)) if len(all_lats) > 1 else 0.0
    lon_range = (max(all_lons) - min(all_lons)) if len(all_lons) > 1 else 0.0
    arrow_len = max(lat_range, lon_range, 1e-6) * 0.15

    csv_name = os.path.basename(csv_file)
    fig, ax = plt.subplots(num=csv_name)
    fig.canvas.manager.set_window_title(csv_name)

    for row, points in rows_data:
        name = f"{row['entity_type']}_{row['entity_number']}"
        lats = [p[0] for p in points]
        lons = [p[1] for p in points]

        if len(points) >= 3:
            # Polygon: close it and fill it, like draw_location_string
            lats_closed = lats + [lats[0]]
            lons_closed = lons + [lons[0]]
            ax.plot(lons_closed, lats_closed, marker="o", linestyle="-")
            ax.fill(lons_closed, lats_closed, alpha=0.2)
        elif len(points) == 2:
            ax.plot(lons, lats, marker="o", linestyle="-")
        else:
            ax.plot(lons, lats, marker="o", linestyle="None")

        anchor_lat = float(row["lat"])
        anchor_lon = float(row["lon"])
        ax.annotate(
            name,
            (anchor_lon, anchor_lat),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=9,
            weight="bold",
        )

        yaw = row.get("yaw", None)
        if yaw is not None and not pd.isna(yaw):
            yaw_rad = np.radians(float(yaw))
            dx = arrow_len * np.sin(yaw_rad)   # east component -> x
            dy = arrow_len * np.cos(yaw_rad)   # north component -> y
            ax.annotate(
                "",
                xy=(anchor_lon + dx, anchor_lat + dy),
                xytext=(anchor_lon, anchor_lat),
                arrowprops=dict(arrowstyle="->", color="red", lw=2),
            )

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Locations - {csv_name}")
    ax.axis("equal")
    ax.grid(True)

    plt.show()

def draw_path(f_path):
    """Draw each (lat, lon) point in f_path as a marker with an arrow
    showing the yaw direction. The alt field is ignored."""

    if not f_path:
        print("No data to plot in f_path")
        return

    lats = [float(p["lat"]) for p in f_path]
    lons = [float(p["lon"]) for p in f_path]

    lat_range = (max(lats) - min(lats)) if len(lats) > 1 else 0.0
    lon_range = (max(lons) - min(lons)) if len(lons) > 1 else 0.0
    arrow_len = max(lat_range, lon_range, 1e-6) * 0.15

    fig, ax = plt.subplots(num="Path")
    fig.canvas.manager.set_window_title("Path")

    # Plot the path itself connecting the points in order
    ax.plot(lons, lats, marker="o", linestyle="-", color="blue")

    for i, point in enumerate(f_path):
        lat = float(point["lat"])
        lon = float(point["lon"])
        yaw = point.get("yaw", None)

        ax.annotate(
            str(i),
            (lon, lat),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=9,
            weight="bold",
        )

        if yaw is not None and not pd.isna(yaw):
            yaw_rad = np.radians(float(yaw))
            dx = arrow_len * np.sin(yaw_rad)   # east component -> x
            dy = arrow_len * np.cos(yaw_rad)   # north component -> y
            ax.annotate(
                "",
                xy=(lon + dx, lat + dy),
                xytext=(lon, lat),
                arrowprops=dict(arrowstyle="->", color="red", lw=2),
            )

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Path")
    ax.axis("equal")
    ax.grid(True)

    plt.show()

if __name__ == "__main__":

    building = "[32.8501306 35.2736127, 32.8498446 35.2735598, 32.849927 35.2732503, 32.8500918 35.2732774]"
    building = "[47.6416258 -122.1399292, 47.6413398 -122.1399821, 47.6414222 -122.1402916, 47.6415870 -122.1402645]"



    f_path = [{'lat': 47.6401202, 'lon': -122.1415699, 'alt': 14.985000610351562, 'yaw': 358.07711935043335},
            {'lat': 47.6401202, 'lon': -122.1415699, 'alt': 15.0, 'yaw': 358.07711935043335},
            {'lat': 47.640141, 'lon': -122.1415707, 'alt': 15.0, 'yaw': 179.99976938043272},
            {'lat': 47.640141, 'lon': -122.1409465, 'alt': 15.0, 'yaw': 270.0},
            {'lat': 47.6397875, 'lon': -122.1409465, 'alt': 15.0, 'yaw': 0.00023061800686718925},
            {'lat': 47.6397875, 'lon': -122.1415707, 'alt': 15.0, 'yaw': 90.0},
            {'lat': 47.640141, 'lon': -122.1415707, 'alt': 15.0, 'yaw': 179.99976938043272}
              ]

    f_path = [{'lat': 47.6401202, 'lon': -122.1415699, 'alt': 14.985000610351562, 'yaw': 358.07711935043335},
              {'lat': 47.6401202, 'lon': -122.1415699, 'alt': 15.0, 'yaw': 358.07711935043335},
              {'lat': 47.640141, 'lon': -122.1415707, 'alt': 15.0, 'yaw': 179.99976938043272},
              {'lat': 47.640141, 'lon': -122.1409465, 'alt': 15.0, 'yaw': None},
              {'lat': 47.6397875, 'lon': -122.1409465, 'alt': 15.0, 'yaw': None},
              {'lat': 47.6397875, 'lon': -122.1415707, 'alt': 15.0, 'yaw': None},
              {'lat': 47.640141, 'lon': -122.1415707, 'alt': 15.0, 'yaw': None}
              ]

    #draw_path(f_path)

    #draw_location_string(building)

    # draw_csv_locations(r'/home/amitli/repo/Agenteam_V2/project_code/app_config/l_flag_location.csv')
    #draw_csv_locations(r'/home/amitli/repo/Agenteam_V2/project_code/app_config/airsim_poly_db.csv')
    #draw_csv_locations(r'/home/amitli/repo/Agenteam_V2/project_code/app_config/teradion_db.csv')
    draw_csv_locations(r'/home/amitli/repo/Agenteam_V2/project_code/app_config/gazebo_sim.csv')

