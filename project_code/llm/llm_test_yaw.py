import matplotlib.pyplot as plt
import numpy as np

if __name__ == "__main__":

    # Waypoints: lat, lon, altitude, yaw
    waypoints = [
        (47.640141,  -122.1415707, 20.0, 215.5396817329062),
        (47.640141,  -122.1415707, 20.0, 215.5396817329062),
        (47.640141,  -122.1415707, 20.0, 130.04732280297196),
        (47.640141,  -122.1409465, 20.0, 229.952677197028),
        (47.6397875, -122.1409465, 20.0, 310.047457948261),
        (47.6397875, -122.1415707, 20.0, 49.95254205173899),
        (47.640141,  -122.1415707, 20.0, 130.04732280297196),
    ]

    lat = np.array([p[0] for p in waypoints])
    lon = np.array([p[1] for p in waypoints])
    yaw = np.array([p[3] for p in waypoints])

    fig, ax = plt.subplots(figsize=(9, 7))

    # ---- Flight path ----
    ax.plot(
        lon, lat,
        color="royalblue",
        linewidth=2.5,
        marker="o",
        markersize=7,
        label="Flight path"
    )

    # ---- Direction arrows ----
    # Scale is chosen in longitude/latitude units for visibility.
    arrow_length = 0.00012

    for i, (la, lo, ya) in enumerate(zip(lat, lon, yaw)):
        # Yaw: 0° = North, 90° = East
        yaw_rad = np.deg2rad(ya)

        # East-West component
        dx = arrow_length * np.sin(yaw_rad)

        # North-South component
        dy = arrow_length * np.cos(yaw_rad)

        ax.arrow(
            lo, la,
            dx, dy,
            width=0.000003,
            head_width=0.000035,
            head_length=0.000035,
            length_includes_head=True,
            color="crimson",
            zorder=5
        )

        ax.text(
            lo, la + 0.000035,
            f"{i}\n{ya:.1f}°",
            fontsize=8,
            ha="center",
            color="darkred"
        )

    # ---- Waypoint labels ----
    for i, (la, lo, _, _) in enumerate(waypoints):
        ax.scatter(lo, la, color="royalblue", s=45, zorder=6)
        ax.text(
            lo + 0.000015,
            la - 0.000025,
            f"WP{i}",
            fontsize=9,
            color="navy"
        )

    # North indicator
    ax.annotate(
        "N",
        xy=(0.96, 0.90),
        xytext=(0.96, 0.78),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops=dict(arrowstyle="->", color="black", lw=2),
        ha="center",
        fontsize=12,
        fontweight="bold"
    )

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Drone Flight Path and Yaw Direction")
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal")
    ax.legend()

    plt.tight_layout()
    plt.show()