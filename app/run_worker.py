import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def main() -> None:
    log_level = os.getenv("WORKER_LOG_LEVEL", "INFO")
    queues = os.getenv("WORKER_QUEUES", "image_jobs,billing,notifications")
    command = [
        "celery",
        "-A",
        "app.workers.celery_app",
        "worker",
        "-l",
        log_level,
        "-Q",
        queues,
    ]
    raise SystemExit(subprocess.call(command))


if __name__ == "__main__":
    main()
