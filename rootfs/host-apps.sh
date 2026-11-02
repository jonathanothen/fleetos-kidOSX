#!/bin/bash
# Runs on the BUILD HOST as an mmdebstrap customize hook, before customize.sh.
#   host-apps.sh <rootfs>
# Fetches Snap! (block-based programming, runs offline in Firefox) into /usr/share/kidsos/snap.
# Scratch has no armhf package and its web app needs a node build; Snap! is plain static HTML + JS.
set -euo pipefail
ROOT=${1:?usage: host-apps.sh <rootfs>}
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
git clone --depth 1 https://github.com/jmoenig/Snap "$T/snap"
D="$ROOT/usr/share/kidsos/snap"
mkdir -p "$D"
git -C "$T/snap" rev-parse HEAD > "$ROOT/usr/share/kidsos/snap.rev"
rm -rf "$T/snap/.git" "$T/snap/.github" "$T/snap/help"
cp -a "$T/snap/." "$D/"
[ -f "$D/snap.html" ] || { echo "ERROR: snap.html missing after copy"; ls "$D"; exit 1; }
ls "$D/locale/lang-sv.js" >/dev/null || { echo "ERROR: Swedish translation for Snap! missing"; exit 1; }
du -sh "$D"