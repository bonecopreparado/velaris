#!/usr/bin/env python3
"""Validação estática do perfil Archiso/Calamares da Velaris."""

from __future__ import annotations

import re
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
        instance_configs.append(MODULES / str(instance.get("config", "")))

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
        ("partition", "velaris"),
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
    }
    check(required_pairs <= instance_pairs, "instâncias críticas da instalação estão declaradas")

    exec_sequence = sequence_for(settings, "exec")
    ordered = (
        "removeuser@velaris" in exec_sequence
        and "users@velaris" in exec_sequence
        and exec_sequence.index("removeuser@velaris") < exec_sequence.index("users@velaris")
    )
    check(ordered, "conta live é removida antes da criação do usuário final")
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
    }
    check(required_excludes <= excludes, "unpackfs exclui identidade, autologin e privilégios do live")
    check(isinstance(removeuser, dict) and removeuser.get("username") == "velaris", "removeuser elimina a conta live")
    check(
        isinstance(users, dict)
        and users.get("doAutologin") is False
        and users.get("setRootPassword") is False,
        "usuário final não recebe autologin nem senha root reutilizada",
    )

    skel_autostart = PROFILE / "airootfs/etc/skel/.config/autostart/calamares.desktop"
    check(not skel_autostart.exists(), "Calamares não fica no autostart de novos usuários")

    customize = (PROFILE / "airootfs/root/customize_airootfs.sh").read_text(encoding="utf-8")
    check("passwd -l root" in customize and "passwd -d root" not in customize, "conta root do live permanece bloqueada")
    check("disable NetworkManager-wait-online.service" in customize, "sessão live não espera rede durante o boot")
    check(
        all(token in customize for token in ("pacman-key --init", "pacman-key --populate archlinux cachyos"))
        and not re.search(r"^\s*pacman\s+-Scc\b", customize, flags=re.MULTILINE),
        "live inicializa os chaveiros e preserva os bancos do pacman",
    )

    policy = (PROFILE / "airootfs/etc/polkit-1/rules.d/49-calamares.rules").read_text(encoding="utf-8")
    restricted_policy = all(
        token in policy
        for token in (
            'action.id === "io.calamares.calamares.pkexec.run"',
            'action.lookup("program") === "/usr/bin/calamares"',
            'subject.user === "velaris"',
            "subject.local",
            "subject.active",
        )
    )
    check(restricted_policy, "regra Polkit limita elevação ao Calamares da sessão live")

    desktop = (PROFILE / "airootfs/usr/share/applications/calamares.desktop").read_text(encoding="utf-8")
    check("Exec=/usr/bin/pkexec /usr/bin/calamares" in desktop, "atalho live chama o executável autorizado pelo Polkit")


def validate_packages_and_performance() -> None:
    package_file = PROFILE / "packages.x86_64"
    packages = [
        line.strip()
        for line in package_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    duplicates = sorted({package for package in packages if packages.count(package) > 1})
    check(not duplicates, f"lista de pacotes não contém duplicatas{': ' + ', '.join(duplicates) if duplicates else ''}")

    required = {
        "linux-cachyos",
        "archlinux-keyring",
        "cachyos-keyring",
        "cachyos-mirrorlist",
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
        "intel-media-driver",
    }
    check(required <= set(packages), "kernel, bootloaders, instalador, X11 e regras de desempenho estão presentes")
    check(not {"iwd", "dhcpcd"} & set(packages), "não há pilhas de rede concorrentes com o NetworkManager")

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

    check(
        isinstance(shellprocess, dict) and "firstboot-plymouth" in repr(shellprocess.get("script", [])),
        "instalação prepara o tema Plymouth temporário do primeiro boot",
    )
    service_units = services.get("units", []) if isinstance(services, dict) else []
    check(
        any(isinstance(unit, dict) and unit.get("name") == "velaris-firstboot.service" and unit.get("action") == "enable" for unit in service_units),
        "serviço que restaura o Plymouth normal é habilitado no destino",
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


def validate_shell() -> None:
    shell_files = sorted(ROOT.glob("*.sh")) + sorted((ROOT / ".devcontainer").glob("*.sh"))
    shell_files += sorted(PROFILE.rglob("*.sh"))
    failures: list[str] = []
    for path in shell_files:
        result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True, check=False)
        if result.returncode:
            failures.append(f"{path.relative_to(ROOT)}: {result.stderr.strip()}")
    check(not failures, "scripts Bash passam em bash -n")
    for failure in failures:
        print(f"       {failure}")


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
        and "Banco do pacman ausente na ISO final" in build,
        "build inspeciona chaveiros e bancos dentro do SquashFS final",
    )


def main() -> int:
    print("Validando perfil Velaris...\n")
    documents = validate_yaml_and_instances()
    validate_branding(documents)
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
