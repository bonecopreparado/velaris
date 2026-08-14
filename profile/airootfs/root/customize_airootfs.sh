#!/usr/bin/env bash
# Velaris — customize_airootfs.sh
set -euo pipefail

echo "[Velaris] Customizando airootfs..."

# ── Locale e timezone ─────────────────────────────────────────────────────────
grep -qxF "pt_BR.UTF-8 UTF-8" /etc/locale.gen || echo "pt_BR.UTF-8 UTF-8" >> /etc/locale.gen
grep -qxF "en_US.UTF-8 UTF-8" /etc/locale.gen || echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen
ln -sf /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime

# ── Desativa firstboot/initial-setup ─────────────────────────────────────────
systemctl mask systemd-firstboot.service 2>/dev/null || true
systemctl mask initial-setup.service 2>/dev/null || true

# ── Grupo autologin — OBRIGATÓRIO pro PAM ────────────────────────────────────
groupadd -r autologin 2>/dev/null || true

# ── Usuário live: velaris ─────────────────────────────────────────────────────
if ! id "velaris" &>/dev/null; then
    useradd -m \
        -G wheel,audio,video,optical,storage,network,lp,autologin \
        -s /bin/zsh \
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
systemctl enable bluetooth.service
systemctl enable cups.service      2>/dev/null || true
systemctl enable irqbalance.service
systemctl enable earlyoom.service
systemctl enable systemd-timesyncd.service 2>/dev/null || true
systemctl enable fstrim.timer 2>/dev/null || true

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

# ── ZSH ───────────────────────────────────────────────────────────────────────
chsh -s /bin/zsh root
cp /etc/skel/.zshrc /root/.zshrc 2>/dev/null || true
cp /etc/skel/.zshrc /home/velaris/.zshrc 2>/dev/null || true
chown velaris:velaris /home/velaris/.zshrc 2>/dev/null || true

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

# ── Cache de ícones (garante que o tema velaris seja reconhecido) ───────────
gtk-update-icon-cache -f /usr/share/icons/velaris 2>/dev/null || true
gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true

# ── Garante que o initramfs live contém o tema Plymouth padrão ───────────────
mkinitcpio -P 2>&1 || echo "[Velaris] AVISO: mkinitcpio -P falhou, verifique MODULES/HOOKS"

# ── Limpeza ───────────────────────────────────────────────────────────────────
pacman -Scc --noconfirm 2>/dev/null || true
rm -rf /var/cache/pacman/pkg/* /tmp/*

echo "[Velaris] Concluído ✓"
