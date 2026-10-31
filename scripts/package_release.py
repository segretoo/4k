"""Package committed source plus built frontend with portable Linux permissions."""
import argparse
import io
from pathlib import Path
import subprocess
import tarfile


def portable(member):
    member.mode = 0o755 if member.isdir() else 0o644
    member.uid = member.gid = 0
    member.uname = member.gname = ""
    member.pax_headers = {}
    return member


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if not (root / "frontend/dist/index.html").is_file():
        raise SystemExit("Build the frontend before packaging")
    tracked = subprocess.run(["git", "archive", "HEAD"], cwd=root, check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(tracked)) as source, tarfile.open(args.out, "w:gz") as target:
        for member in source:
            target.addfile(portable(member), source.extractfile(member) if member.isfile() else None)
        target.add(root / "frontend/dist", arcname="frontend/dist", filter=portable)
    print(args.out)


if __name__ == "__main__":
    main()
