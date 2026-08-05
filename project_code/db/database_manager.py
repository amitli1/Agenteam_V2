import pandas as pd
import logging
from project_code.app_config.settings import app_settings
from pyproj import Geod

class DatabaseManager:
    def __init__(self):
        self.df_db = pd.read_csv(app_settings.database.db_path)


    def geometry_area_m2(self, geometry: str) -> float:
        geod = Geod(ellps="WGS84")
        """
        Calculate the area (m²) of a polygon represented as a string.

        Examples
        --------
        '[47.6401410 -122.1415707, 47.6401410 -122.1409465, 47.6397875 -122.1409465, 47.6397875 -122.1415707]'
        '[47.6395010,-122.141538]'

        Returns
        -------
        float
            Area in square meters. Returns 0.0 if the geometry contains fewer than
            3 points (e.g. a single point).
        """
        if not geometry:
            return 0.0

        # Remove surrounding brackets
        s = geometry.strip()[1:-1]

        points = []
        for item in s.split(","):
            item = item.strip()
            if not item:
                continue

            parts = item.split()
            if len(parts) != 2:
                # Handles the single-point format: "lat,lon"
                parts = item.split(",")

            if len(parts) != 2:
                continue

            lat = float(parts[0])
            lon = float(parts[1])
            points.append((lon, lat))  # Geod expects (lon, lat)

        # Need at least 3 points to form a polygon
        if len(points) < 3:
            return 0.0

        # Close the polygon if needed
        if points[0] != points[-1]:
            points.append(points[0])

        lons, lats = zip(*points)
        area, _ = geod.polygon_area_perimeter(lons, lats)

        return abs(area)

    def check_if_db_is_valid(self):
        l_geomtries = self.df_db['geometry'].values
        for i in range(len(l_geomtries)):
            geomtry = l_geomtries[i]
            area    = self.geometry_area_m2(geomtry)
            if area > app_settings.database.max_area_in_meters:
                entity = f"{self.df_db.entity_type.values[i]}_{self.df_db.entity_number.values[i]}"
                logging.error(f'Max area of: {entity} is: {area}m > {app_settings.database.max_area_in_meters}m')
                return False
        return True

    def get_db(self):
        return self.df_db.copy()

    def get_location(self, entity_type, entity_number):
        df = self.df_db.copy()
        df = df[df.entity_type == entity_type]
        if len(df) == 0:
            logging.error(f"There is no entity_type: {entity_type} in the database")
            return None

        df = df[df.entity_number == int(entity_number)]
        if len(df) == 0:
            logging.error(f"There is no entity_number: {entity_number} (of: {entity_type}) in the database")
            return None

        if len(df) != 1:
            logging.error(f"There are multiple {entity_type}:{entity_number} in the database")
            return None

        lat = df.lat.values[0]
        lon = df.lon.values[0]
        alt = df.alt.values[0]
        return {'lat': lat, 'lon': lon, 'alt': alt}

if __name__ == "__main__":
    databaseManager = DatabaseManager()
    res = databaseManager.get_location("junction", "1")
    df = databaseManager.get_db()
    print(df.shape)
    print(df.columns)
    print(df.to_dict())
    #print(res)


