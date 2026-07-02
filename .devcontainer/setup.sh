#!/usr/bin/env bash
# Velaris — Setup do ambiente de build no Codespaces
set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${CYAN}[*]${NC} $*"; }
ok()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Velaris — Configurando ambiente   ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Inicializa o keyring do pacman
log "Inicializando keyring do pacman..."
pacman-key --init
pacman-key --populate archlinux
ok "Keyring do Arch inicializado"

# Adiciona a chave de assinatura do CachyOS
log "Adicionando chave do CachyOS..."
pacman-key --recv-keys F3B607488DB35A47 \
    --keyserver hkps://keyserver.ubuntu.com 2>/dev/null || \
pacman-key --recv-keys F3B607488DB35A47 \
    --keyserver hkps://keys.openpgp.org 2>/dev/null || \
warn "Não foi possível buscar a chave CachyOS automaticamente. Execute manualmente se necessário."
pacman-key --lsign-key F3B607488DB35A47 2>/dev/null || true
ok "Chave CachyOS configurada"

# Atualiza o sistema
log "Atualizando pacotes do ambiente de build..."
pacman -Syu --noconfirm
ok "Sistema atualizado"

# Permissões do script de build
chmod +x /workspace/build.sh 2>/dev/null || true

echo ""
ok "Ambiente pronto! Execute: sudo ./build.sh"
echo ""
