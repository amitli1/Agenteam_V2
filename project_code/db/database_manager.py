import pandas as pd
import logging
from project_code.app_config.settings import app_settings


class DatabaseManager:
    def __init__(self):
        self.df_db = pd.read_csv(app_settings.database.db_path)

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


