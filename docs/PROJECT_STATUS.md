# Velaris project status

Updated on August 15, 2026.

## Summary

Velaris is an Arch Linux distribution for x86-64 with KDE Plasma 6, selectable CachyOS or Arch kernels, SDDM, PipeWire, and Calamares. Its technical goal is to balance responsive performance, stability across varied hardware, and a clean installed system with no live-session residue.

## State of this revision

| Area | Change | Expected result |
|---|---|---|
| Calamares | Dedicated Velaris instances and configuration files | Package upgrades cannot silently replace project configuration |
| Installer UI | Horizontal welcome artwork, consistent styling, larger window, and scrollable language popup | Clearer layout without the oversized square logo |
| Kernel selection | CPU-gated BORE+LTO, regular CachyOS, CachyOS LTS, and Arch choices | High performance where supported without breaking older CPUs |
| Graphics | Early NVIDIA generation policy plus PCI-based AMD/Intel/NVIDIA and VM detection | The live session and installer avoid a blind graphics default |
| NVIDIA | Kernel-matched NVIDIA Open modules for each kernel | Offline installation without a mismatched module |
| Power | Balanced, performance, and power-saver profiles | Predictable trade-off instead of unsafe generic tuning scripts |
| Partitioning | Real 24 GiB requirement, nested layout, manual mode, and alongside support | Calamares can offer resize/dual-boot when the disk is eligible |
| Live display | Plasma X11 live fallback plus `xrandr --auto` | Preferred display mode is selected before Calamares opens |
| Support links | User-session URL bridge, bug form, and permanent Known Issues issue | Both welcome-page links work before the development PR is merged |
| Installed system | `unpackfs` exclusions, `removeuser`, and mandatory cleanup | No live user, autologin, passwordless sudo, installer helper, or Polkit exception remains |
| Plasma services | Baloo indexer and unused XEmbed/global-menu bridges masked globally | Lower background activity while keeping essential Plasma services intact |
| Printing | CUPS socket activation | The daemon starts only when printing is requested |
| Bluetooth | No unconditional service enable | D-Bus or hardware use may start Bluetooth when needed |
| Storage | Btrfs `noatime`, Zstd level 1, `fstrim.timer`, and `paccache.timer` | Lower metadata writes and scheduled SSD/cache maintenance |
| Memory | ZRAM, `swappiness=100`, `page-cluster=0`, `earlyoom`, and absolute writeback limits | Better response under pressure without aggressive overcommit |
| Internationalization | English live session with Calamares locale selection | Predictable global default while preserving the user's installed locale |
| CI | Self-hosted `lenovo-server` runner inside an Arch container | Reproducible ISO validation and build on the project machine |

## Automated validation

`scripts/validate-profile.py` checks:

- Calamares YAML, instances, selection flow, and execution ordering;
- branding assets, welcome dimensions, support URLs, and slideshow lifecycle;
- kernel, NVIDIA, Mesa, VM, and detection packages;
- CPU compatibility gating for x86-64-v3;
- live-only file exclusions, early GPU policy, wrapper paths, Polkit scope, and English default;
- dual-boot prerequisites, Btrfs options, GRUB OS probing, and storage requirements;
- shell syntax, executable helper modes, repository signatures, and package duplicates;
- ZRAM, OOM policy, Fish, CUPS activation, service masks, and first-boot behavior.

GitHub Actions runs validation before `mkarchiso`, confirms the runner is exactly `lenovo-server`, and cleans large temporary build directories even after a failure.

## Proof still required

Static validation cannot prove real installation behavior. Before a stable release, complete the matrix in `docs/TESTING.md`, including:

1. empty-disk UEFI installation;
2. Windows alongside/resize installation on disposable test hardware;
3. each kernel choice on a compatible CPU;
4. AMD, Intel, modern NVIDIA, legacy NVIDIA, and major VM graphics paths;
5. two clean boots with `systemctl --failed` empty.

Until those tests pass, the correct status remains **implemented and statically validated, awaiting hardware installation proof**.
