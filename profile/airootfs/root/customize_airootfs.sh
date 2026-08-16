#!/usr/bin/env bash
# Velaris — customize_airootfs.sh
set -euo pipefail

echo "[Velaris] Customizing airootfs..."

# ── Locale e timezone ─────────────────────────────────────────────────────────
grep -qxF "pt_BR.UTF-8 UTF-8" /etc/locale.gen || echo "pt_BR.UTF-8 UTF-8" >> /etc/locale.gen
grep -qxF "en_US.UTF-8 UTF-8" /etc/locale.gen || echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen
printf 'LANG=en_US.UTF-8\n' > /etc/locale.conf
ln -sf /usr/share/zoneinfo/UTC /etc/localtime

# ── Chaveiros do pacman ──────────────────────────────────────────────────────
# Ter os pacotes *-keyring instalados não popula automaticamente o chaveiro
# ativo do sistema live. Sem isto, o banco assinado do CachyOS é rejeitado.
echo "[Velaris] Initializing Arch Linux and CachyOS keyrings..."
rm -rf /etc/pacman.d/gnupg
install -d -m 0755 /etc/pacman.d/gnupg
pacman-key --init
pacman-key --populate archlinux cachyos
pacman-key --finger F3B607488DB35A47 >/dev/null

# ── Desativa firstboot/initial-setup ─────────────────────────────────────────
systemctl mask systemd-firstboot.service 2>/dev/null || true
systemctl mask initial-setup.service 2>/dev/null || true

# ── Grupo autologin — OBRIGATÓRIO pro PAM ────────────────────────────────────
groupadd -r autologin 2>/dev/null || true

# ── Usuário live: velaris ─────────────────────────────────────────────────────
if ! id "velaris" &>/dev/null; then
    useradd -m \
        -G wheel,audio,video,optical,storage,network,lp,autologin \
        -s /usr/bin/fish \
        velaris
fi

# Senha de acesso manual caso o autologin não funcione
echo "velaris:velaris" | chpasswd

# Root não recebe senha conhecida. Administração no live é feita via sudo.
passwd -l root

# Sudo sem senha no live
echo "velaris ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/velaris
chmod 440 /etc/sudoers.d/velaris

# ── Serviços ──────────────────────────────────────────────────────────────────
systemctl enable NetworkManager.service
systemctl enable NetworkManager-dispatcher.service
systemctl disable NetworkManager-wait-online.service 2>/dev/null || true
systemctl enable sddm.service
systemctl disable bluetooth.service 2>/dev/null || true
systemctl disable vmtoolsd.service vmware-vmblock-fuse.service \
    vboxservice.service qemu-guest-agent.service spice-vdagentd.service \
    2>/dev/null || true
systemctl disable cups.service     2>/dev/null || true
systemctl enable cups.socket       2>/dev/null || true
systemctl enable irqbalance.service
systemctl enable earlyoom.service
systemctl mask systemd-oomd.service 2>/dev/null || true
systemctl enable systemd-timesyncd.service 2>/dev/null || true
systemctl enable fstrim.timer 2>/dev/null || true

# Keep optional Plasma compatibility bridges out of the default session. They
# can be restored with `systemctl --global unmask <unit>` when needed.
systemctl --global mask kde-baloo.service 2>/dev/null || true
systemctl --global mask plasma-baloorunner.service 2>/dev/null || true
systemctl --global mask plasma-xembedsniproxy.service 2>/dev/null || true
systemctl --global mask plasma-gmenudbusmenuproxy.service 2>/dev/null || true

# open-vm-tools: causa conflito com Plasma Wayland em VMware
# Desativado por padrão — usuário habilita manualmente se precisar
# systemctl enable vmtoolsd.service  # desativado: causa hard lockup com vmwgfx/Wayland

# As regras oficiais do CachyOS estão na imagem, então o daemon pode operar
# sem ficar falhando em loop.
systemctl enable ananicy-cpp.service 2>/dev/null || true

# ── UFW ───────────────────────────────────────────────────────────────────────
ufw default deny incoming
ufw default allow outgoing
ufw --force enable

# ── Fish ──────────────────────────────────────────────────────────────────────
# useradd normally copies /etc/skel, but keep this explicit for reproducible
# live sessions when an existing home directory is reused during development.
install -d -m 0755 /home/velaris/.config/fish
install -m 0644 /etc/skel/.config/fish/config.fish /home/velaris/.config/fish/config.fish
chown -R velaris:velaris /home/velaris/.config/fish

# English is the live-session default. Calamares writes the user's selected
# locale to the installed system, and /home/velaris is never copied there.
install -d -m 0755 /home/velaris/.config/environment.d
printf 'LANG=en_US.UTF-8\nLC_MESSAGES=en_US.UTF-8\n' \
    > /home/velaris/.config/environment.d/10-velaris-live-locale.conf

# ── XDG dirs ─────────────────────────────────────────────────────────────────
su - velaris -c "xdg-user-dirs-update" 2>/dev/null || true

# ── Plymouth ─────────────────────────────────────────────────────────────────
plymouth-set-default-theme velaris 2>/dev/null || plymouth-set-default-theme spinner 2>/dev/null || true

# ── Atalho do instalador no desktop do live ───────────────────────────────────
mkdir -p /home/velaris/Desktop
cp /usr/share/applications/calamares.desktop /home/velaris/Desktop/
chmod +x /home/velaris/Desktop/calamares.desktop
chown -R velaris:velaris /home/velaris/Desktop

# Abre o Calamares automaticamente ao logar no live (usuário já existe,
# então /etc/skel/.config/autostart não chega até ele sozinho)
mkdir -p /home/velaris/.config/autostart
cp /usr/share/applications/calamares.desktop /home/velaris/.config/autostart/
chown -R velaris:velaris /home/velaris/.config

# NVIDIA's userspace package blacklists Nouveau. The live image must remain
# usable on pre-Turing cards, so driver-specific blacklisting is applied only
# to installed systems that selected NVIDIA Open.
rm -f /usr/lib/modprobe.d/nvidia-utils.conf

# Ensure all Velaris helpers retain executable permissions in the image.
chmod 0755 \
    /usr/bin/velaris-calamares \
    /usr/lib/velaris-live/calamares-root \
    /usr/lib/velaris-live/display-setup \
    /usr/lib/velaris-live/gpu-module-policy \
    /usr/lib/velaris-live/prepare-installer \
    /usr/lib/velaris-live/bin/xdg-open \
    /usr/lib/velaris/record-selection \
    /usr/lib/velaris/apply-selections \
    /usr/lib/velaris/apply-runtime-profile

# ── Cache de ícones (garante que o tema velaris seja reconhecido) ───────────
gtk-update-icon-cache -f /usr/share/icons/velaris 2>/dev/null || true
gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true

# ── Garante que o initramfs live contém o tema Plymouth padrão ───────────────
mkinitcpio -P 2>&1 || echo "[Velaris] WARNING: mkinitcpio -P failed; check MODULES/HOOKS"

# ── Limpeza ───────────────────────────────────────────────────────────────────
# Limpa somente pacotes baixados. `pacman -Scc` também remove os bancos de
# sincronização e fazia o primeiro `pacman -S pacote` dizer que core/extra não
# existiam.
rm -rf /var/cache/pacman/pkg/* /tmp/*

echo "[Velaris] Complete ✓"
