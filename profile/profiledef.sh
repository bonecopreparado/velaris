#!/usr/bin/env bash
# Velaris — Definição do perfil archiso

# O archiso atual restringe iso_name a caracteres minúsculos [a-z0-9].
iso_name="velaris"
iso_label="VELARIS_$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y%m)"
iso_publisher="Caelum"
iso_application="Velaris — Arch-based Linux Distribution"
iso_version="$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y.%m.%d)"
install_dir="arch"
buildmodes=('iso')
bootmodes=(
    'bios.syslinux'
    'uefi.systemd-boot'
)
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=(
    '-comp' 'zstd'
    '-Xcompression-level' '15'
    '-b' '1M'
)
bootstrap_tarball_compression=('zstd' '-c' '-T0' '--auto-threads=logical' '--long' '-19')

declare -A file_permissions=(
    ["/etc/shadow"]="0:0:400"
    ["/etc/gshadow"]="0:0:400"
    ["/root"]="0:0:750"
    ["/root/customize_airootfs.sh"]="0:0:755"
)
