#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIR="$ROOT"/GIS/source/osmdata
MANIFEST="$ROOT"/GIS/validation/osmdata_download_manifest.json
mkdir -p "$DIR"

declare -A EXPECT=(
  [land-polygons-split-4326.zip]=930863091
  [water-polygons-split-4326.zip]=908939540
)
BASE=https://osmdata.openstreetmap.de/download

START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
rm -f /tmp/osmdata_dl.txt
FAILED=0
for F in land-polygons-split-4326.zip water-polygons-split-4326.zip; do
  URL="$BASE/$F"
  WANT=${EXPECT[$F]}
  echo "=== $F (expected $WANT bytes)"
  S=$(date +%s.%N)
  curl -fL --retry 3 --retry-delay 5 -C - --max-time 7200 \
       --progress-bar -o "$DIR/$F" "$URL"
  RC=$?
  E=$(date +%s.%N)
  GOT=$(stat -c%s "$DIR/$F" 2>/dev/null || echo 0)
  if [ "$RC" -ne 0 ]; then echo "  curl rc=$RC"; FAILED=1; fi
  if [ "$GOT" -ne "$WANT" ]; then echo "  SIZE MISMATCH got=$GOT want=$WANT"; FAILED=1; fi
  SHA=$(sha256sum "$DIR/$F" | awk '{print $1}')
  echo "  bytes=$GOT  sha256=$SHA  seconds=$(printf %.0f "$(echo "$E-$S" | bc)")"
  printf '%s\n' "$F|$URL|$WANT|$GOT|$SHA|$(printf %.0f "$(echo "$E-$S" | bc)")" >> /tmp/osmdata_dl.txt
done

END=$(date -u +%Y-%m-%dT%H:%M:%SZ)
python3 - "$START" "$END" "$FAILED" <<'PY'
import json, sys
start, end, failed = sys.argv[1], sys.argv[2], int(sys.argv[3])
rows = []
try:
    for line in open('/tmp/osmdata_dl.txt'):
        f, url, want, got, sha, secs = line.strip().split('|')
        rows.append({"file": f, "url": url, "expected_bytes": int(want), "actual_bytes": int(got),
                     "sha256": sha, "seconds": int(secs),
                     "size_matches": int(want) == int(got),
                     "throughput_mbps": round(int(got) / max(int(secs), 1) / 1e6, 2)})
except FileNotFoundError:
    pass
doc = {"started_utc": start, "finished_utc": end, "failures": failed,
       "licence": "ODbL", "source_service": "osmdata.openstreetmap.de",
       "downloads": rows,
       "publisher_warnings": ["Some errors in the OSM data are repaired.",
                              "If the OSM data can't be repaired automatically, the data here will not be updated."]}
open('"$ROOT"/GIS/validation/osmdata_download_manifest.json', 'w').write(json.dumps(doc, indent=1))
print("manifest written; failures =", failed)
for r in rows:
    print(f"  {r['file']:<32} {r['actual_bytes']:>12,}  {r['throughput_mbps']:>6} MB/s  size_matches={r['size_matches']}")
PY
exit $FAILED
