# Preparing the Chromebook and troubleshooting USB boot

Applies to the Samsung Chromebook XE303C12 (snow) and XE503C12 (peach-pit).

## 1. Put the Chromebook in developer mode (once per machine)

Developer mode is required to boot anything other than ChromeOS. **It wipes the ChromeOS user data.**

1. Power the Chromebook off.
2. Hold **Esc + Refresh** (the circular-arrow key, F3 position) and press the **Power** button.
   Release when the "Chrome OS is missing or damaged" recovery screen appears.
3. Press **Ctrl+D**. On newer firmware the screen says "To turn OS verification OFF, press ENTER";
   press **Enter** and confirm.
4. The machine reboots and shows "Preparing system for Developer Mode". This takes about 10-15 minutes
   and ends with ChromeOS first-time setup.
5. From now on every boot shows the **"OS verification is OFF"** screen.
   Press **Ctrl+D** (or wait ~30 s) to boot the internal disk, or **Ctrl+U** to boot from USB.
   You can ignore the beeps.

## 2. Enable USB boot (once per machine)

You do not need to finish the ChromeOS setup or sign in with a Google account.

1. At the "OS verification is OFF" screen press **Ctrl+D** to boot ChromeOS.
2. On the sign-in screen choose **Browse as Guest**.
3. Press **Ctrl+Alt+T** to open the terminal ("crosh").
4. Type `shell` and press Enter. You are now the user `chronos` with a bash shell.
   (Alternative: press Ctrl+Alt+F2, i.e. the "->" key in the top row, and log in as `chronos`.)
5. Run:

   ```
   sudo enable_dev_usb_boot
   ```

   Answer `y` if it asks. This is the supported way on these machines;
   `crossystem dev_boot_usb=1` alone does not always persist.
6. Verify with `sudo crossystem dev_boot_usb`. It must print `1`.
7. Reboot, **insert the stick before powering on**, wait a few seconds at the
   "OS verification is OFF" screen, then press **Ctrl+U**.

`sudo crossystem dev_boot_signed_only=0` should already be set (it prints `0`).

## 3. USB stick, SD card or adapter?

Use a **plain USB stick**, ideally an old small USB 2.0 one (8 GB or larger).

- SD cards in USB card readers / adapters often fail to boot even though ChromeOS sees them as a normal
  disk (`/dev/sda`). The firmware has a much simpler USB driver than the OS: many card readers answer too
  slowly or present several devices, and the firmware gives up.
- Some fast USB 3 sticks have the same problem.
- Try the **USB 2.0 port** (black) first, then the blue USB 3.0 port.
- Insert the stick **before** power-on and wait a few seconds before pressing Ctrl+U.
- The same behaviour was seen with Kali Linux on these machines, so a failing boot is not necessarily
  a problem with the image. Try a different stick before changing the build.
- What worked in practice: an **old no-brand 8 GB USB stick**. Large or newer sticks (e.g. 32 GB) and
  SD-card readers did not boot. The image is only ~2.1 GB, so a small stick is enough
  (it must not be smaller than the image; the internal eMMC of these machines is ~16 GB, which is plenty).

## 3b. Turn USB boot on again from KidsOS / FleetOS itself (no ChromeOS needed)

The installer wipes the internal disk, so ChromeOS is gone and `sudo enable_dev_usb_boot` is no longer available. If the
flag is off (Ctrl+U gives a short beep, or the screen complains about the flag), set it from the installed system:

```
sudo fleet-usb-boot status      # shows dev_boot_usb=0 or 1
sudo fleet-usb-boot on          # turns it on (the parent account has sudo)
```

On the Samsung **XE503C12 (Peach Pit)** the firmware keeps the flag in the EC, and Debian's `crossystem` cannot reach it
(`crossystem` prints `(error)` for every `dev_boot_*` value and "Failed to set parameter"). `fleet-usb-boot` then falls
back to `fleet-ec-nvram`, which talks to the EC over `/dev/cros_ec`:

```
sudo fleet-ec-nvram                # shows the 16-byte flag block, its checksum and dev_boot_usb / dev_boot_signed_only
sudo fleet-ec-nvram --set-usb      # asks first; turns USB boot on and allows kernels not signed by Google
sudo fleet-ec-nvram --clear-usb    # turns it off
```

It refuses to write unless the checksum of the block matches, and reads the block back to check that the change stuck.
Verified on an XE503C12 (flag was off, `--set-usb`, then a stick booted with Ctrl+U). Restart afterwards and press
**Ctrl+U** on the "OS verification is OFF" screen. With `echo yes | sudo tee /etc/fleet-usb-boot` the flag is also
restored at every boot if the firmware loses it (`fleet-usb-boot.service`).

## 4. What the beeps mean (Ctrl+U)

| Sound | Meaning |
|---|---|
| Short beep, nothing happens | USB boot is disabled. Run `sudo enable_dev_usb_boot` (section 2) or, on an installed machine, `sudo fleet-usb-boot on` (section 3b). |
| Screen flashes once, then a deep beep | USB boot is on, but the firmware finds no bootable kernel on the stick. Change stick and port. |

## 5. Verify the kernel partition on the stick (from ChromeOS)

Insert the stick into a machine running ChromeOS, open the shell as above, and run one line at a time:

```
cd /tmp
sudo dd if=/dev/sda of=k.bin bs=512 skip=8192 count=131072
vbutil_kernel --verify k.bin
```

- Write `if=/dev/sda` **without** a trailing slash (otherwise: "Not a directory").
- Files in `/tmp` disappear on reboot.
- Expected: `Body verification succeeded` and a command line containing `root=PARTUUID=...`.
- "Secondary GPT header is invalid" from `cgpt show /dev/sda` is harmless: the backup partition table sits
  at the end of the image, not at the end of a larger stick.

## 6. Writing the image on Windows

- Unzip the artifact from GitHub, then unpack the `.img.xz` with 7-Zip. The result is a ~2.1 GB `.img`.
- balenaEtcher: select the `.img` and click **Continue** at the "Missing partition table" warning
  (ChromeOS uses a GPT without a regular MBR, so the warning is expected).
  If Etcher fails with `requestMetadata is not a function`, unpack the `.xz` first and select the `.img`.
- Alternative: Rufus in **DD Image mode**.
