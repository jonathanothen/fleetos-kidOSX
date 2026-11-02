# KidsOS for Samsung Chromebook XE303C12 (snow) and XE503C12 (peach-pit)

A light, stable Debian 13 (armhf) with XFCE for children aged 4-8, built for old Exynos Chromebooks. It is a fork
of FleetOS: same kernel, same USB installer, same build chain, but a different desktop and different programs.
Internal script and service names still start with `fleet-` (installer, first-boot, audio, themes); only what the
user sees says KidsOS.

- **Start screen, one app:** children get no panel. A full-screen start screen shows big coloured tiles on a plain
  background (phone style), with the clock, volume buttons, battery, a power button (shut down / log out / switch user)
  and a sticker counter; every tile shows its level ("Nivå N"). Our own games run full screen with a small Hem button
  in the corner. Parents (members of the `sudo` group) keep a normal panel with windows, Wi-Fi, volume and a program menu.
  Large text (Comic Neue), large buttons.
- **Two colour themes:** `sol` (yellow/orange, default) and `hav` (blue). Switch with **Färger** in the start menu
  or `fleet-theme set <sol|hav>`.
- **Programs:** our own games **Mattelek**, **Skrivlabbet**, **Para ihop**, **Minne**, **Klockan**, **Lyssna och peka**
  and **Mönster** (all Swedish, with voice), Snap! (block programming, offline), Thonny (Python, for the older kids),
  Parole (music and video), Thunar (files), Firefox limited to a list of child-safe sites.
- **Kernel, installer, no built-in account:** unchanged from FleetOS (see the sections below).

## Two accounts: parent and child

The first-boot wizard (language, keyboard, **parent** name/password/computer name, **child's** name, Wi-Fi) creates

| Account | Rights | Login |
|---|---|---|
| Parent | administrator (`sudo`), full start menu, terminal, Synaptic | password |
| Child | no `sudo`, no terminal, short start menu with the child's programs only | no password, signs in by itself at boot (autologin) |

The child cannot install programs (no admin password), cannot start a terminal (`xfce4-terminal` is limited to the
`sudo` group), cannot change the panel (kiosk setting) and can only open sites on the allow list. To use the parent
account the child (or you) logs out from the shut-down menu in the panel; the login screen then lists both users.
There is no built-in account, so a machine can be reinstalled and handed on.

**Parent tasks** (log in as the parent): install programs with Synaptic or `sudo apt install ...`; Debian security
updates install themselves (unattended-upgrades).

### Web filter

Firefox only opens the pages in `/etc/kidsos/web-allow.list` (default: SVT, UR, Sveriges Radio) plus the local start
page and the local Snap! app. Everything else shows Firefox's blocked page. Developer tools, `about:config`,
add-ons, private windows and saving passwords are switched off by policy; uBlock Origin is installed by policy.
To allow another site, as the parent:

```
sudo nano /etc/kidsos/web-allow.list      # one pattern per line, e.g.  *://*.example.se/*
sudo kidsos-web-apply
```

`kidsos-web-apply` regenerates `/usr/lib/firefox-esr/distribution/policies.json` (it is also run at build time).
Limits: the filter blocks page and frame loads; the child can still use anything in Thonny (Python can run
programs, but never as root). It is a guard for small children, not a hardened kiosk.

## 1. Build (no Linux needed: GitHub Actions)

1. Create a **new** private GitHub repo and add this folder (GitHub Desktop is the easiest way on Windows; the
   hidden folders `.github` and `rootfs/overlay/etc/skel` must be included).
2. No secrets or passwords are needed.
3. Actions -> "Build KidsOS USB image" -> Run workflow (`usb_model` = `auto`).
   The kernel is cached between runs; a change to `kernel/` rebuilds it (about 30-40 minutes).
4. Download the artifact `kidsos-usb-auto` (a zip containing a `.img.xz`).

The build refuses to produce an image if the root filesystem fails `e2fsck`, if the kernel config lacks critical
options, if the Wi-Fi driver patch does not apply, if WhiteSur or Snap! could not be fetched, if there are not
exactly two KidsOS themes, or if one of the launcher programs is missing at its expected path.

Build-time downloads (from GitHub): the WhiteSur GTK theme (window frames and CSS base) and Snap!
(`jmoenig/Snap`, the revision is saved in `/usr/share/kidsos/snap.rev`). The first needs `sassc`, installed by
`build.sh deps`.

Local build alternative (Debian/Ubuntu or WSL2): `sudo ./build.sh deps && sudo ./build.sh all`

## 2. Write the stick (Windows)

Unpack the zip, then the `.img.xz` (7-Zip), and write the `.img` with balenaEtcher (click Continue at the
"Missing partition table" warning; ChromeOS uses GPT without a regular MBR) or Rufus in DD Image mode.
Use a plain, preferably old, USB 2.0 stick (8 GB or larger).

## 3. Prepare each Chromebook once (developer mode)

See [PREPARE-AND-TROUBLESHOOT.md](PREPARE-AND-TROUBLESHOOT.md). Then insert the stick before powering on and
press Ctrl+U at the "OS verification is OFF" screen.

## 4. Install

The stick boots straight into the installer: 15 s countdown (press any key to abort), then it repartitions the
eMMC, writes the kernel (slot A plus a fallback slot B), copies the system and powers off. **Remove the stick only
after the screen has gone dark.** Then power on and press Ctrl+D (or wait 30 s) on the dev-mode screen.

## Programs and what they need

| Icon | Program | Notes |
|---|---|---|
| Koda | Snap! | Block programming like Scratch (Swedish UI), offline in Firefox: `file:///usr/share/kidsos/snap/snap.html#lang:sv`. Scratch 3 has no armhf package and needs a node build; Snap! is plain HTML/JS and lighter. Projects are saved in the browser or exported as files. |
| Webben | Firefox ESR | Start page with three big buttons, allow-list filter. |
| Musik och film | Parole | Local files (GStreamer with libav). No YouTube player in this variant. |
| Mina filer | Thunar | |
| Räkna | Mattelek (own, pygame) | Full screen, voice (Swedish), levels 0-2: counting, number line/ten frames, plus and minus to 20. `kids-math --window` to test in a window. Hold Esc for 3 s to leave. |
| Para ihop | Para ihop (own, pygame) | Match a word to its picture: tap a word to hear it, drag it onto the picture. `kids-match --window`. |
| Rita | Rita (own, pygame) | Drawing: 12 colours, 3 brush sizes, eraser, paint bucket, stamps from our pictures, undo, new picture, save to `~/Bilder/Rita` (the last picture is restored automatically). |
| Minne | Minne (own, pygame) | Memory with picture and word cards; every card is read aloud. 6 to 16 cards as the child plays more rounds. |
| Klockan | Klockan (own, pygame) | Read an analog clock: whole hours, half hours, quarters, five-minute steps. Needs no new voice clips; a spoken "Vad är klockan?" is still to be ordered. |
| Lyssna och peka | Lyssna och peka (own, pygame) | Hear a word, tap the right picture (2 to 4 pictures). |
| Mönster | Mönster (own, pygame) | Which shape or colour comes next (AB, AAB, ABC, ABAC). |
| Skriva | Skrivlabbet (own, pygame) | Letters, the child's own name (from the account), words with pictures. `kids-write --window`. |
| (menu) Python | Thonny | For children who can read. |
| (menu) Färger | `fleet-theme gui` | |

Start-menu entries are `rootfs/overlay/usr/share/applications/kids-*.desktop`; the child's menu is
`/usr/share/kidsos/kid.menu` (a menu that lists only those files). The six desktop icons are copied from
`/etc/skel/Desktop` to each new user (they must be executable; `customize.sh` sets that).

## Hardware notes, performance, diagnostics

Unchanged from FleetOS and still valid:

- **Backlight:** only 8 steps (0-7); the brightness keys run `fleet-brightness up|down` and never go to black.
- **Audio:** `fleet-audio-init` runs at every boot and locks the speaker amplifier at +5 dB; PipeWire keeps the
  volume in software, so the volume keys (0-100 %) are the only thing that changes loudness. This matters more for
  children's ears: the maximum is deliberately limited.
- **Wi-Fi (Marvell 88W8797):** `firmware-libertas` plus a small driver patch in `kernel/build-kernel.sh`.
- **USB boot flag:** `sudo fleet-usb-boot on|off|status`.
- **Speed:** apt timers run 20-30 min after boot, `e2scrub`, `man-db` and `NetworkManager-wait-online` are not
  started at boot, the journal lives in RAM, zram swap, `noatime`; Firefox has two content processes, an in-RAM cache
  and no animations (`/usr/lib/firefox-esr/defaults/pref/fleet.js`). Removed compared with FleetOS: Plank dock,
  Whisker menu, app store, mpv/yt-dlp, Bluetooth stack, Atril, Xarchiver, the five old themes.
- **Diagnostics:** `sudo fleet-diag` writes `/tmp/fleet-diag.txt`.

## First boot (setup wizard)

Before the login screen a graphical wizard asks for language, keyboard layouts (up to three, Alt+Shift), the parent
account (username and computer name are suggested from the name and corrected automatically), whether to allow
booting from USB, the child's name, and Wi-Fi. If the graphical wizard fails, a text-mode wizard takes over. SSH is
installed but disabled (`sudo systemctl enable --now ssh`).

## What is verified and what is not

Verified on an XE303C12 running the previous FleetOS image (the desktop pieces were tried in a live session and then
removed again):

- The panel layout (bottom, 56 px), the Start button with the custom child menu, desktop launcher icons (executable
  `.desktop` files show as big icons and open on one click), both KidsOS GTK themes, the wallpaper, the readable
  icon labels, window frames and Thunar in the theme, the panel colour, and that the theme generator output is
  complete (it caught a missing newline in a palette file).
- All shell scripts pass `bash -n`; the generated Firefox policy file is valid JSON.
- Paths of the launched programs against the Debian trixie package file lists
  (`/usr/bin/thonny`,
  `/usr/bin/parole`).

**Not verified (needs a build and a real install):**

- The whole build (new package list, `host-apps.sh` fetching Snap!, `dpkg-statoverride` for the terminal, the
  `nopasswdlogin` PAM line, `customize.sh` checks).
- The two-account wizard, autologin of the child, and logging out to the parent (login screen, parent's full menu
  after `fleet-look` restarts the panel).
- Our own games on the real hardware with real touchpad input, Snap! speed in Firefox, Thonny and
  Parole playback on this hardware; nothing was installed on the test Chromebook.
- That the Firefox website filter also stops sub-resources; SVT and UR may load video from other domains, in which case add
  those domains to `web-allow.list`. The default start-page sites and their video hosts were not tested.
- Comic Neue / Adwaita icons in the panel and tray (the test machine used other fonts and icons).
- The XE503C12 (peach-pit) and `usb_model=auto` on both models.

## Project layout

```
build.sh, config.env              build driver and settings
kernel/                           kernel config fragment and cross-build script (with the Wi-Fi patch)
rootfs/packages.txt               Debian packages
rootfs/host-themes.sh             installs the WhiteSur GTK/window-frame base on the build host
rootfs/host-apps.sh               fetches Snap! on the build host
rootfs/customize.sh               runs in the armhf chroot (themes, child-safe settings, services, cleanup)
rootfs/overlay/                   files copied into the image (scripts, units, themes, icons, launchers, skel)
.github/workflows/build.yml       GitHub Actions build
```
