import platform


def get_system_info():
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
    }
