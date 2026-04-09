import os
import subprocess
import sys


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
