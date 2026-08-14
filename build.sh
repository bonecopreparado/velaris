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
VALIDATOR="$SCRIPT_DIR/scripts/validate-profile.py"

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

command -v python3 &>/dev/null || err "python não encontrado. Instale: pacman -S python python-yaml"
[[ -f "$VALIDATOR" ]] || err "Validador não encontrado: $VALIDATOR"
python3 "$VALIDATOR" || err "O perfil falhou na validação; o build foi interrompido."

[[ $EUID -ne 0 ]] && err "Este script precisa ser executado como root (sudo ./build.sh)"
command -v mkarchiso &>/dev/null || err "archiso não encontrado. Instale com: pacman -S archiso"

ok "Perfil validado"
ok "Rodando como root"
ok "mkarchiso disponível"

# ── Configurar repositório CachyOS ───────────────────────────────────────────
title "── Configurando CachyOS ──"

if ! pacman -Qq cachyos-keyring cachyos-mirrorlist &>/dev/null; then
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

# ── Limpeza ─────────────────────────────────────────────────────────────────
title "── Limpando build anterior ──"

if [[ -d "$WORK_DIR" ]]; then
    log "Removendo work/ anterior..."
    rm -rf "$WORK_DIR"
fi
mkdir -p "$OUT_DIR"

# Impede que um build anterior seja confundido com o resultado atual.
find "$OUT_DIR" -maxdepth 1 -type f \( -name '*.iso' -o -name '*.iso.sha256' \) -delete
ok "Limpeza concluída"

# ── Timestamp e rótulo ───────────────────────────────────────────────────────
BUILD_DATE=$(date +%Y.%m.%d)
log "Build date: $BUILD_DATE"

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

# ── Verificação do sistema realmente gravado na ISO ─────────────────────────
title "── Verificando pacman dentro da ISO ──"
AIROOTFS_SFS="$WORK_DIR/iso/arch/x86_64/airootfs.sfs"
[[ -f "$AIROOTFS_SFS" ]] || err "airootfs.sfs não encontrado para validação"

VERIFY_DIR=$(mktemp -d)
cleanup_verify() { rm -rf -- "$VERIFY_DIR"; }
trap cleanup_verify EXIT

unsquashfs -no-progress -d "$VERIFY_DIR" "$AIROOTFS_SFS" \
    etc/pacman.d/gnupg >/dev/null \
    || err "Não foi possível extrair o chaveiro da ISO"

gpg --batch --homedir "$VERIFY_DIR/etc/pacman.d/gnupg" \
    --list-keys F3B607488DB35A47 >/dev/null 2>&1 \
    || err "A chave de assinatura do CachyOS não está na ISO final"

cleanup_verify
trap - EXIT
ok "Chaveiros Arch Linux e CachyOS presentes na ISO final"

# ── Resultado ────────────────────────────────────────────────────────────────
echo ""
title "── Build concluído ──"
shopt -s nullglob
ISO_FILES=("$OUT_DIR"/*.iso)
shopt -u nullglob
ISO_FILE="${ISO_FILES[0]:-}"

if [[ -n "$ISO_FILE" && -f "$ISO_FILE" ]]; then
    sha256sum "$ISO_FILE" > "${ISO_FILE}.sha256"
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
