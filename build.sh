#!/usr/bin/env bash
# ============================================================
#  Velaris — Script de Build
#  Gera a ISO usando archiso + kernel CachyOS BORE+LTO
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE_DIR="$SCRIPT_DIR/profile"
OUT_DIR="$SCRIPT_DIR/out"
WORK_DIR="$SCRIPT_DIR/work"

CYAN='\033[0;36m'; GREEN='\033[0;32m'
RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
BOLD='\033[1m'

log()   { echo -e "${CYAN}[*]${NC} $*"; }
ok()    { echo -e "${GREEN}[✓]${NC} $*"; }
err()   { echo -e "${RED}[✗]${NC} $*"; exit 1; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
title() { echo -e "\n${BOLD}$*${NC}\n"; }

# ── Banner ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}"
cat << 'BANNER'
 __   __   _           _
 \ \ / /__| | __ _ _ __(_)___
  \ V / _ \ |/ _` | '__| / __|
   | |  __/ | (_| | |  | \__ \
   |_|\___|_|\__,_|_|  |_|___/
         Velaris
BANNER
echo -e "${NC}"

# ── Verificações ─────────────────────────────────────────────────────────────
title "── Verificações ──"

[[ $EUID -ne 0 ]] && err "Este script precisa ser executado como root (sudo ./build.sh)"
command -v mkarchiso &>/dev/null || err "archiso não encontrado. Instale com: pacman -S archiso"

ok "Rodando como root"
ok "mkarchiso disponível"

# ── Configurar repositório CachyOS ───────────────────────────────────────────
title "── Configurando CachyOS ──"

if ! pacman -Qi cachyos-keyring &>/dev/null; then
    log "Instalando cachyos-keyring via pacman..."

    # Recebe e assina a chave CachyOS antes de adicionar o repo
    pacman-key --recv-keys F3B607488DB35A47 \
        --keyserver hkps://keyserver.ubuntu.com 2>/dev/null || \
    pacman-key --recv-keys F3B607488DB35A47 \
        --keyserver hkps://keys.openpgp.org 2>/dev/null || \
    warn "Keyserver inacessível — continuando com keyring local se disponível."
    pacman-key --lsign-key F3B607488DB35A47 2>/dev/null || true

    # Adiciona o repo CachyOS temporariamente no pacman.conf do sistema de build
    if ! grep -q "\[cachyos\]" /etc/pacman.conf; then
        cat >> /etc/pacman.conf << 'REPOCFG'

[cachyos]
Server = https://mirror.cachyos.org/repo/x86_64/$repo
Server = https://repo.cachyos.org/$repo/x86_64
REPOCFG
        log "Repositório CachyOS adicionado ao pacman.conf do build"
    fi

    # Sincroniza e instala — sem versão hardcoded
    pacman -Sy --noconfirm cachyos-keyring cachyos-mirrorlist \
        || err "Falha ao instalar cachyos-keyring. Verifique conexão e mirrors."

    ok "cachyos-keyring e mirrorlist instalados"
else
    ok "cachyos-keyring já instalado"
fi

# Garante que a chave CachyOS está no keyring local de build
pacman-key --recv-keys F3B607488DB35A47 \
    --keyserver hkps://keyserver.ubuntu.com 2>/dev/null || \
pacman-key --recv-keys F3B607488DB35A47 \
    --keyserver hkps://keys.openpgp.org 2>/dev/null || \
warn "Chave CachyOS não encontrada no keyserver — o keyring já instalado deve ser suficiente."
pacman-key --lsign-key F3B607488DB35A47 2>/dev/null || true

ok "Chave CachyOS configurada"

# ── Criar symlinks de serviços no airootfs ───────────────────────────────────
title "── Habilitando serviços no airootfs ──"

SYSTEMD_DIR="$PROFILE_DIR/airootfs/etc/systemd/system"

enable_service() {
    local service="$1"
    local target_dir="$2"
    mkdir -p "$SYSTEMD_DIR/$target_dir"
    ln -sf "/usr/lib/systemd/system/$service" \
        "$SYSTEMD_DIR/$target_dir/$service" 2>/dev/null || true
    log "Habilitado: $service → $target_dir"
}

# Display manager
ln -sf "/usr/lib/systemd/system/sddm.service" \
    "$SYSTEMD_DIR/display-manager.service" 2>/dev/null || true

# Serviços essenciais
enable_service "NetworkManager.service"              "multi-user.target.wants"
enable_service "NetworkManager-dispatcher.service"  "multi-user.target.wants"
enable_service "NetworkManager-wait-online.service" "network-online.target.wants"
enable_service "bluetooth.service"                  "multi-user.target.wants"

ok "Serviços configurados nos symlinks"

# ── Limpeza ─────────────────────────────────────────────────────────────────
title "── Limpando build anterior ──"

if [[ -d "$WORK_DIR" ]]; then
    log "Removendo work/ anterior..."
    rm -rf "$WORK_DIR"
fi
mkdir -p "$OUT_DIR"
ok "Limpeza concluída"

# ── Timestamp e rótulo ───────────────────────────────────────────────────────
BUILD_DATE=$(date +%Y.%m.%d)
ISO_LABEL="VELARIS_$(date +%Y%m)"
log "Build date: $BUILD_DATE | Label: $ISO_LABEL"

# ── Build da ISO ─────────────────────────────────────────────────────────────
title "── Build da ISO ──"
log "Iniciando mkarchiso..."
log "Profile: $PROFILE_DIR"
log "Output:  $OUT_DIR"
log "Work:    $WORK_DIR"
echo ""

mkarchiso -v \
    -w "$WORK_DIR" \
    -o "$OUT_DIR" \
    "$PROFILE_DIR"

# ── Resultado ────────────────────────────────────────────────────────────────
echo ""
title "── Build concluído ──"
ISO_FILE=$(ls "$OUT_DIR"/*.iso 2>/dev/null | head -1)
if [[ -n "$ISO_FILE" ]]; then
    ok "ISO gerada com sucesso!"
    echo ""
    echo -e "  ${BOLD}Arquivo:${NC} $ISO_FILE"
    echo -e "  ${BOLD}Tamanho:${NC} $(du -sh "$ISO_FILE" | cut -f1)"
    echo -e "  ${BOLD}SHA256:${NC}  $(sha256sum "$ISO_FILE" | cut -d' ' -f1)"
    echo ""
    echo -e "${CYAN}  Velaris está pronta! — Caelum${NC}"
else
    err "Nenhuma ISO encontrada em $OUT_DIR — verifique os logs acima."
fi
echo ""
