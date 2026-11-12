# flightPath
1. default_drone_altitude: - alt for master drone (buddy)
2. spatial_distance: - distance (team) in xy
3. slave_drone_altitude_offset: 
   (default_drone_altitude+slave_drone_altitude_offset) alt for slave drone (jarvis)
4. point_toward_structure_center: when surrounding structure, point toward center of structure (true/false)
5. sleep_time_between_team_members_sec: (time to wait before jarvis starts moving after buddy has moved)

Notes:
1. Distance betwween drones is measured in xy plane + (altitude) (NOT TOTAL DISTANCE).

