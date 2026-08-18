import platform

def is_intel() -> bool:
    """
    Returns True if running on an Intel (x86_64) machine,
    False if running on Jetson (aarch64/arm) or any other architecture.
    """
    machine = platform.machine().lower()
    return machine in ("x86_64", "amd64")