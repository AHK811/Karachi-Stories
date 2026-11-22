import hashlib
import json
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]

MANIFEST = _ROOT / "GIS/validation/osmdata_download_manifest.json"
SRC = _ROOT / "GIS/source/osmdata"


def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ok = True
    for r in man["downloads"]:
        p = SRC / r["file"]
        if not p.exists():
            print(f"  {r['file']}: MISSING")
            ok = False
            continue
        got = sha256(p)
        size_ok = p.stat().st_size == r["expected_bytes"]
        sha_ok = got == r["sha256"]
        ok &= size_ok and sha_ok
        print(f"  {r['file']}:")
        print(f"    size      {p.stat().st_size:>12,} expected {r['expected_bytes']:>12,}  match={size_ok}")
        print(f"    sha256    {got}")
        print(f"    manifest  {r['sha256']}  match={sha_ok}")
    print("RESULT: ALL ARCHIVES VERIFIED" if ok else "RESULT: VERIFICATION FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
