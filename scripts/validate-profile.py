#!/usr/bin/env python3
"""Static validation for the Velaris Archiso and Calamares profile."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[ERRO] PyYAML ausente. Instale com: pacman -S python-yaml", file=sys.stderr)
    raise SystemExit(2)


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profile"
CALAMARES = PROFILE / "airootfs/etc/calamares"
MODULES = CALAMARES / "modules"
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        print(f"[OK] {message}")
    else:
        print(f"[ERRO] {message}")
        FAILURES.append(message)


def load_yaml(path: Path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        FAILURES.append(f"YAML inválido em {path.relative_to(ROOT)}: {error}")
        print(f"[ERRO] {FAILURES[-1]}")
        return None


def sequence_for(settings: dict, phase_name: str) -> list[str]:
    for phase in settings.get("sequence", []):
        if isinstance(phase, dict) and phase_name in phase:
            value = phase[phase_name]
            return value if isinstance(value, list) else []
    return []


def validate_yaml_and_instances() -> dict[Path, object]:
    paths = [CALAMARES / "settings.conf", CALAMARES / "branding/velaris/branding.desc"]
    paths.extend(sorted(MODULES.glob("*.conf")))
    documents = {path: load_yaml(path) for path in paths}
    check(all(document is not None for document in documents.values()), "arquivos YAML do Calamares carregam")

    settings_path = CALAMARES / "settings.conf"
    settings = documents.get(settings_path)
    if not isinstance(settings, dict):
        return documents

    instance_pairs: set[tuple[str, str]] = set()
    instance_configs: list[Path] = []
    duplicate_pairs: set[tuple[str, str]] = set()
    for instance in settings.get("instances", []):
        if not isinstance(instance, dict):
            continue
        pair = (str(instance.get("module", "")), str(instance.get("id", "")))
        if pair in instance_pairs:
            duplicate_pairs.add(pair)
        instance_pairs.add(pair)
        config = instance.get("config")
        if config:
            instance_configs.append(MODULES / str(config))

    check(not duplicate_pairs, "instâncias do Calamares não estão duplicadas")
    check(all(path.is_file() for path in instance_configs), "cada instância aponta para um arquivo existente")

    package_owned_names = {
        "bootloader.conf",
        "displaymanager.conf",
        "grubcfg.conf",
        "initcpiocfg.conf",
        "packages.conf",
        "partition.conf",
        "removeuser.conf",
        "services-systemd.conf",
        "unpackfs.conf",
        "users.conf",
    }
    collisions = sorted(path.name for path in MODULES.glob("*.conf") if path.name in package_owned_names)
    check(not collisions, "configs locais do Calamares não colidem com nomes fornecidos pelo pacote")

    referenced_pairs: set[tuple[str, str]] = set()
    for phase in settings.get("sequence", []):
        if not isinstance(phase, dict):
            continue
        for modules in phase.values():
            if not isinstance(modules, list):
                continue
            for module_ref in modules:
                if isinstance(module_ref, str) and "@" in module_ref:
                    module, instance_id = module_ref.split("@", 1)
                    referenced_pairs.add((module, instance_id))

    check(referenced_pairs <= instance_pairs, "referências module@id possuem instâncias declaradas")

    required_pairs = {
        ("welcome", "velaris"),
        ("packagechooser", "kernel"),
        ("packagechooser", "graphics"),
        ("packagechooser", "profile"),
        ("partition", "velaris"),
        ("mount", "velaris"),
        ("unpackfs", "velaris"),
        ("users", "velaris"),
        ("displaymanager", "velaris"),
        ("grubcfg", "velaris"),
        ("bootloader", "velaris"),
        ("initcpiocfg", "velaris"),
        ("services-systemd", "velaris"),
        ("removeuser", "velaris"),
        ("packages", "cleanup"),
        ("shellprocess", "firstboot"),
        ("shellprocess", "keyring"),
        ("velarisselections", "selections"),
        ("shellprocess", "applyselections"),
    }
    check(required_pairs <= instance_pairs, "instâncias críticas da instalação estão declaradas")

    exec_sequence = sequence_for(settings, "exec")
    show_sequence = sequence_for(settings, "show")
    chooser_order = [
        "welcome@velaris",
        "locale",
        "keyboard",
        "packagechooser@kernel",
        "packagechooser@graphics",
        "packagechooser@profile",
        "partition@velaris",
    ]
    check(
        all(item in show_sequence for item in chooser_order)
        and [show_sequence.index(item) for item in chooser_order]
        == sorted(show_sequence.index(item) for item in chooser_order),
        "installer presents locale, hardware choices, and partitioning in a safe order",
    )
    check(
        "mount@velaris" in exec_sequence and "mount" not in exec_sequence,
        "instalação usa opções de montagem próprias da Velaris",
    )
    ordered = (
        "removeuser@velaris" in exec_sequence
        and "users@velaris" in exec_sequence
        and exec_sequence.index("removeuser@velaris") < exec_sequence.index("users@velaris")
    )
    check(ordered, "conta live é removida antes da criação do usuário final")
    selection_order = [
        "unpackfs@velaris",
        "velarisselections@selections",
        "shellprocess@applyselections",
        "initcpiocfg@velaris",
        "initcpio",
    ]
    check(
        all(item in exec_sequence for item in selection_order)
        and [exec_sequence.index(item) for item in selection_order]
        == sorted(exec_sequence.index(item) for item in selection_order),
        "hardware selections are applied after unpacking and before initramfs generation",
    )
    check(settings.get("dont-chroot") is False, "instalação usa o sistema de destino via chroot")
    check(settings.get("disable-cancel-during-exec") is True, "cancelamento fica bloqueado durante a gravação")
    return documents


def validate_branding(documents: dict[Path, object]) -> None:
    branding = documents.get(CALAMARES / "branding/velaris/branding.desc")
    branding_dir = CALAMARES / "branding/velaris"
    if not isinstance(branding, dict):
        check(False, "branding do Calamares está estruturado")
        return

    referenced_files: list[Path] = []
    images = branding.get("images", {})
    if isinstance(images, dict):
        referenced_files.extend(branding_dir / str(value) for value in images.values())
    slideshow = branding.get("slideshow")
    if isinstance(slideshow, str):
        referenced_files.append(branding_dir / slideshow)
    check(bool(referenced_files) and all(path.is_file() for path in referenced_files), "imagens e slideshow do branding existem")

    slideshow_path = branding_dir / str(slideshow)
    slideshow_text = slideshow_path.read_text(encoding="utf-8") if slideshow_path.is_file() else ""
    api2_ready = branding.get("slideshowAPI") != 2 or (
        "function onActivate()" in slideshow_text and "function onLeave()" in slideshow_text
    )
    check(api2_ready, "slideshow implementa o ciclo de vida da API 2")
    wallpaper = PROFILE / "airootfs/usr/share/wallpapers/velaris/contents/images/velaris_desktop.png"
    check(wallpaper.is_file() and str(wallpaper).replace(str(PROFILE / "airootfs"), "") in slideshow_text, "slideshow referencia um wallpaper existente")

    strings = branding.get("strings", {})
    images = branding.get("images", {})
    check(
        isinstance(strings, dict)
        and strings.get("supportUrl") == "https://github.com/Caeluum/velaris/issues/new/choose"
        and strings.get("knownIssuesUrl") == "https://github.com/Caeluum/velaris/issues/2",
        "support and known-issues buttons point to their dedicated GitHub pages",
    )
    check(
        isinstance(images, dict)
        and images.get("productWelcome") == "welcome.svg"
        and branding.get("windowSize") == "1000px,680px",
        "welcome page uses horizontal artwork in a predictable window size",
    )
    qss = PROFILE / "airootfs/usr/share/velaris/calamares/calamares.qss"
    qss_text = qss.read_text(encoding="utf-8") if qss.is_file() else ""
    check(
        "QComboBox#languageWidget QAbstractItemView" in qss_text
        and "min-height: 380px" in qss_text,
        "language chooser receives a large scrollable popup",
    )


def validate_installer_choices(documents: dict[Path, object]) -> None:
    expected_items = {
        "packagechooser_kernel.conf": {"cachyos", "lts", "arch"},
        "packagechooser_graphics.conf": {"nvidia-open", "nouveau", "amd", "intel", "virtual", "universal"},
        "packagechooser_profile.conf": {"balanced", "performance", "powersave"},
    }
    for filename, expected in expected_items.items():
        document = documents.get(MODULES / filename)
        items = document.get("items", []) if isinstance(document, dict) else []
        ids = {str(item.get("id")) for item in items if isinstance(item, dict)}
        check(
            isinstance(document, dict)
            and document.get("mode") == "required"
            and document.get("method") == "legacy"
            and expected <= ids,
            f"{filename} defines one required, locally processed choice",
        )

    v3_template = load_yaml(PROFILE / "airootfs/usr/share/velaris/calamares/kernel-v3.conf")
    v3_items = v3_template.get("items", []) if isinstance(v3_template, dict) else []
    v3_ids = {
        str(item.get("id"))
        for item in v3_items
        if isinstance(item, dict)
    }
    check(
        isinstance(v3_template, dict)
        and v3_template.get("default") == "bore-lto"
        and "bore-lto" in v3_ids,
        "BORE+LTO exists only in the CPU-gated x86-64-v3 chooser template",
    )

    selection_module = PROFILE / "airootfs/usr/lib/calamares/modules/velarisselections"
    module_desc = load_yaml(selection_module / "module.desc")
    module_script = selection_module / "main.py"
    module_text = module_script.read_text(encoding="utf-8") if module_script.is_file() else ""
    check(
        isinstance(module_desc, dict)
        and module_desc.get("type") == "job"
        and module_desc.get("interface") == "python"
        and module_desc.get("script") == "main.py"
        and module_desc.get("noconfig") is True
        and all(
            token in module_text
            for token in ("rootMountPoint", "packagechooser_{kind}", '"kernel"', '"graphics"', '"profile"')
        ),
        "local Calamares module records every installer choice",
    )
    try:
        compile(module_text, str(module_script), "exec")
        module_syntax_valid = bool(module_text)
    except SyntaxError:
        module_syntax_valid = False
    check(module_syntax_valid, "local Calamares selection module has valid Python syntax")

    partition = documents.get(MODULES / "partition_velaris.conf")
    welcome = documents.get(MODULES / "welcome_velaris.conf")
    requirements = welcome.get("requirements", {}) if isinstance(welcome, dict) else {}
    check(
        isinstance(partition, dict)
        and partition.get("allowManualPartitioning") is True
        and partition.get("drawNestedPartitions") is True
        and partition.get("initialPartitioningChoice") == "none"
        and isinstance(requirements, dict)
        and float(requirements.get("requiredStorage", 0)) >= 24,
        "manual and alongside partitioning have a real storage requirement",
    )


def validate_live_identity(documents: dict[Path, object]) -> None:
    unpack = documents.get(MODULES / "unpackfs_velaris.conf")
    removeuser = documents.get(MODULES / "removeuser_velaris.conf")
    users = documents.get(MODULES / "users_velaris.conf")

    excludes: set[str] = set()
    if isinstance(unpack, dict):
        for source in unpack.get("unpack", []):
            if isinstance(source, dict):
                excludes.update(str(item) for item in source.get("exclude", []))

    required_excludes = {
        "/home/velaris/",
        "/etc/skel/.config/autostart/calamares.desktop",
        "/etc/sddm.conf.d/autologin.conf",
        "/etc/sudoers.d/velaris",
        "/etc/polkit-1/rules.d/49-calamares.rules",
        "/etc/calamares/",
        "/usr/share/applications/calamares.desktop",
        "/etc/xdg/autostart/00-velaris-display-setup.desktop",
        "/usr/bin/velaris-calamares",
        "/usr/lib/velaris-live/",
        "/usr/lib/udev/rules.d/00-velaris-gpu-policy.rules",
    }
    check(required_excludes <= excludes, "unpackfs exclui identidade, autologin e privilégios do live")
    check(isinstance(removeuser, dict) and removeuser.get("username") == "velaris", "removeuser elimina a conta live")
    check(
        isinstance(users, dict)
        and users.get("doAutologin") is False
        and users.get("setRootPassword") is False,
        "usuário final não recebe autologin nem senha root reutilizada",
    )
    user_settings = users.get("user", {}) if isinstance(users, dict) else {}
    check(
        isinstance(user_settings, dict) and user_settings.get("shell") == "/usr/bin/fish",
        "Fish é o shell padrão do usuário instalado",
    )

    skel_autostart = PROFILE / "airootfs/etc/skel/.config/autostart/calamares.desktop"
    check(not skel_autostart.exists(), "Calamares não fica no autostart de novos usuários")

    customize = (PROFILE / "airootfs/root/customize_airootfs.sh").read_text(encoding="utf-8")
    check("passwd -l root" in customize and "passwd -d root" not in customize, "conta root do live permanece bloqueada")
    check("disable NetworkManager-wait-online.service" in customize, "sessão live não espera rede durante o boot")
    check("-s /usr/bin/fish" in customize, "usuário live também usa Fish")
    check(
        "disable cups.service" in customize and "enable cups.socket" in customize,
        "CUPS da sessão live usa ativação por socket",
    )
    check("mask systemd-oomd.service" in customize, "sessão live evita um segundo gerenciador de OOM")
    check(
        all(
            token in customize
            for token in (
                "systemctl --global mask kde-baloo.service",
                "systemctl --global mask plasma-xembedsniproxy.service",
                "systemctl --global mask plasma-gmenudbusmenuproxy.service",
            )
        ),
        "unused Plasma indexer and compatibility bridges are masked globally",
    )
    check(
        "LANG=en_US.UTF-8" in customize
        and "10-velaris-live-locale.conf" in customize
        and "rm -f /usr/lib/modprobe.d/nvidia-utils.conf" in customize,
        "live session stays English and allows Nouveau fallback before installation",
    )
    check(
        all(token in customize for token in ("pacman-key --init", "pacman-key --populate archlinux cachyos"))
        and not re.search(r"^\s*pacman\s+-Scc\b", customize, flags=re.MULTILINE),
        "live inicializa os chaveiros e preserva os bancos do pacman",
    )

    policy = (PROFILE / "airootfs/etc/polkit-1/rules.d/49-calamares.rules").read_text(encoding="utf-8")
    restricted_policy = all(
        token in policy
        for token in (
            'action.id === "org.freedesktop.policykit.exec"',
            'action.lookup("program") === "/usr/lib/velaris-live/calamares-root"',
            'subject.user === "velaris"',
            "subject.local",
            "subject.active",
        )
    )
    check(restricted_policy, "regra Polkit limita elevação ao Calamares da sessão live")

    desktop = (PROFILE / "airootfs/usr/share/applications/calamares.desktop").read_text(encoding="utf-8")
    check("Exec=/usr/bin/velaris-calamares" in desktop, "live shortcut uses the session-preserving installer wrapper")

    wrapper_paths = [
        PROFILE / "airootfs/usr/bin/velaris-calamares",
        PROFILE / "airootfs/usr/lib/velaris-live/calamares-root",
        PROFILE / "airootfs/usr/lib/velaris-live/bin/xdg-open",
        PROFILE / "airootfs/usr/lib/velaris-live/prepare-installer",
        PROFILE / "airootfs/usr/lib/velaris-live/display-setup",
        PROFILE / "airootfs/usr/lib/velaris-live/gpu-module-policy",
    ]
    check(
        all(path.is_file() and path.stat().st_mode & 0o111 for path in wrapper_paths),
        "live installer, URL bridge, hardware detector, and display helper are executable",
    )
    root_wrapper = wrapper_paths[1].read_text(encoding="utf-8")
    url_bridge = wrapper_paths[2].read_text(encoding="utf-8")
    detector = wrapper_paths[3].read_text(encoding="utf-8")
    boot_policy = wrapper_paths[5].read_text(encoding="utf-8")
    check(
        "DBUS_SESSION_BUS_ADDRESS" in root_wrapper
        and "/usr/lib/velaris-live/bin" in root_wrapper
        and "runuser -u velaris" in url_bridge,
        "support URLs are delegated back to the unprivileged live browser session",
    )
    check(
        "10de:" in detector
        and "1002:" in detector
        and "8086:" in detector
        and "systemd-detect-virt" in detector
        and "x86-64-v3 (supported" in detector,
        "hardware detector covers NVIDIA, AMD, Intel, VMs, and CPU v3 capability",
    )
    udev_policy = PROFILE / "airootfs/usr/lib/udev/rules.d/00-velaris-gpu-policy.rules"
    check(
        udev_policy.is_file()
        and 'ATTR{vendor}==\"0x10de\"' in udev_policy.read_text(encoding="utf-8")
        and "0x1e00" in boot_policy
        and "blacklist nouveau" in boot_policy
        and "blacklist nvidia" in boot_policy,
        "live boot selects NVIDIA Open or Nouveau before generic udev driver loading",
    )
    sddm_live = (PROFILE / "airootfs/etc/sddm.conf.d/autologin.conf").read_text(encoding="utf-8")
    display_helper = wrapper_paths[4].read_text(encoding="utf-8")
    check(
        "Session=plasmax11" in sddm_live and "xrandr --auto" in display_helper,
        "live session uses the broad X11 fallback and requests the preferred display mode",
    )


def validate_packages_and_performance() -> None:
    package_file = PROFILE / "packages.x86_64"
    packages = [
        line.strip()
        for line in package_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    duplicates = sorted({package for package in packages if packages.count(package) > 1})
    check(not duplicates, f"lista de pacotes não contém duplicatas{': ' + ', '.join(duplicates) if duplicates else ''}")

    package_names = {package.split("/", 1)[-1] for package in packages}
    required = {
        "linux-cachyos-bore-lto",
        "linux-cachyos",
        "linux-cachyos-lts",
        "linux",
        "linux-cachyos-bore-lto-nvidia-open",
        "linux-cachyos-nvidia-open",
        "linux-cachyos-lts-nvidia-open",
        "nvidia-open",
        "nvidia-utils",
        "lib32-nvidia-utils",
        "archlinux-keyring",
        "cachyos-keyring",
        "cachyos-mirrorlist",
        "cachyos-v3-mirrorlist",
        "cachyos-calamares",
        "grub",
        "efibootmgr",
        "syslinux",
        "plasma-x11-session",
        "cachyos-ananicy-rules",
        "power-profiles-daemon",
        "cryptsetup",
        "lvm2",
        "mkinitcpio-openswap",
        "vulkan-nouveau",
        "lib32-vulkan-nouveau",
        "vulkan-radeon",
        "lib32-vulkan-radeon",
        "vulkan-intel",
        "lib32-vulkan-intel",
        "vulkan-virtio",
        "lib32-vulkan-virtio",
        "intel-media-driver",
        "pciutils",
        "open-vm-tools",
        "virtualbox-guest-utils",
        "qemu-guest-agent",
        "spice-vdagent",
        "fish",
        "pacman-contrib",
    }
    check(required <= package_names, "selectable kernels, matched graphics stacks, VM tools, and installer packages are present")
    check(not {"iwd", "dhcpcd"} & package_names, "não há pilhas de rede concorrentes com o NetworkManager")
    check(
        not {"zsh", "zsh-completions", "zsh-syntax-highlighting", "zsh-autosuggestions"} & package_names,
        "plugins Zsh interpretados não permanecem instalados junto do Fish",
    )

    fish_config = PROFILE / "airootfs/etc/skel/.config/fish/config.fish"
    fish_text = fish_config.read_text(encoding="utf-8") if fish_config.is_file() else ""
    check(
        fish_config.is_file()
        and "XDG_RUNTIME_DIR/velaris-fastfetch-shown" in fish_text
        and "command fastfetch" in fish_text,
        "Fastfetch do Fish aparece somente uma vez por sessão",
    )

    profile_texts: list[tuple[Path, str]] = []
    for path in PROFILE.rglob("*"):
        if not path.is_file():
            continue
        try:
            data = path.read_bytes()
            if b"\0" in data:
                continue
            profile_texts.append((path, data.decode("utf-8")))
        except (OSError, UnicodeError):
            continue

    def contains(pattern: str) -> list[str]:
        return [str(path.relative_to(ROOT)) for path, text in profile_texts if pattern in text]

    check(not contains("LIBGL_ALWAYS_SOFTWARE"), "renderização por software não é forçada globalmente")
    check(not contains("LatencyPolicy=ExtremelyLow") and not contains("Backend=OpenGL"), "KWin escolhe automaticamente backend e latência")
    check(not contains("TrustAll"), "repositórios não desativam verificação de assinatura")
    check(not (PROFILE / "airootfs/etc/pacman.d/cachyos-mirrorlist").exists(), "mirrorlist oficial do pacote CachyOS não é sobrescrita")
    build_pacman = (PROFILE / "pacman.conf").read_text(encoding="utf-8")
    runtime_pacman = (PROFILE / "airootfs/etc/pacman.conf").read_text(encoding="utf-8")
    check(
        "Architecture = x86_64 x86_64_v3" in build_pacman
        and build_pacman.index("[cachyos]") < build_pacman.index("[cachyos-v3]")
        and "#[cachyos-v3]" in runtime_pacman,
        "v3 kernel packages build safely while the installed v3 repository stays opt-in",
    )
    forced_xorg = [
        PROFILE / "airootfs/etc/X11/xorg.conf.d/10-vmware.conf",
        PROFILE / "airootfs/etc/X11/xorg.conf.d/10-modesetting.conf",
    ]
    check(not any(path.exists() for path in forced_xorg), "Xorg não força driver virtual nem desativa aceleração")

    sysctl = (PROFILE / "airootfs/etc/sysctl.d/10-velaris-performance.conf").read_text(encoding="utf-8")
    check("vm.overcommit_memory" not in sysctl, "memória virtual não usa overcommit agressivo")
    check("vm.dirty_bytes" in sysctl and "vm.dirty_background_bytes" in sysctl, "writeback usa limites absolutos estáveis")
    check("vm.swappiness = 100" in sysctl and "vm.page-cluster = 0" in sysctl, "ZRAM está configurada para uso efetivo")


def validate_first_boot(documents: dict[Path, object]) -> None:
    shellprocess = documents.get(MODULES / "shellprocess_firstboot.conf")
    services = documents.get(MODULES / "services-systemd_velaris.conf")
    bootloader = documents.get(MODULES / "bootloader_velaris.conf")
    packages = documents.get(MODULES / "packages_cleanup.conf")
    mount_config = documents.get(MODULES / "mount_velaris.conf")

    check(
        isinstance(shellprocess, dict) and "firstboot-plymouth" in repr(shellprocess.get("script", [])),
        "instalação prepara o tema Plymouth temporário do primeiro boot",
    )
    service_units = services.get("units", []) if isinstance(services, dict) else []
    service_actions = {
        str(unit.get("name")): str(unit.get("action"))
        for unit in service_units
        if isinstance(unit, dict)
    }
    check(
        any(isinstance(unit, dict) and unit.get("name") == "velaris-firstboot.service" and unit.get("action") == "enable" for unit in service_units),
        "serviço que restaura o Plymouth normal é habilitado no destino",
    )
    check(
        service_actions.get("cups.service") == "disable"
        and service_actions.get("cups.socket") == "enable",
        "sistema instalado ativa o CUPS somente por socket",
    )
    check(
        service_actions.get("earlyoom.service") == "enable"
        and service_actions.get("systemd-oomd.service") == "mask",
        "somente o earlyoom gerencia pressão extrema de memória",
    )
    check(
        service_actions.get("fstrim.timer") == "enable"
        and service_actions.get("paccache.timer") == "enable",
        "TRIM e limpeza segura do cache de pacotes usam timers",
    )
    check(
        service_actions.get("bluetooth.service") == "disable"
        and service_actions.get("velaris-performance-profile.service") == "enable",
        "Bluetooth is not forced on and the selected power profile is applied",
    )
    firstboot_service = PROFILE / "airootfs/usr/lib/systemd/system/velaris-firstboot.service"
    check(firstboot_service.is_file(), "unidade de finalização do primeiro boot existe")
    service_text = firstboot_service.read_text(encoding="utf-8") if firstboot_service.is_file() else ""
    check(
        all(
            token in service_text
            for token in (
                "ConditionPathExists=/var/lib/velaris/firstboot-plymouth",
                "ConditionPathExists=!/run/archiso/bootmnt",
                "ExecStart=/usr/bin/plymouth-set-default-theme velaris",
                "ExecStart=/usr/bin/mkinitcpio -P",
                "ExecStart=/usr/bin/rm -f /var/lib/velaris/firstboot-plymouth",
            )
        ),
        "unidade restaura o tema normal, reconstrói o initramfs e remove o marcador",
    )
    check(isinstance(bootloader, dict) and bootloader.get("efiBootLoader") == "grub", "Calamares instala GRUB explicitamente")
    boot_params = bootloader.get("kernelParams", []) if isinstance(bootloader, dict) else []
    grubcfg = documents.get(MODULES / "grubcfg_velaris.conf")
    grub_params = grubcfg.get("kernel_params", []) if isinstance(grubcfg, dict) else []
    check(
        "zswap.enabled=0" in boot_params and "zswap.enabled=0" in grub_params,
        "zswap fica desativado no sistema instalado quando ZRAM está ativa",
    )

    mount_options = mount_config.get("mountOptions", []) if isinstance(mount_config, dict) else []
    btrfs_options: list[str] = []
    for entry in mount_options:
        if isinstance(entry, dict) and entry.get("filesystem") == "btrfs":
            btrfs_options = [str(option) for option in entry.get("options", [])]
            break
    check(
        "compress=zstd:1" in btrfs_options and "noatime" in btrfs_options,
        "installed Btrfs uses low-cost compression without access-time writes",
    )

    grubcfg = documents.get(MODULES / "grubcfg_velaris.conf")
    grub_defaults = grubcfg.get("defaults", {}) if isinstance(grubcfg, dict) else {}
    check(
        isinstance(grub_defaults, dict)
        and grub_defaults.get("GRUB_DISABLE_OS_PROBER") is False,
        "GRUB OS probing remains enabled for dual-boot discovery",
    )

    removed_packages: set[str] = set()
    if isinstance(packages, dict):
        for operation in packages.get("operations", []):
            if isinstance(operation, dict):
                removed_packages.update(str(item) for item in operation.get("remove", []))
    check(
        {"cachyos-calamares", "mkinitcpio-archiso", "syslinux"} <= removed_packages,
        "pacotes exclusivos do live têm remoção obrigatória no destino",
    )

    keyring = documents.get(MODULES / "shellprocess_keyring.conf")
    keyring_script = repr(keyring.get("script", [])) if isinstance(keyring, dict) else ""
    check(
        "pacman-key --init" in keyring_script
        and "pacman-key --populate archlinux cachyos" in keyring_script
        and "F3B607488DB35A47" in keyring_script,
        "Calamares prepara o chaveiro Arch Linux e CachyOS no destino",
    )

    selection_script = PROFILE / "airootfs/usr/lib/velaris/apply-selections"
    selection_text = selection_script.read_text(encoding="utf-8") if selection_script.is_file() else ""
    check(
        all(
            token in selection_text
            for token in (
                "linux-cachyos-bore-lto",
                "linux-cachyos-lts",
                'selected_kernel="linux"',
                "x86-64-v3 (supported",
                "nvidia_drm modeset=1",
                "systemd-detect-virt",
                "FILES=()",
                '"${module_dir}/vmlinuz"',
                "remove_candidates+=(cachyos-v3-mirrorlist)",
                "Architecture = x86_64",
            )
        ),
        "selection helper gates v3, keeps one kernel, configures NVIDIA, and handles VMs",
    )
    power_service = PROFILE / "airootfs/usr/lib/systemd/system/velaris-performance-profile.service"
    power_helper = PROFILE / "airootfs/usr/lib/velaris/apply-runtime-profile"
    check(
        power_service.is_file()
        and power_helper.is_file()
        and "powerprofilesctl set" in power_helper.read_text(encoding="utf-8"),
        "power-profile selection has a non-fatal systemd application path",
    )


def validate_shell() -> None:
    shell_files = sorted(ROOT.glob("*.sh")) + sorted((ROOT / ".devcontainer").glob("*.sh"))
    shell_files += sorted(PROFILE.rglob("*.sh"))
    for path in PROFILE.rglob("*"):
        if not path.is_file() or path in shell_files:
            continue
        try:
            if path.open("rb").readline().strip() == b"#!/usr/bin/env bash":
                shell_files.append(path)
        except OSError:
            continue
    shell_files = sorted(set(shell_files))
    failures: list[str] = []
    for path in shell_files:
        result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True, check=False)
        if result.returncode:
            failures.append(f"{path.relative_to(ROOT)}: {result.stderr.strip()}")
    check(not failures, "scripts Bash passam em bash -n")
    for failure in failures:
        print(f"       {failure}")

    helper_paths = [
        PROFILE / "airootfs/usr/bin/velaris-calamares",
        PROFILE / "airootfs/usr/lib/velaris-live/calamares-root",
        PROFILE / "airootfs/usr/lib/velaris-live/display-setup",
        PROFILE / "airootfs/usr/lib/velaris-live/prepare-installer",
        PROFILE / "airootfs/usr/lib/velaris-live/gpu-module-policy",
        PROFILE / "airootfs/usr/lib/velaris-live/bin/xdg-open",
        PROFILE / "airootfs/usr/lib/velaris/apply-selections",
        PROFILE / "airootfs/usr/lib/velaris/apply-runtime-profile",
    ]
    check(
        all(path.is_file() and path.stat().st_mode & 0o111 for path in helper_paths),
        "all installer and runtime shell helpers are executable",
    )

    fish_config = PROFILE / "airootfs/etc/skel/.config/fish/config.fish"
    fish_binary = shutil.which("fish")
    if fish_binary:
        result = subprocess.run(
            [fish_binary, "--no-execute", str(fish_config)],
            capture_output=True,
            text=True,
            check=False,
        )
        check(result.returncode == 0, "configuração Fish passa na validação de sintaxe")
        if result.returncode:
            print(f"       {result.stderr.strip()}")
    else:
        print("[INFO] fish não está disponível; a sintaxe será validada no GitHub Actions")


def validate_profiledef() -> None:
    profiledef = (PROFILE / "profiledef.sh").read_text(encoding="utf-8")
    name_match = re.search(r'^iso_name="([^"]+)"', profiledef, flags=re.MULTILINE)
    iso_name = name_match.group(1) if name_match else ""
    check(bool(re.fullmatch(r"[a-z0-9]+", iso_name)), "iso_name usa somente caracteres aceitos pelo archiso")
    check("'-comp' 'zstd'" in profiledef, "SquashFS usa Zstd para inicialização e instalação rápidas")

    mkinitcpio = (PROFILE / "airootfs/etc/mkinitcpio.conf").read_text(encoding="utf-8")
    hooks_match = re.search(r"^HOOKS=\(([^)]*)\)", mkinitcpio, flags=re.MULTILINE)
    hooks = hooks_match.group(1).split() if hooks_match else []
    required_hooks = {"base", "udev", "microcode", "modconf", "kms", "plymouth", "archiso", "block", "filesystems"}
    check(required_hooks <= set(hooks), "initramfs live contém microcode, KMS, Plymouth e hooks do Archiso")
    check(
        all(name in hooks for name in ("kms", "plymouth", "archiso"))
        and hooks.index("kms") < hooks.index("plymouth") < hooks.index("archiso"),
        "hooks gráficos do initramfs live estão em ordem segura",
    )
    check(
        "/usr/lib/udev/rules.d/00-velaris-gpu-policy.rules" in mkinitcpio
        and "/usr/lib/velaris-live/gpu-module-policy" in mkinitcpio,
        "early live GPU policy is embedded in the initramfs",
    )

    live_boot_configs = [
        PROFILE / "efiboot/loader/entries/velaris.conf",
        PROFILE / "efiboot/loader/entries/velaris-fallback.conf",
        PROFILE / "grub/grub.cfg",
        PROFILE / "syslinux/syslinux.cfg",
    ]
    check(
        all("zswap.enabled=0" in path.read_text(encoding="utf-8") for path in live_boot_configs),
        "todas as rotas de boot live evitam zswap duplicada com ZRAM",
    )

    locale = (PROFILE / "airootfs/etc/locale.conf").read_text(encoding="utf-8")
    vconsole = (PROFILE / "airootfs/etc/vconsole.conf").read_text(encoding="utf-8")
    customize = (PROFILE / "airootfs/root/customize_airootfs.sh").read_text(encoding="utf-8")
    mirrorlist = (PROFILE / "airootfs/etc/pacman.d/mirrorlist").read_text(encoding="utf-8")
    check(
        "LANG=en_US.UTF-8" in locale
        and "KEYMAP=us" in vconsole
        and "/usr/share/zoneinfo/UTC" in customize
        and "geo.mirror.pkgbuild.com" in mirrorlist,
        "sessão live inicia em inglês, teclado US, UTC e mirrors globais",
    )
    autologin = (PROFILE / "airootfs/etc/sddm.conf.d/autologin.conf").read_text(encoding="utf-8")
    display_autostart = PROFILE / "airootfs/etc/xdg/autostart/00-velaris-display-setup.desktop"
    check(
        "Session=plasmax11" in autologin
        and display_autostart.is_file()
        and "/usr/lib/velaris-live/display-setup" in display_autostart.read_text(encoding="utf-8"),
        "live desktop starts with the compatible session and display detector",
    )

    metadata_paths = [
        PROFILE / "airootfs/etc/calamares/branding/velaris/branding.desc",
        PROFILE / "airootfs/etc/os-release",
        PROFILE / "airootfs/usr/share/velaris/README",
    ]
    profile_text = "\n".join(path.read_text(encoding="utf-8") for path in metadata_paths)
    check(
        "github.com/bonecopreparado/velaris" not in profile_text,
        "metadados e suporte apontam para a organização Caeluum",
    )


def validate_workflow() -> None:
    workflow = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
    check("runs-on: [self-hosted, Linux, X64]" in workflow, "workflow usa o runner self-hosted Linux x86-64")
    check(
        'test "${RUNNER_NAME:-}" = "lenovo-server"' in workflow,
        "workflow confirma o nome exato lenovo-server",
    )
    check(
        "github.event.pull_request.head.repo.full_name == github.repository" in workflow,
        "runner particular não executa código vindo de forks",
    )
    check(
        'rm -rf -- "$GITHUB_WORKSPACE/work" "$GITHUB_WORKSPACE/out"' in workflow,
        "workflow limpa os artefatos temporários do runner",
    )

    build = (ROOT / "build.sh").read_text(encoding="utf-8")
    check(
        "unsquashfs" in build
        and "--list-keys F3B607488DB35A47" in build
        and "A chave de assinatura do CachyOS não está na ISO final" in build,
        "build inspeciona o chaveiro ativo dentro do SquashFS final",
    )

    check(
        (ROOT / "KNOWN_ISSUES.md").is_file()
        and (ROOT / ".github/ISSUE_TEMPLATE/bug_report.yml").is_file()
        and all(
            token in (ROOT / "README.md").read_text(encoding="utf-8")
            for token in ("BORE+LTO", "Early live-boot selection", "Install alongside")
        ),
        "English project docs cover hardware selection, dual boot, and support",
    )


def main() -> int:
    print("Validando perfil Velaris...\n")
    documents = validate_yaml_and_instances()
    validate_branding(documents)
    validate_installer_choices(documents)
    validate_live_identity(documents)
    validate_packages_and_performance()
    validate_first_boot(documents)
    validate_shell()
    validate_profiledef()
    validate_workflow()

    if FAILURES:
        print(f"\nValidação falhou com {len(FAILURES)} problema(s).")
        return 1
    print("\nPerfil Velaris validado com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
