# Velaris ISO test checklist

Use a virtual machine with an empty virtual disk for routine tests. Use only disposable hardware or a complete verified backup for alongside/resize tests.

## 1. Prepare the VM

Recommended baseline:

- UEFI firmware;
- 2 vCPUs;
- 4 GiB RAM;
- a 40 GiB or larger virtual disk;
- networking enabled;
- the hypervisor's default accelerated virtual GPU.

Run an additional 2 GiB test for ZRAM and memory-pressure behavior. Test VMware, VirtualBox, and QEMU/KVM separately when possible.

## 2. Check the live session

1. Confirm automatic login as `velaris`.
2. Confirm the desktop uses the display's preferred resolution.
3. Open Calamares from both the desktop launcher and autostart.
4. Confirm the installer starts in English, fits the screen, and shows the horizontal welcome artwork.
5. Open the language selector, scroll through the list, and choose a non-English locale once.
6. Confirm **Velaris support** opens the issue form and **Known issues** opens `KNOWN_ISSUES.md` in Firefox.
7. Test networking, audio, screen lock, and browser rendering.

On NVIDIA hardware, also inspect `/run/velaris/live-graphics` and `lsmod`. Turing or newer hardware should use NVIDIA Open; older hardware should use Nouveau. The initramfs policy must not exist in the installed system after Calamares finishes.

`printenv LIBGL_ALWAYS_SOFTWARE` must return no value.

## 3. Check automatic recommendations

On every machine, record `/run/velaris/hardware-detection` and compare it with the selected graphics option.

| Hardware | Expected graphics default |
|---|---|
| NVIDIA Turing or newer | NVIDIA Open |
| NVIDIA older than Turing | Nouveau |
| AMD GPU without NVIDIA | AMD Mesa + AMDGPU |
| Intel GPU without AMD/NVIDIA | Intel Mesa + ANV |
| VM with no identified physical GPU | Virtual machine |
| Unknown hardware | Universal open-source fallback |

The BORE+LTO kernel must appear and be selected only when the loader reports `x86-64-v3 (supported)`. Otherwise, regular CachyOS must be the first and default choice.

## 4. Installation matrix

At minimum, test:

1. regular CachyOS + detected graphics + Balanced on an empty Btrfs disk;
2. CachyOS LTS + Universal + Power saver on Ext4;
3. Arch kernel + detected graphics on an empty disk;
4. BORE+LTO + Performance on confirmed x86-64-v3 hardware;
5. manual partitioning with a separate home partition;
6. LUKS encryption in a separate run;
7. alongside/resize on a disposable Windows installation after disabling Fast Startup and suspending BitLocker.

Never proceed if the partition summary does not exactly match the intended target disk and resize boundary.

## 5. Validate the installed system

### Live identity removed

```bash
getent passwd velaris
test ! -e /home/velaris
test ! -e /etc/sddm.conf.d/autologin.conf
test ! -e /usr/bin/velaris-calamares
test ! -e /usr/lib/velaris-live
test ! -e /usr/lib/udev/rules.d/00-velaris-gpu-policy.rules
test ! -e /etc/polkit-1/rules.d/49-calamares.rules
```

All commands must produce no output and return the expected success state.

### Kernel and graphics choice

```bash
cat /etc/velaris/kernel-choice
cat /etc/velaris/graphics-choice
uname -r
pacman -Q | grep -E '^(linux|nvidia)'
```

Only the selected kernel should remain. Kernel headers are intentionally installed on demand rather than carried by every desktop. NVIDIA Open installations must contain exactly one matching NVIDIA kernel-module package; non-NVIDIA installations must not retain NVIDIA userspace packages.

### Services and boot

```bash
systemctl --failed --no-pager
systemctl is-enabled NetworkManager.service sddm.service ananicy-cpp.service ufw.service
systemctl is-enabled cups.socket fstrim.timer paccache.timer velaris-performance-profile.service
systemctl is-enabled NetworkManager-wait-online.service cups.service bluetooth.service systemd-oomd.service
plymouth-set-default-theme
```

Expected results:

- no failed units;
- core services and timers enabled;
- NetworkManager wait-online, CUPS daemon, and Bluetooth not unconditionally enabled;
- `systemd-oomd` masked;
- Plymouth theme set to `velaris` after the first-boot service completes.

Reboot a second time to verify the rebuilt initramfs.

### Memory, storage, and power profile

```bash
swapon --show
sysctl vm.swappiness vm.page-cluster vm.dirty_bytes vm.dirty_background_bytes
cat /sys/module/zswap/parameters/enabled
findmnt -no OPTIONS /
powerprofilesctl get
```

Confirm ZRAM, `swappiness = 100`, `page-cluster = 0`, zswap `N`, and `noatime,compress=zstd:1` on Btrfs. The active power profile must match the installer choice when the platform supports it.

### Locale and Plasma sessions

```bash
locale
localectl status
getent passwd "$USER" | cut -d: -f7
```

The installed locale, keyboard, and timezone must match Calamares, while Fish remains the default shell. Test both Plasma Wayland and Plasma X11 and confirm hardware acceleration is not globally disabled.

## 6. Failure report data

Attach sanitized output from:

```bash
fastfetch
systemctl --failed --no-pager
journalctl -b -p warning..alert --no-pager
cat /etc/velaris/kernel-choice /etc/velaris/graphics-choice /etc/velaris/performance-profile
```

For installer failures, copy `/root/.cache/calamares/session.log` before rebooting. Remove passwords, tokens, serial numbers, recovery keys, usernames, and personal paths before publishing logs.
