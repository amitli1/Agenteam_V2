import matplotlib.pyplot as plt

if __name__ == "__main__":
    building = "[32.8501306 35.2736127, 32.8498446 35.2735598, 32.849927 35.2732503, 32.8500918 35.2732774]"
    building = "[47.6416258 -122.1399292, 47.6413398 -122.1399821, 47.6414222 -122.1402916, 47.6415870 -122.1402645]"

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
    ax.plot(lats_closed, lons_closed, marker="o", linestyle="-")
    ax.fill(lats_closed, lons_closed, alpha=0.2)

    for lat, lon in points:
        ax.annotate(f"({lat:.7f}, {lon:.7f})", (lat, lon), textcoords="offset points", xytext=(5, 5))

    ax.set_xlabel("Latitude")
    ax.set_ylabel("Longitude")
    ax.set_title("Building Footprint")
    ax.axis("equal")
    ax.grid(True)

    plt.show()