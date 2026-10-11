# Point status:
# 1. to stop pointing - just send prompt ""
```
{
    "session": {
        "id": "shm_session_1791702973",
        "is_active": true,
        "mode": "video",
        "uptime_seconds": 0
    },
    "agent": {
        "status": "idle",
        "running": true,
        "prompt": null,
        "prompt_count": 0
    },
    "tools": {
        "pointing": {
            "healthy": true,
            "model_path": "/data/pointing_head_v3/snapshots/pointing_v3",
            "base_url": "http://localhost:8000/v1",
            "response_ms": 3.29,
            "error": null
        },
        "tracking": {
            "type": null,
            "healthy": false,
            "config": null
        }
    },
    "lock_state": {
        "has_stable_lock": false,
        "has_pending_candidates": false,
        "pending_count": 0,
        "current_point": null,
        "frame_id": null
    },
    "source": {
        "type": "shared_memory",
        "connection_status": "reconnecting (attempt 2)",
        "fps_in": null,
        "fps_target": 30,
        "fps_processing": 0.0,
        "resolution": [
            640,
            480
        ],
        "frames_total": 0,
        "frames_processed": 0,
        "reconnect_count": 2
    },
    "progress": {
        "current_frame": 0,
        "total_frames": null,
        "percentage": null
    },
    "result": {
        "frame_id": null,
        "tracked_point": null,
        "status": null,
        "solution_source": null
    }
}
```