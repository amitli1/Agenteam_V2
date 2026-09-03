"""
Dockers Dashboard
=================
A small Flask web app that:
  1. Lists the currently running docker containers ("sudo docker ps") in a table.
  2. Streams the logs of a chosen container ("sudo docker logs -f ...") in its own
     browser tab, using Server-Sent Events (SSE).

The sudo user/password and the web server port are read from config.yaml.
"""

import json
import os
import subprocess
import threading
import time
from pathlib import Path

import yaml
from flask import Flask, Response, jsonify, render_template, stream_with_context

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.environ.get("DASHBOARD_CONFIG", BASE_DIR / "config.yaml"))

app = Flask(__name__)

_config_lock = threading.Lock()
_config_cache = {"mtime": None, "data": None}


def load_config():
    """Load config.yaml, caching it and reloading if the file changed on disk."""
    with _config_lock:
        try:
            mtime = CONFIG_PATH.stat().st_mtime
        except FileNotFoundError:
            mtime = None

        if _config_cache["data"] is None or _config_cache["mtime"] != mtime:
            with open(CONFIG_PATH, "r") as f:
                data = yaml.safe_load(f) or {}
            _config_cache["data"] = data
            _config_cache["mtime"] = mtime

        return _config_cache["data"]


def get_sudo_credentials():
    cfg = load_config()
    sudo_cfg = cfg.get("sudo", {}) or {}
    return sudo_cfg.get("username", ""), sudo_cfg.get("password", "")


def get_web_settings():
    cfg = load_config()
    web_cfg = cfg.get("web", {}) or {}
    return web_cfg.get("host", "0.0.0.0"), int(web_cfg.get("port", 6179))


def get_docker_settings():
    cfg = load_config()
    docker_cfg = cfg.get("docker", {}) or {}
    return {
        "refresh_seconds": int(docker_cfg.get("refresh_seconds", 5)),
        "log_tail_lines": int(docker_cfg.get("log_tail_lines", 200)),
    }


def run_sudo_command(args, timeout=15):
    """Run a command with `sudo -S`, feeding the configured sudo password on stdin."""
    _, password = get_sudo_credentials()
    cmd = ["sudo", "-S", "-p", ""] + args
    try:
        proc = subprocess.run(
            cmd,
            input=(password + "\n").encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1

    stdout = proc.stdout.decode(errors="replace")
    stderr = proc.stderr.decode(errors="replace")
    return stdout, stderr, proc.returncode


def list_running_containers():
    """Return a list of dicts describing currently running containers."""
    fmt = "{{json .}}"
    stdout, stderr, code = run_sudo_command(["docker", "ps", "--format", fmt])

    if code != 0:
        return [], stderr.strip() or "Failed to run 'docker ps'"

    containers = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            containers.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return containers, None


@app.route("/")
def index():
    host, port = get_web_settings()
    docker_settings = get_docker_settings()
    return render_template(
        "index.html",
        refresh_seconds=docker_settings["refresh_seconds"],
        web_port=port,
    )


@app.route("/api/containers")
def api_containers():
    containers, error = list_running_containers()
    return jsonify({"containers": containers, "error": error})


@app.route("/logs/<container_id>")
def logs_page(container_id):
    containers, _ = list_running_containers()
    name = container_id
    for c in containers:
        if c.get("ID") == container_id or c.get("Names") == container_id:
            name = c.get("Names") or c.get("ID")
            container_id = c.get("ID")
            break
    return render_template("logs.html", container_id=container_id, container_name=name)


@app.route("/stream/<container_id>")
def stream_logs(container_id):
    """Server-Sent Events endpoint streaming `sudo docker logs -f <container_id>`."""
    _, password = get_sudo_credentials()
    docker_settings = get_docker_settings()
    tail = str(docker_settings["log_tail_lines"])

    def generate():
        cmd = ["sudo", "-S", "-p", "", "docker", "logs", "-f", "--tail", tail, container_id]
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        try:
            proc.stdin.write(password + "\n")
            proc.stdin.flush()
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass

        yield "event: open\ndata: connected\n\n"

        try:
            for line in iter(proc.stdout.readline, ""):
                if line == "":
                    break
                safe_line = line.rstrip("\n").replace("\r", "")
                yield f"data: {safe_line}\n\n"
        except GeneratorExit:
            proc.kill()
            raise
        finally:
            if proc.poll() is None:
                proc.terminate()
                time.sleep(0.2)
                if proc.poll() is None:
                    proc.kill()

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


if __name__ == "__main__":
    web_host, web_port = get_web_settings()
    app.run(host=web_host, port=web_port, threaded=True)

