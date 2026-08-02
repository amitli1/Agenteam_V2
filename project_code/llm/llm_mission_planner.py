"""

Turn a natural-language (STT) flight command into a concrete list of GPS
way-points for one or two drones.

Inputs (see :meth:`MissionPlannerAgent.get_way_points`):
    1. text_command          - free text coming from the STT model
                               (e.g. "go to building number two",
                                     "surround building number 5").
    2. team_member           - one of:
                                   "buddy"  -> master drone only
                                   "jarvis" -> slave  drone only
                                   "team"   -> both drones
    3. master_drone_location - {'lat', 'lon', 'alt', 'yaw'}
    4. slave_drone_location  - {'lat', 'lon', 'alt', 'yaw'} or None
    5. database_manager      - object exposing get_db() -> DataFrame with
                               columns: entity_type, entity_number, lat, lon,
                               alt, geometry
    6. ALT_DEFAULT           - default way-point altitude (master drone).
    7. SPATIAL_DISTANCE      - required spatial distance between the 2 drones.
    8. DELTA_ALT_SLAVE_DRONE - altitude added to ALT_DEFAULT for the slave.

Design:
    * The user intent (action + target entity) is extracted with the LLM
      (gpt-oss-20b served by vLLM) using guided-JSON decoding, exactly like
      the rest of the project (see llm/llm_manager.py). A deterministic
      fallback parser is used when the LLM endpoint is unreachable.
    * The intent extraction is also exposed as a Google ADK Agent / tool
      (``self.agent``) so it can be orchestrated together with the other
      agents of the system.
    * Way-points are then computed purely in Python from the database
      geometry (point or polygon).
"""

import ast
import json
import math
import logging
from typing import Optional, List, Dict, Any, Tuple

from openai import OpenAI

# ---------------------------------------------------------------------------
# Google ADK (agents / tools). ADK is a mandatory dependency of this module.
# ---------------------------------------------------------------------------
from google.adk import Agent


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TEAM_MEMBER_MASTER = "buddy"
TEAM_MEMBER_SLAVE = "jarvis"
TEAM_MEMBER_TEAM = "team"

# Surround behaviour (used when the target geometry is a single point).
SURROUND_RADIUS_M = 20.0      # radius of the surround circle in meters
SURROUND_NUM_POINTS = 8       # number of way-points around the target

# Word -> digit mapping so the STT text ("two") can be normalised ("2").
_WORD_TO_NUM = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12",
}


class MissionPlannerAgent:
    """Plan drone way-points from an STT text command."""

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #
    def __init__(
        self,
        model_name: str = "openai/gpt-oss-20b",
        base_url: str = "http://localhost:8090/v1",
        api_key: str = "EMPTY",
    ):
        self.model_name = model_name
        self.base_url = base_url

        # OpenAI-compatible client pointing at the local vLLM server.
        try:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        except Exception as exc:  # pragma: no cover
            logging.error("Could not create OpenAI client: %s", exc)
            self.client = None

        # JSON schema used to constrain (guided decoding) the intent output.
        self._intent_schema = {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["goto", "surround", "unknown"],
                },
                "entity_type": {"type": "string"},
                "entity_number": {"type": "string"},
            },
            "required": ["action", "entity_type", "entity_number"],
            "additionalProperties": False,
        }

        self._intent_prompt = (
            "You are a drone flight-command parser.\n"
            "Given a short spoken command, extract:\n"
            "  * action        : 'goto' if the user wants to fly/go/move to a "
            "target, 'surround' if the user wants to surround/circle/orbit a "
            "target, otherwise 'unknown'.\n"
            "  * entity_type   : the kind of target, lower case singular "
            "(e.g. 'building', 'junction'). Empty string if none.\n"
            "  * entity_number : the target number as a string of digits "
            "(convert words to digits, e.g. 'two' -> '2'). Empty string if "
            "none.\n"
            "Return ONLY the JSON object, nothing else."
        )

        # Expose the intent parser as a Google ADK Agent/tool so it can be
        # orchestrated with the rest of the system.
        self.agent = self._build_adk_agent()

    # ------------------------------------------------------------------ #
    # Google ADK agent
    # ------------------------------------------------------------------ #
    def _build_adk_agent(self):
        return Agent(
            name="mission_planner_agent",
            model=self.model_name,
            instruction=(
                "You are an autonomous drone flight planner. Extract the "
                "action (goto/surround) and the target entity "
                "(type + number) from the user command and use the "
                "parse_flight_command tool to obtain the structured "
                "intent."
            ),
            tools=[self.parse_flight_command],
        )

    # ------------------------------------------------------------------ #
    # Intent parsing (LLM + fallback) -- also usable as an ADK tool
    # ------------------------------------------------------------------ #
    def parse_flight_command(self, text_command: str) -> Dict[str, str]:
        """Parse a text command into {action, entity_type, entity_number}.

        This method is registered as a Google ADK tool. It first tries the
        LLM (guided JSON) and gracefully falls back to a rule-based parser.
        """
        intent = self._parse_with_llm(text_command)
        if intent is None:
            intent = self._parse_with_rules(text_command)
        return intent

    def _parse_with_llm(self, text_command: str) -> Optional[Dict[str, str]]:
        if self.client is None:
            return None
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self._intent_prompt},
                    {"role": "user", "content": f"COMMAND: {text_command}"},
                ],
                extra_body={
                    "reasoning_effort": "low",
                    "seed": 0,
                    "guided_json": self._intent_schema,
                },
                temperature=0.0,
                max_tokens=300,
            )
            raw = response.choices[0].message.content
            data = json.loads(raw)
            # Normalise the number (words -> digits) just in case.
            number = str(data.get("entity_number", "")).strip().lower()
            number = _WORD_TO_NUM.get(number, number)
            return {
                "action": str(data.get("action", "unknown")).strip().lower(),
                "entity_type": str(data.get("entity_type", "")).strip().lower(),
                "entity_number": number,
            }
        except Exception as exc:
            logging.warning("LLM intent parsing failed, using fallback: %s", exc)
            return None

    @staticmethod
    def _parse_with_rules(text_command: str) -> Dict[str, str]:
        """Deterministic fallback parser."""
        words = str(text_command).lower().replace(",", " ").split()

        surround_kw = {"surround", "circle", "orbit", "around", "encircle"}
        action = "surround" if any(w in surround_kw for w in words) else "goto"

        # entity number: first plain digit or spelled-out number.
        number = ""
        for w in words:
            if w.isdigit():
                number = w
                break
            if w in _WORD_TO_NUM:
                number = _WORD_TO_NUM[w]
                break

        # entity type: known keyword if present, else default to "building".
        known_types = {"building", "junction", "tower", "house", "car", "cow"}
        entity_type = next((w for w in words if w in known_types), "")
        if not entity_type:
            entity_type = "building"

        if not number:
            action = "unknown"

        return {
            "action": action,
            "entity_type": entity_type,
            "entity_number": number,
        }

    # ------------------------------------------------------------------ #
    # Geometry helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_geometry_string(geom_str: str) -> List[Tuple[float, float]]:
        """Parse a point '[lat, lon]' or polygon '[lat1 lon1, lat2 lon2, ...]'.

        Returns a list of (lat, lon) tuples (empty list on failure).
        """
        cleaned = str(geom_str).strip()
        if not cleaned or cleaned.lower() == "nan":
            return []

        inner = cleaned.strip("[]").strip()

        # Point format with only a comma between the two numbers:
        #   "[47.6395010, -122.141538]"  or  "[47.6395010,-122.141538]"
        if "," in inner and " " not in inner.replace(",", ""):
            try:
                lat_str, lon_str = inner.split(",")[:2]
                return [(float(lat_str), float(lon_str))]
            except Exception:
                pass

        # Polygon / vertices where each vertex is "lat lon" separated by commas:
        #   "[47.64014 -122.1415, 47.64014 -122.1409, ...]"
        points: List[Tuple[float, float]] = []
        for vertex in inner.split(","):
            parts = vertex.strip().split()
            if len(parts) >= 2:
                try:
                    points.append((float(parts[0]), float(parts[1])))
                except Exception:
                    continue

        # Last resort: a clean python literal like "[47.63, -122.14]".
        if not points:
            try:
                coords = ast.literal_eval(cleaned)
                if (
                    isinstance(coords, (list, tuple))
                    and len(coords) == 2
                    and all(isinstance(c, (int, float)) for c in coords)
                ):
                    points = [(float(coords[0]), float(coords[1]))]
            except Exception:
                pass

        return points

    @staticmethod
    def _offset_latlon(
        lat: float, lon: float, d_north_m: float, d_east_m: float
    ) -> Tuple[float, float]:
        """Offset a (lat, lon) by meters north/east (flat-earth approximation)."""
        d_lat = d_north_m / 111_320.0
        d_lon = d_east_m / (111_320.0 * math.cos(math.radians(lat)))
        return lat + d_lat, lon + d_lon

    @staticmethod
    def _prepend_current_location(
            drone_location: Dict[str, float], alt: float
    ) -> List[Tuple[float, float, float]]:
        """Build the starting way-points: current position, then climb straight
        up (same lat/lon) to the target altitude before any lateral movement.
        """
        lat = float(drone_location["lat"])
        lon = float(drone_location["lon"])
        cur_alt = float(drone_location.get("alt", alt))
        return [(lat, lon, cur_alt), (lat, lon, alt)]

    def _surround_waypoints(
        self, center_lat: float, center_lon: float, alt: float
    ) -> List[Tuple[float, float, float]]:
        """Circle of way-points around a single center point."""
        waypoints: List[Tuple[float, float, float]] = []
        for i in range(SURROUND_NUM_POINTS):
            angle = 2.0 * math.pi * i / SURROUND_NUM_POINTS
            d_north = SURROUND_RADIUS_M * math.cos(angle)
            d_east = SURROUND_RADIUS_M * math.sin(angle)
            lat, lon = self._offset_latlon(center_lat, center_lon, d_north, d_east)
            waypoints.append((lat, lon, alt))
        # close the loop
        waypoints.append(waypoints[0])
        return waypoints

    # ------------------------------------------------------------------ #
    # Database lookup
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_target_string(target: str) -> Tuple[str, str]:
        """Split a target string like 'building 2' into (entity_type, entity_number)."""
        if not target:
            return "", ""
        parts = str(target).strip().lower().split()
        if len(parts) < 2:
            return "", ""
        entity_number = parts[-1]
        entity_type = " ".join(parts[:-1])
        return entity_type, entity_number

    @staticmethod
    def _find_entity(database_manager, entity_type: str, entity_number: str):
        """Return the matching DataFrame row or None."""
        df = database_manager.get_db()
        match = df[
            (df["entity_type"].astype(str).str.lower() == str(entity_type).lower())
            & (df["entity_number"].astype(str) == str(entity_number))
        ]
        if match.empty:
            return None
        return match.iloc[0]

    # ------------------------------------------------------------------ #
    # Core way-point computation for a single logical target
    # ------------------------------------------------------------------ #
    def _base_waypoints_for_action(
        self,
        action: str,
        row,
        alt: float,
    ) -> List[Tuple[float, float, float]]:
        """Compute the (lat, lon, alt) way-points for the given action/target."""
        coords = self._parse_geometry_string(row.get("geometry", ""))
        if not coords:
            return []

        if action == "surround":
            if len(coords) > 1:
                # Polygon: fly the boundary vertices, then close the loop.
                waypoints = [(lat, lon, alt) for lat, lon in coords]
                waypoints.append(waypoints[0])
                return waypoints
            # Single point: build a circle around it.
            lat, lon = coords[0]
            return self._surround_waypoints(lat, lon, alt)

        # action == "goto" (default): destination is the first geometry point.
        lat, lon = coords[0]
        return [(lat, lon, alt)]

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def get_way_points(
        self,
        text_command: str,
        team_member: str,
        master_drone_location: Optional[Dict[str, float]],
        slave_drone_location: Optional[Dict[str, float]],
        database_manager,
        ALT_DEFAULT: float,
        SPATIAL_DISTANCE: float,
        DELTA_ALT_SLAVE_DRONE: float,
        last_destination: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Plan the flight and return a structured way-point plan.

        Returns a dict::

            {
                "status": "success" | "error",
                "error":  <str, only on error>,
                "action": "goto" | "surround",
                "target": "building 2",
                "team_member": "team",
                "plan": {
                    "buddy":  [(lat, lon, alt), ...],   # master, or None
                    "jarvis": [(lat, lon, alt), ...],   # slave, or None
                },
            }
        """
        team_member = (team_member or "").strip().lower()
        if team_member not in (TEAM_MEMBER_MASTER, TEAM_MEMBER_SLAVE, TEAM_MEMBER_TEAM):
            return self._error(f"INVALID_TEAM_MEMBER: '{team_member}'.")

        # 1. Understand what the user asked for (LLM + fallback).
        intent = self.parse_flight_command(text_command)
        action = intent.get("action", "unknown")
        entity_type = intent.get("entity_type", "")
        entity_number = intent.get("entity_number", "")

        # No specific destination in the command (e.g. "surround the building") ->
        # fall back to the last known destination, if any.
        if not entity_number:
            fallback_type, fallback_number = self._parse_target_string(last_destination)
            if fallback_number:
                entity_type = fallback_type or entity_type
                entity_number = fallback_number
                if action == "unknown":
                    action = "goto"
                logging.info(
                    f"No explicit destination in '{text_command}', "
                    f"reusing last_destination='{last_destination}'."
                )

        if action == "unknown" or not entity_number:
            return self._error(
                f"PARSE_ERROR: could not understand target in '{text_command}'."
            )

        # 2. Resolve the target from the database (step 7: nothing if missing).
        row = self._find_entity(database_manager, entity_type, entity_number)
        if row is None:
            return self._error(
                f"DESTINATION_NOT_FOUND: '{entity_type} {entity_number}' "
                f"is not in the database."
            )

        target_name = f"{entity_type} {entity_number}"

        # 3. Master altitude = ALT_DEFAULT, slave altitude = +delta.
        master_alt = float(ALT_DEFAULT)
        slave_alt = float(ALT_DEFAULT) + float(DELTA_ALT_SLAVE_DRONE)

        plan: Dict[str, Optional[List[Tuple[float, float, float]]]] = {
            TEAM_MEMBER_MASTER: None,
            TEAM_MEMBER_SLAVE: None,
        }

        # --- buddy: master drone only ------------------------------------
        if team_member == TEAM_MEMBER_MASTER:
            if master_drone_location is None:
                return self._error("NO_MASTER_DRONE: master drone location is not available.")
            wps = self._base_waypoints_for_action(action, row, master_alt)
            if not wps:
                return self._error("INVALID_GEOMETRY: could not parse coordinates.")
            plan[TEAM_MEMBER_MASTER] = self._prepend_current_location(
                master_drone_location, master_alt
            ) + wps

        # --- jarvis: slave drone only ------------------------------------
        elif team_member == TEAM_MEMBER_SLAVE:
            if slave_drone_location is None:
                return self._error("NO_SLAVE_DRONE: slave drone is not available.")
            wps = self._base_waypoints_for_action(action, row, slave_alt)
            if not wps:
                return self._error("INVALID_GEOMETRY: could not parse coordinates.")
            plan[TEAM_MEMBER_SLAVE] = self._prepend_current_location(
                slave_drone_location, slave_alt
            ) + wps

        # --- team: both drones -------------------------------------------
        else:  # TEAM_MEMBER_TEAM
            if master_drone_location is None:
                return self._error("NO_MASTER_DRONE: master drone location is not available.")
            if slave_drone_location is None:
                return self._error("NO_SLAVE_DRONE: team flight needs two drones.")

            master_wps = self._base_waypoints_for_action(action, row, master_alt)
            if not master_wps:
                return self._error("INVALID_GEOMETRY: could not parse coordinates.")

            # Slave follows the same path but is shifted so that the *spatial*
            # (3D) distance between the drones equals SPATIAL_DISTANCE, taking
            # the altitude difference (DELTA_ALT_SLAVE_DRONE) into account.
            slave_wps = self._apply_spatial_offset(
                master_wps,
                slave_alt,
                spatial_distance=float(SPATIAL_DISTANCE),
                delta_alt=float(DELTA_ALT_SLAVE_DRONE),
            )
            plan[TEAM_MEMBER_MASTER] = self._prepend_current_location(
                master_drone_location, master_alt
            ) + master_wps
            plan[TEAM_MEMBER_SLAVE] = self._prepend_current_location(
                slave_drone_location, slave_alt
            ) + slave_wps

        return {
            "status": "success",
            "action": action,
            "target": target_name,
            "team_member": team_member,
            "plan": plan,
        }

    # ------------------------------------------------------------------ #
    # Team spatial-offset helper
    # ------------------------------------------------------------------ #
    def _apply_spatial_offset(
        self,
        master_wps: List[Tuple[float, float, float]],
        slave_alt: float,
        spatial_distance: float,
        delta_alt: float,
    ) -> List[Tuple[float, float, float]]:
        """Shift the master path to obtain the slave path.

        The horizontal separation is chosen so that the 3D (spatial) distance
        between the two drones equals ``spatial_distance`` given the vertical
        separation ``delta_alt``.
        """
        remaining = spatial_distance ** 2 - delta_alt ** 2
        horizontal = math.sqrt(remaining) if remaining > 0 else spatial_distance

        slave_wps: List[Tuple[float, float, float]] = []
        for lat, lon, _ in master_wps:
            # offset horizontally towards the east by `horizontal` meters.
            s_lat, s_lon = self._offset_latlon(lat, lon, 0.0, horizontal)
            slave_wps.append((s_lat, s_lon, slave_alt))
        return slave_wps

    # ------------------------------------------------------------------ #
    # Utils
    # ------------------------------------------------------------------ #
    @staticmethod
    def _error(message: str) -> Dict[str, Any]:
        logging.error(message)
        return {
            "status": "error",
            "error": message,
            "action": None,
            "target": None,
            "plan": {TEAM_MEMBER_MASTER: None, TEAM_MEMBER_SLAVE: None},
        }


# --------------------------------------------------------------------------- #
# Manual smoke test
# --------------------------------------------------------------------------- #


def parse_coords(s):
    nums = list(map(float, s.strip('[]').replace(',', ' ').split()))
    if len(nums) % 2 != 0:
        raise ValueError("Odd number of coordinates")
    return list(zip(nums[::2], nums[1::2]))

def init_monitor(base_url, df, master, slave):

    _post(base_url, "/api/reset", {})


    post_master_pos(base_url, lat=master['lat'], lon=master['lon'], alt=master['alt'])
    post_slave_pos(base_url, lat=slave['lat'], lon=slave['lon'], alt=slave['alt'])


    for i in range(len(df)):
        entity_name = df.iloc[i]["entity_type"]
        entity_number = df.iloc[i]["entity_number"]
        entity = f"{entity_name}_{entity_number}"
        lat = df.iloc[i]["lat"]
        lon = df.iloc[i]["lon"]
        alt = df.iloc[i]["alt"]

        str_cords = df.iloc[i]['geometry']
        coords = parse_coords(str_cords)
        for coord in coords:
            post_waypoint(base_url, lat=coord[0], lon=coord[1], alt=15, title=entity)


if __name__ == "__main__":
    # Use the real project DatabaseManager (reads the CSV configured in
    # app_config/conf.yaml). Run this file from the ``project_code`` folder so
    # that the relative config path resolves correctly.
    from project_code.db.database_manager import DatabaseManager
    import time

    missionPlannerAgent = MissionPlannerAgent()
    db     = DatabaseManager()
    base_url = "http://127.0.0.1:5052"

    # Assumed current location for both drones.
    # master = {"lat": 47.6399500, "lon": -122.1416800, "alt": 0, "yaw": 0}
    # slave = {"lat": 47.6399949, "lon": -122.1416133, "alt": 0, "yaw": 0}
    master = {"lat": 47.6399500, "lon": -122.1416800, "alt": 0}
    slave = {"lat": 47.6399949, "lon": -122.1416133, "alt": 0}

    #init_monitor(base_url, db.get_db(), master, slave)


    tests = [
        ("return home", "team", master, None),
        ("go to building number two", "buddy", master, None),
        ("surround building number one", "team", master, slave),
        ("jarvis fly to building number 2", "jarvis", master, slave),
        ("go to building number 99", "buddy", master, None),
        ("please fly to building number 4", "buddy", master, None)
    ]

    for cmd, member, m_loc, s_loc in tests:
        print("=" * 70)
        print(f"CMD='{cmd}'  member='{member}'")
        start_time = time.time()
        result = missionPlannerAgent.get_way_points(
            text_command=cmd,
            team_member=member,
            master_drone_location=m_loc,
            slave_drone_location=s_loc,
            database_manager=db,
            ALT_DEFAULT=20.0,
            SPATIAL_DISTANCE=5.0,
            DELTA_ALT_SLAVE_DRONE=3.0,
        )
        end_time = time.time()
        print(f"\tTotal time: {(end_time - start_time):.2f} seconds")

        #add_path_to_monitor(base_url, result)

        print(json.dumps(result, indent=2))

