import subprocess


def main() -> None:
    raise SystemExit(subprocess.call(["alembic", "-c", "alembic.ini", "upgrade", "head"]))


if __name__ == "__main__":
    main()
