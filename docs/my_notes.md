# Camera:
1. 640*480
2. Blue robotics camera

# Follow:
1. To initiate tracking:
   1.1  Send a point command for the target object.
   1.2 Send the start_tracking() command to QUAD (with an empty body).
2. Only the pointing agent knows which target to point at (i.e., track). QUAD follows the target's XYZ position without knowing the target's name.
3. The tracking algorithm is based on the target's XYZ position, which is obtained directly from the pointing agent's status messages, not from me.