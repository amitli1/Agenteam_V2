#!/bin/sh
# Patches app_config/conf.yaml's general.run_as_master value (if RUN_AS_MASTER is set)
# before starting the air service. This lets docker-compose control whether this
# container behaves as the master or the slave drone without editing conf.yaml.
set -e

CONF_FILE="/app/app_config/conf.yaml"

if [ -n "${RUN_AS_MASTER}" ]; then
    python - "$CONF_FILE" "$RUN_AS_MASTER" <<'PYEOF'
import sys
import yaml

conf_file, run_as_master = sys.argv[1], sys.argv[2]

with open(conf_file, "r") as f:
    data = yaml.safe_load(f)

data.setdefault("general", {})["run_as_master"] = run_as_master.strip().lower() in ("1", "true", "yes", "on")

with open(conf_file, "w") as f:
    yaml.safe_dump(data, f, sort_keys=False)
PYEOF
    echo "[entrypoint] general.run_as_master set to: ${RUN_AS_MASTER}"
fi

exec "$@"

