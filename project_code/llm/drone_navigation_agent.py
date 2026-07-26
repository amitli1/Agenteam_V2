import ast
import asyncio
import numpy as np
import pandas as pd

from google.genai import Client, types
from google.adk import Agent
from google.adk.runners import InMemoryRunner


class DroneNavigationAgent:
    def __init__(
            self,
            model_name: str = "gpt-oss-20b",
            base_url: str = "http://localhost:8090/v1",
            api_key: str = "EMPTY"
    ):
        self.model_name = model_name

        # CORRECT FIX FOR BASE_URL IN GOOGLE GENAI SDK:
        # Pass custom endpoints inside HttpOptions
        http_opts = types.HttpOptions(base_url=base_url)

        try:
            self.client = Client(
                api_key=api_key,
                http_options=http_opts
            )
        except Exception:
            # Fallback if vLLM endpoint doesn't strictly adhere to Google GenAI Client
            self.client = None

        # Instantiate Google ADK Agent
        self.agent = Agent(
            name="drone_navigation_agent",
            model=self.model_name,
            instruction="""
            You are an autonomous drone flight planner.
            Extract the destination entity type (e.g., 'building') and entity number (e.g., '2') from the user command.
            Calculate waypoints by resolving target geometries from the system database.
            """,
            tools=[self._generate_flight_waypoints]
        )

    @staticmethod
    def _parse_geometry_string(geom_str: str) -> list[tuple[float, float]]:
        """Parses point '[lat, lon]' or polygon '[lat1 lon1, lat2 lon2]' strings."""
        cleaned = str(geom_str).strip()
        if not cleaned or cleaned == "nan":
            return []

        # Point format: "[47.6395010, -122.141538]"
        if "," in cleaned and not cleaned.startswith("[["):
            try:
                coords = ast.literal_eval(cleaned)
                return [(float(coords[0]), float(coords[1]))]
            except Exception:
                pass

        # Polygon format: "[47.64014 -122.1415, 47.64014 -122.1409, ...]"
        cleaned = cleaned.strip("[]")
        point_strings = cleaned.split(",")
        points = []
        for p in point_strings:
            parts = p.strip().split()
            if len(parts) == 2:
                points.append((float(parts[0]), float(parts[1])))
        return points

    def _generate_flight_waypoints(
            self,
            destination_type: str,
            destination_number: str,
            database_manager: object,
            default_alt: float = 20.0
    ) -> dict:
        """Queries the database and computes waypoints for Point or Polygon geometries."""
        df = database_manager.get_db()

        # Database Entity Search
        match = df[
            (df["entity_type"].astype(str).str.lower() == str(destination_type).lower()) &
            (df["entity_number"].astype(str) == str(destination_number))
            ]

        if match.empty:
            return {
                "status": "error",
                "error": f"DESTINATION_NOT_FOUND: 'Building {destination_number}' does not exist in the database.",
                "waypoints": []
            }

        row = match.iloc[0]
        coords = self._parse_geometry_string(row.get("geometry", ""))

        if not coords:
            return {
                "status": "error",
                "error": "INVALID_GEOMETRY: Could not parse database coordinates.",
                "waypoints": []
            }

        waypoints = []

        # Case A: Polygon (Returns boundary vertices + polygon center centroid)
        if len(coords) > 1:
            for lat, lon in coords:
                waypoints.append((lat, lon, default_alt))

            # Center Point
            avg_lat = float(np.mean([p[0] for p in coords]))
            avg_lon = float(np.mean([p[1] for p in coords]))
            waypoints.append((avg_lat, avg_lon, default_alt))

        # Case B: Single Point Target
        else:
            lat, lon = coords[0]
            alt = row["alt"] if pd.notna(row.get("alt")) and row.get("alt") is not None else default_alt
            waypoints.append((lat, lon, float(alt)))

        return {
            "status": "success",
            "target": f"{destination_type} {destination_number}",
            "waypoints": waypoints
        }

    async def get_list_of_wp_from_text_cmd(
            self,
            textCommand: str,
            databaseManager: object,
            main_drone_location: dict,
            defaultALT: float
    ) -> dict:
        """Entry point called to parse text STT commands into drone flight waypoints."""

        # 1. Parse spoken/text entity target ('two' -> '2', 'building')
        words = textCommand.lower().split()
        num_map = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5"}

        target_num = next((w for w in words if w.isdigit()), None)
        if not target_num:
            for w in words:
                if w in num_map:
                    target_num = num_map[w]
                    break

        if not target_num:
            return {
                "status": "error",
                "error": f"PARSE_ERROR: Unable to identify target building/number from command '{textCommand}'.",
                "waypoints": []
            }

        target_type = "building"

        # 2. Run waypoint computation via Google ADK tool function logic
        result = self._generate_flight_waypoints(
            destination_type=target_type,
            destination_number=target_num,
            database_manager=databaseManager,
            default_alt=defaultALT
        )

        return result



if __name__ == "__main__":
    None