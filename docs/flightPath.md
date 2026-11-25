# flightPath configuration (app_config/conf.yaml)

## `point_toward_structure_center`

Controls the yaw (heading) used at each waypoint of a **surround** mission around a
multi-point structure/polygon:

- **`true`** – at every waypoint around the structure, the drone yaw points directly
  toward the **centroid** of the structure (bearing from the waypoint to the
  centroid).
- **`false`** – the drone yaw is set **perpendicular to the polygon edge** it is
  currently flying along (facing inward, toward the structure), instead of pointing
  at the centroid. This is computed by `_perpendicular_edge_yaw(...)`.

This only affects the `"surround"` action and only when the target structure has
more than one coordinate (a polygon). For a single point target, or for a `"goto"`
action, this flag has no effect.

## `use_enu_edge_yaw_calculation`

Only relevant when `point_toward_structure_center` is `false` (i.e. when the
perpendicular-edge-yaw logic is used). It selects **how** the ±90° perpendicular
candidates to an edge are computed:

- **`false` (default)** – the perpendicular candidates are computed by adding/
  subtracting 90° directly in the North-based bearing convention
  (0° = North, clockwise) used throughout the mission planner.
- **`true`** – the edge bearing is first converted from the North convention to the
  **ENU** (East-North-Up) convention (0° = East, clockwise), the ±90° candidates are
  computed in ENU, and the result is converted back to the North-based convention
  before picking the inward-facing candidate.

Both approaches should, in principle, produce the same perpendicular directions —
this flag exists mainly to make the intermediate coordinate system explicit/
switchable for testing and comparison, not to change the final selection logic
(the inward candidate is still chosen the same way in both cases).

## Relation between the two flags

- `point_toward_structure_center` decides **whether** the perpendicular-edge yaw
  calculation is used at all (it is only used when this flag is `false`).
- `use_enu_edge_yaw_calculation` only matters **inside** that perpendicular-edge
  calculation — it has **no effect** when `point_toward_structure_center` is `true`,
  since in that case the yaw is simply the bearing to the centroid and no edge/ENU
  math is involved.

In short: `point_toward_structure_center` is the higher-level switch (centroid vs.
edge-perpendicular yaw), and `use_enu_edge_yaw_calculation` is a lower-level detail
that only applies to the edge-perpendicular branch.

