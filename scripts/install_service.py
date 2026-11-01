"""Install one CPU or GPU systemd service using an existing Python environment."""
import argparse
import getpass
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=["cpu", "gpu"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root, python = args.root.resolve(), args.python.absolute()
    work = root / ("backend" if args.role == "cpu" else "ml/gpu_server")
    env = root / ".env" if args.role == "cpu" else work / ".env"
    if any(any(char.isspace() for char in str(path)) for path in (root, python)):
        raise SystemExit("Deployment paths must not contain whitespace")
    if not args.dry_run and (not python.is_file() or not env.is_file()):
        raise SystemExit("Python environment and private .env must exist first")
    app = "app.main:app" if args.role == "cpu" else "app:app"
    port = 8000 if args.role == "cpu" else 8080
    limit = " --limit-concurrency 8" if args.role == "cpu" else ""
    unit = f"""[Unit]
Description=Kkokkok {args.role} API
After=network-online.target
Wants=network-online.target

[Service]
User={getpass.getuser()}
WorkingDirectory={work}
EnvironmentFile={env}
Environment=PYTHONUNBUFFERED=1
ExecStart={python} -m uvicorn {app} --host 0.0.0.0 --port {port} --workers 1 --no-access-log{limit}
Restart=on-failure
RestartSec=5
TimeoutStartSec=300
TimeoutStopSec=60
UMask=0077

[Install]
WantedBy=multi-user.target
"""
    if args.dry_run:
        print(unit)
        return
    name = f"kkokkok-{args.role}.service"
    generated = root / name
    generated.write_text(unit, encoding="utf-8")
    subprocess.run(["sudo", "-n", "install", "-m", "0644", str(generated),
                    f"/etc/systemd/system/{name}"], check=True)
    subprocess.run(["sudo", "-n", "systemctl", "daemon-reload"], check=True)
    subprocess.run(["sudo", "-n", "systemctl", "enable", "--now", name], check=True)


if __name__ == "__main__":
    main()
