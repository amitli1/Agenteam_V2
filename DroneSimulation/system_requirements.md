I want you to build drone simulation.
General requirements:
1. use python
2. use current simulation.yaml 
3. you will use rest api to control the drone (start mission, return to home, etc.)
4. you will use websockets to send telemetry data to the client every 1 second.

Rest API requirements:
1. /mission
   1.1 post request.
   1.2 input: list of waypoints (lat, lon, alt).
   1.3 every mission_step_duration (from simulation.yaml) seconds, the drone will go to the next waypoint. After reaching the last waypoint.
   1.4 each cell in the array is json (lat, lon, alt)
    
2. /return
   2.1 post request.
   2.2 no parameters 
   2.3 return the drone to home position (lat, lon, alt) from simulation.yaml.
   2.4 after mission_step_duration (from simulation.yaml) seconds, the drone is back to home position.

3. The restAPI will be running on localhost with the port specified in simulation.yaml (quad_port).


Websockets requirements:
1. you are the server.
2. every 1 second, send the following telemetry json data to the client: 
   'timestamp': current time in milliseconds, 
   'is_armed': False, 
   'flight_mode': 'HOLD' or 'MISSION'. change to 'MISSION' when the mission is started (got post request to /mission) (after 3 seconds return back to 'HOLD').
   'lat': current latitude, calculated based on the current waypoint and the time elapsed since the last waypoint was reached.
   'lon': current longitude, calculated based on the current waypoint and the time elapsed since the last waypoint was reached.
   'alt': current altitude,, calculated based on the current waypoint and the time elapsed since the last waypoint was reached.
   'yaw': current yaw,
   'horizontal_velocity': 1.0, 
   'vertical_velocity': 1.0,
   'battery_voltage': 50.0, 
   'in_air': True, 
   'is_mission_finished': True if got post request to /mission and the mission is finished, False otherwise,
   'mission_progress': '0/0'. when user sends a post request to /mission, update the mission_progress to 'current_waypoint_index/total_waypoints'. After reaching the last waypoint, set is_mission_finished to True and mission_progress to 'total_waypoints/total_waypoints'.

Running requirements:
1. we can run simulation.py to start the simulation.
2. we can run docker and dockercompose (with the configuration in simulation.yaml) to run the simulation in a containerized environment.