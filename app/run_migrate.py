
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def main() -> None:
    raise SystemExit(subprocess.call(["alembic", "-c", "alembic.ini", "upgrade", "head"]))


if __name__ == "__main__":
    main()
