#!/bin/bash
# Runs INSIDE the armhf chroot after the packages are installed.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# --- Locale, time, keyboard (Swedish default; Nordic layouts switchable) ---
sed -i 's/^# *sv_SE.UTF-8/sv_SE.UTF-8/; s/^# *en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen
locale-gen
update-locale LANG=sv_SE.UTF-8
ln -sf /usr/share/zoneinfo/Europe/Stockholm /etc/localtime
echo Europe/Stockholm > /etc/timezone
# /etc/default/keyboard comes from the overlay; apply to the console
setupcon --save-only 2>/dev/null || true

# --- Users ---
# No built-in account and no shared password. The first user is created by the
# first-boot wizard (fleet-setup.service). root has no password (locked).
echo "kidsos" > /etc/hostname
echo "127.0.1.1 kidsos" >> /etc/hosts
# Group that lets the child sign in without a password (autologin and the login screen); see fleet-setup-gui
groupadd --system nopasswdlogin
grep -q pam_nologin /etc/pam.d/lightdm || { echo "ERROR: unexpected /etc/pam.d/lightdm"; exit 1; }
sed -i '/pam_nologin.so/a auth    sufficient      pam_succeed_if.so user ingroup nopasswdlogin' /etc/pam.d/lightdm

# --- Kernel (our own build, drivers built in) ---
apt-get -y install initramfs-tools
mkdir -p /etc/initramfs-tools
echo "update_initramfs=no" > /etc/initramfs-tools/update-initramfs.conf   # no initramfs needed
apt-get -y install /tmp/linux-image-*.deb
rm -f /tmp/linux-image-*.deb

# --- Look: WhiteSur window frames + GTK base, two colourful KidsOS themes on top ---
# WhiteSur is installed on the build host by rootfs/host-themes.sh (a mmdebstrap hook that runs before this script).
# Stop here if it is missing: without it there are no window frames and no base for the KidsOS themes.
[ -f /usr/share/fleet-base/themes/WhiteSur-Light/gtk-3.0/gtk.css ] || { echo "ERROR: WhiteSur-Light is missing (host-themes.sh failed?)"; exit 1; }
[ -d /usr/share/kidsos/snap ] || { echo "ERROR: Snap! is missing (host-apps.sh failed?)"; exit 1; }
chmod +x /usr/local/sbin/fleet-theme-gen /usr/local/bin/fleet-theme /usr/local/bin/fleet-look
/usr/local/sbin/fleet-theme-gen
# The colour settings should list KidsOS themes only
find /usr/share/themes -mindepth 1 -maxdepth 1 ! -name 'KidsOS*' -exec rm -rf {} +
ls /usr/share/themes | tr '\n' ' '; echo
[ "$(ls -d /usr/share/themes/KidsOS* | wc -l)" -eq 2 ] || { echo "ERROR: expected 2 KidsOS themes"; exit 1; }

# Refresh the icon cache so the KidsOS icons (added by the overlay) are found by name
# The old coloured Wi-Fi PNGs would win over our flat SVG icons
rm -f /usr/share/icons/hicolor/*/apps/nm-signal-*.png /usr/share/icons/hicolor/*/apps/nm-no-connection*.png
gtk-update-icon-cache -f /usr/share/icons/hicolor || true

# --- Child-safe desktop ---
# The start screen (big tiles) replaces desktop icons; it is a GTK3 python program
chmod +x /usr/local/bin/kidsos-home /usr/local/bin/fleet-volume /usr/local/bin/fleet-osd /usr/local/bin/kids-math
# Our own games: pygame must import, and the game content must be there
python3 -c "import pygame" || { echo "ERROR: python3-pygame missing"; exit 1; }
[ -d /usr/share/kidsos/games/assets/voices/sv ] || { echo "ERROR: game voices missing"; exit 1; }
ls /usr/lib/*/gdk-pixbuf-2.0/2.10.0/loaders/ | grep -q svg || { echo "ERROR: SVG pixbuf loader missing (librsvg2-common): every icon would be blank"; exit 1; }
python3 -c "import gi; gi.require_version(\"Gtk\",\"3.0\"); from gi.repository import Gtk" || { echo "ERROR: python3-gi / GTK3 bindings missing"; exit 1; }
# The programs the launchers start must exist at these paths (a typo here would give the child dead icons)
for b in /usr/bin/tuxpaint /usr/bin/firefox-esr /usr/games/gcompris-qt /usr/bin/parole /usr/bin/thunar \
         /usr/games/tuxmath /usr/games/tuxtype /usr/bin/thonny; do
  [ -x "$b" ] || { echo "ERROR: $b is missing (wrong path or package?)"; exit 1; }
done
# No terminal for the child: only members of the sudo group (the parent) may start it
for b in /usr/bin/xfce4-terminal /usr/bin/xterm /usr/bin/uxterm; do
  [ -e "$b" ] && dpkg-statoverride --update --add root sudo 0750 "$b"
done
# Only parents (sudo group) may change the panel layout; kids get no panel editing
mkdir -p /etc/xdg/xfce4/kiosk
cat > /etc/xdg/xfce4/kiosk/kioskrc <<'EOF'
[xfce4-panel]
CustomizePanel=%sudo
EOF
# The web filter (Firefox policy) is generated from /etc/kidsos/web-allow.list
chmod +x /usr/local/sbin/kidsos-web-apply
/usr/local/sbin/kidsos-web-apply
# Child-safe Firefox: the default profile skeleton gets nothing from us, everything is in policies + pref files
# --- Services ---
# First-boot wizard: runs on the installed machine, not on the install stick (see fleet-setup.service)
touch /etc/fleet-needs-setup
# ssh is installed but NOT enabled: no remote access until the owner turns it on
# (sudo systemctl enable --now ssh).
for s in lightdm NetworkManager fleet-firstboot.service fleet-mark-good.service fleet-installer.service fleet-setup.service fleet-installer-shell.service fleet-usb-boot.service fleet-audio-init.service zramswap; do
  systemctl enable "$s" || echo "WARN: could not enable $s"
done
# sudoers drop-ins must be mode 0440 and valid, or sudo ignores them
chmod 0440 /etc/sudoers.d/fleet-brightness
visudo -cf /etc/sudoers.d/fleet-brightness
# Debian enables ssh automatically when openssh-server is installed; turn it off explicitly.
systemctl disable ssh.service ssh.socket 2>/dev/null || true
# Speed: units that only cost boot time or idle CPU/RAM on these machines. All still start on demand where
# something needs them (e2scrub is for LVM, we use plain ext4).
systemctl disable e2scrub_reap.service e2scrub_all.timer man-db.timer \
  NetworkManager-wait-online.service 2>/dev/null || true
systemctl set-default graphical.target
# SSH host keys and machine-id must be unique per machine -> created at first boot
rm -f /etc/ssh/ssh_host_*
: > /etc/machine-id
rm -f /var/lib/dbus/machine-id

# --- Cleanup ---
apt-get -y autoremove --purge || true
apt-get clean
rm -rf /var/lib/apt/lists/* /var/cache/apt/* /var/log/* /tmp/* /root/.cache
find /usr/share/doc -type f ! -name copyright -delete 2>/dev/null || true
find /usr/share/man /usr/share/info -type f -delete 2>/dev/null || true
