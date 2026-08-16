# Velaris known issues

This page tracks limitations that are known before the first stable Velaris release. Check the latest ISO and existing [GitHub issues](https://github.com/Caeluum/velaris/issues) before reporting a problem.

## Secure Boot

Secure Boot is not supported by the current Beta images because the Velaris boot chain and kernels are not yet signed with a project key. Disable Secure Boot in firmware before starting the ISO. Do not disable TPM or disk encryption unless your device documentation specifically requires it.

## NVIDIA graphics

- NVIDIA Open is offered automatically for Turing-generation and newer GPUs.
- Older NVIDIA hardware uses Nouveau by default. Velaris does not install unsupported legacy proprietary branches automatically.
- If the normal live entry produces a black screen, use **Boot Velaris (nomodeset — graphics compatibility)**. This mode intentionally uses a basic resolution; install the appropriate driver and reboot before judging display performance.

## Virtual machines

- The installer detects VMware, VirtualBox, and QEMU/KVM and keeps the matching guest tools.
- Plasma X11 is the safest fallback if a VMware guest shows compositor freezes under Wayland.
- Dynamic resizing depends on the virtual GPU and guest integration offered by the hypervisor.

## Dual boot and existing Windows installations

- Back up important files before resizing any partition.
- Disable Windows Fast Startup and fully shut Windows down. A hibernated or dirty NTFS volume cannot be resized safely.
- Suspend BitLocker before changing Windows partitions and keep the recovery key available.
- **Install alongside** appears only when Calamares finds a supported, safely resizable partition with enough free space. Use manual partitioning only if you understand the existing layout.
- Velaris uses GRUB and enables OS probing. Some firmware may still place Windows Boot Manager first after a firmware update.

## Wi-Fi firmware

The ISO includes the standard Arch Linux firmware bundle. A small number of adapters require firmware that cannot be redistributed or a newer upstream kernel. Use Ethernet or USB tethering for installation and include the adapter's PCI or USB ID in a bug report.

## Language and keyboard

The live session and installer start in English. The language, keyboard layout, timezone, and locale selected in Calamares are applied to the installed system.

## Reporting a problem

Use the [Velaris support form](https://github.com/Caeluum/velaris/issues/new/choose) and include:

```text
ISO/build number:
Installation mode: UEFI or BIOS
Kernel choice:
Graphics choice:
GPU and CPU:
Partitioning choice:
Exact failure:
```

Attach the output of `fastfetch`, `systemctl --failed --no-pager`, and relevant logs after removing private information. Never publish passwords, tokens, serial numbers, recovery keys, or personal files.
