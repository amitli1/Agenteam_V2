#!/bin/bash
set -euo pipefail

CONFIG_FILE="${DASHBOARD_CONFIG:-/app/config.yaml}"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "ERROR: config file not found at $CONFIG_FILE" >&2
  exit 1
fi

# Extract sudo username/password from config.yaml using python (PyYAML already installed)
read -r SUDO_USER SUDO_PASS <<EOF
$(python3 - "$CONFIG_FILE" <<'PYEOF'
import sys, yaml
with open(sys.argv[1]) as f:
    cfg = yaml.safe_load(f) or {}
sudo_cfg = cfg.get("sudo", {}) or {}
print(sudo_cfg.get("username", "dashboard"), sudo_cfg.get("password", "dashboard"))
PYEOF
)
EOF

if [ -z "${SUDO_USER}" ]; then
  SUDO_USER="dashboard"
fi
if [ -z "${SUDO_PASS}" ]; then
  SUDO_PASS="dashboard"
fi

# Create the configured user if it doesn't already exist
if ! id -u "$SUDO_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "$SUDO_USER"
fi

echo "${SUDO_USER}:${SUDO_PASS}" | chpasswd

# Allow this user to run sudo
usermod -aG sudo "$SUDO_USER"

# Give access to the mounted docker socket regardless of host group id mismatches
if [ -S /var/run/docker.sock ]; then
  chmod 666 /var/run/docker.sock || true
fi

# Best-effort ownership change. The config file is typically bind-mounted
# read-only from the host, so chown on it (and anything else we can't touch)
# is expected to fail there - that must not abort the whole script.
chown -R "$SUDO_USER":"$SUDO_USER" /app 2>/dev/null || true

# Make sure the app files are at least readable/executable by the target user
# even if chown above couldn't take effect on some of them (e.g. read-only mounts).
chmod -R a+rX /app 2>/dev/null || true

echo "Starting Dockers Dashboard as user '$SUDO_USER'..."
exec su -s /bin/bash "$SUDO_USER" -c "python3 /app/app.py"

