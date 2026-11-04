                    STRAIGHT AHEAD
                         YAW = 0°
                            ↑
                            |
             LEFT           |           RIGHT
          YAW = -45°        |        YAW = +45°
                ↖           |           ↗
                  \         |         /
                   \        |        /
                    \       |       /
                     \      |      /
                      \     |     /
                       \    |    /
                        \   |   /
                         \  |  /
                          \ | /
                           \|/
                        YOU / CAMERA




| Direction          | Yaw Value       |
|--------------------|-----------------|
| Straight ahead     | 0°              |
| 45° right          | +45°            |
| 45° left           | -45°            |
| 90° right          | +90°            |
| 90° left           | -90°            |
| 180° (backward)    | 180° or -180°   |


## Logic:
For the 'fly' command:
1. If the YAW value is NaN, the drone flies with its YAW oriented toward the direction of flight.
2. If a specific YAW value is provided, the drone travels to the destination (with its YAW oriented toward the direction of flight) and then adjusts the YAW upon arrival.

For an surround:
1. Throughout the entire orbit, the drone remains oriented toward the center of the structure (which results in a slight tilt for the camera).

In the QUAD API:
1. The 'mission' command can be issued either with or without a YAW value.
2. If no YAW value is provided, the drone flies with the camera facing forward.
3. If a YAW value is provided, the drone flies according to that YAW. 