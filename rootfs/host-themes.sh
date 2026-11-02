#!/bin/bash
# Runs on the BUILD HOST (native x86, no qemu) as an mmdebstrap customize hook, before customize.sh.
#   host-themes.sh <rootfs>
# Installs the WhiteSur GTK/xfwm4 themes (the base of the KidsOS themes; no icons) straight into the image tree. Themes are only text and
# images, so they do not care which architecture they were built on. Doing it here instead of inside the armhf
# chroot avoids qemu problems with sassc, and a failure now stops the build with the full log (it used to be
# swallowed by "|| true", which produced images without WhiteSur: no window frames, themes without a base).
set -euo pipefail
ROOT=${1:?usage: host-themes.sh <rootfs>}
export TERM=xterm USER=root HOME=${HOME:-/root}

T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
mkdir -p "$ROOT/usr/share/themes"

git clone --depth 1 https://github.com/vinceliuice/WhiteSur-gtk-theme  "$T/gtk"
git -C "$T/gtk"   rev-parse HEAD > "$ROOT/usr/share/fleet-theme-gtk.rev"

echo "== WhiteSur GTK theme (log: last lines)"
if ! ( cd "$T/gtk" && ./install.sh -d "$ROOT/usr/share/themes" -n WhiteSur -c light -o normal ) > "$T/gtk.log" 2>&1; then
  echo "ERROR: WhiteSur GTK install failed. Full log:"; cat "$T/gtk.log"; exit 1
fi
tail -5 "$T/gtk.log"

# Verify what the rest of the build and the KidsOS themes rely on
for d in WhiteSur-Light; do
  [ -f "$ROOT/usr/share/themes/$d/gtk-3.0/gtk.css" ] || { echo "ERROR: $d/gtk-3.0/gtk.css missing"; ls "$ROOT/usr/share/themes"; cat "$T/gtk.log"; exit 1; }
  [ -f "$ROOT/usr/share/themes/$d/xfwm4/themerc" ]   || { echo "ERROR: $d/xfwm4/themerc missing (window frames)"; exit 1; }
done

# The WhiteSur themes are only the BASE of the KidsOS themes. Move them out of /usr/share/themes so that the
# appearance settings list nothing but "KidsOS ..." (the generated themes import the base from fleet-base, and
# link its window-frame theme).
mkdir -p "$ROOT/usr/share/fleet-base/themes"
for d in "$ROOT"/usr/share/themes/WhiteSur-*; do mv "$d" "$ROOT/usr/share/fleet-base/themes/"; done
echo "WhiteSur base themes: $(ls "$ROOT/usr/share/fleet-base/themes" | tr '\n' ' ')"
