<div align="center">
  <img src="assets/velaris-logo.jpg" width="170" alt="Velaris logo">

  <h1>Velaris</h1>

  <p><strong>Arch Linux refinado para desempenho, estabilidade e uma experiência KDE Plasma limpa.</strong></p>

  <p>
    <a href="https://github.com/Caeluum/velaris/releases">Downloads</a>
    ·
    <a href="https://github.com/Caeluum/velaris/actions">Builds</a>
    ·
    <a href="https://github.com/Caeluum/velaris/issues">Issues</a>
    ·
    <a href="https://github.com/Caeluum">Caelum</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/status-beta-2563eb?style=for-the-badge" alt="Status: Beta">
    <img src="https://img.shields.io/badge/base-Arch_Linux-1793D1?style=for-the-badge&logo=archlinux&logoColor=white" alt="Base: Arch Linux">
    <img src="https://img.shields.io/badge/desktop-KDE_Plasma-1D99F3?style=for-the-badge&logo=kde&logoColor=white" alt="Desktop: KDE Plasma">
    <img src="https://img.shields.io/badge/arch-x86__64-111827?style=for-the-badge" alt="Architecture: x86-64">
  </p>

  <a href="https://github.com/Caeluum/velaris/actions/workflows/build.yml">
    <img src="https://github.com/Caeluum/velaris/actions/workflows/build.yml/badge.svg?branch=main" alt="Velaris ISO build">
  </a>
</div>

<br>

<p align="center">
  <img src="assets/velaris-wallpaper.jpg" width="100%" alt="Velaris wallpaper">
</p>

> [!IMPORTANT]
> Velaris está em desenvolvimento ativo. As imagens disponíveis atualmente são versões **Beta**: faça backup dos seus dados e teste a instalação em uma máquina virtual ou equipamento secundário antes de usar em produção.

## Sobre o Velaris

**Velaris** é uma distribuição Linux baseada em Arch criada pela [Caelum](https://github.com/Caeluum). O projeto combina o kernel CachyOS, KDE Plasma 6 e uma seleção cuidadosamente configurada de componentes para entregar um desktop rápido, responsivo e previsível.

O objetivo não é aplicar ajustes agressivos sem medição. Cada decisão deve preservar compatibilidade, segurança e estabilidade, especialmente em máquinas com pouca memória ou armazenamento mais lento.

## Pilares do projeto

| | Pilar | Objetivo |
|---|---|---|
| ⚡ | **Desempenho equilibrado** | Melhorar resposta do sistema, gerenciamento de memória e cargas interativas sem sacrificar estabilidade. |
| 🛡️ | **Base confiável** | Manter configurações conservadoras, firewall disponível e proteção contra falta de memória. |
| ✨ | **Plasma limpo** | Oferecer KDE Plasma 6 organizado, moderno e sem serviços ou aplicativos desnecessários. |
| 🧩 | **Compatibilidade** | Suportar hardware AMD e Intel, múltiplos sistemas de arquivos, PipeWire e ferramentas de instalação conhecidas. |
| 🔧 | **Projeto aberto** | Manter perfil, scripts de build e decisões técnicas visíveis para revisão e contribuição. |

## Stack principal

| Componente | Tecnologia |
|---|---|
| Base | Arch Linux |
| Kernel | `linux-cachyos` |
| Desktop | KDE Plasma 6 |
| Gerenciador de sessão | SDDM |
| Áudio | PipeWire + WirePlumber |
| Rede | NetworkManager |
| Inicialização | systemd |
| Bootloader | GRUB com suporte UEFI e BIOS legado |
| Instalador | Calamares |
| Sistema de arquivos padrão | Btrfs, com alternativas Ext4 e XFS |

## Recursos

- Kernel CachyOS voltado a cargas interativas e boa responsividade.
- ZRAM para reduzir o impacto da pressão de memória.
- Ananicy C++, `irqbalance`, GameMode e `earlyoom` integrados ao perfil.
- KDE Plasma 6 com animações e efeitos ajustados para uma experiência mais direta.
- PipeWire para áudio, vídeo e compatibilidade com aplicações modernas.
- Suporte a Btrfs, Ext4, XFS, NTFS, exFAT, LUKS e LVM.
- Sessão live com Calamares para uma instalação gráfica simples.
- Build automatizado e reprodução local com ArchISO.

## Download

As imagens publicadas ficam na página de [Releases](https://github.com/Caeluum/velaris/releases). Quando houver um arquivo de checksum junto da ISO, valide o download antes de criar o pendrive:

```bash
sha256sum -c velaris-*.iso.sha256
```

> [!WARNING]
> Não baixe ISOs do Velaris publicadas por contas ou sites não vinculados à organização Caelum.

## Instalação

1. Baixe a ISO mais recente e seu checksum.
2. Grave a imagem em um pendrive usando uma ferramenta confiável.
3. Inicie o computador pelo pendrive em modo UEFI ou BIOS legado.
4. Teste rede, áudio, vídeo e armazenamento na sessão live.
5. Abra o Calamares e revise cuidadosamente o particionamento antes de confirmar.

Como o instalador ainda está sendo estabilizado, mantenha um backup atualizado dos arquivos importantes.

## Compilar o projeto

### Arch Linux, CachyOS ou Codespaces

```bash
git clone https://github.com/Caeluum/velaris.git
cd velaris
sudo ./build.sh
```

A ISO e o checksum SHA-256 serão gravados no diretório `out/`.

### Docker

```bash
docker build -t velaris-builder .devcontainer/
docker run --rm --privileged \
  -v "$(pwd)":/workspace \
  -w /workspace \
  velaris-builder \
  ./build.sh
```

> [!NOTE]
> O ArchISO precisa montar sistemas de arquivos durante o build. Por isso, a execução em contêiner utiliza o modo privilegiado.

## Branches

| Branch | Finalidade |
|---|---|
| [`main`](https://github.com/Caeluum/velaris/tree/main) | Base pública principal do projeto. |
| [`agent/velaris-stability-lenovo-runner`](https://github.com/Caeluum/velaris/tree/agent/velaris-stability-lenovo-runner) | Revisão de estabilidade, Calamares, validação e build no runner `lenovo-server`. |

## Estrutura do repositório

```text
velaris/
├── .devcontainer/       # Ambiente de desenvolvimento e build em contêiner
├── .github/workflows/   # Automação do GitHub Actions
├── assets/              # Identidade visual usada na documentação
├── profile/             # Perfil ArchISO e sistema live
│   ├── airootfs/        # Arquivos inseridos no sistema raiz
│   ├── efiboot/         # Inicialização UEFI
│   ├── grub/            # Inicialização GRUB e BIOS legado
│   ├── packages.x86_64  # Pacotes incluídos na imagem
│   ├── pacman.conf      # Repositórios usados durante o build
│   └── profiledef.sh    # Definição principal do ArchISO
└── build.sh             # Entrada principal do build
```

Branches de desenvolvimento também podem conter documentação e validadores adicionais antes da integração à `main`.

## Roadmap

- Estabilizar completamente o Calamares e os cenários de particionamento.
- Medir boot, memória ociosa, responsividade e tamanho da instalação.
- Separar com mais precisão os pacotes da sessão live e do sistema instalado.
- Revisar serviços do Plasma com perfis seguros e reversíveis.
- Aprimorar os testes de hardware, VM, UEFI, BIOS e criptografia.
- Preparar a primeira versão estável oficial do Velaris.

## Contribuindo

Relatórios e contribuições são bem-vindos:

1. Verifique os [issues existentes](https://github.com/Caeluum/velaris/issues).
2. Abra um issue com logs, hardware utilizado e passos para reproduzir o problema.
3. Para código, crie uma branch no seu fork e envie um pull request com uma mudança focada.
4. Evite incluir chaves, tokens, senhas, imagens pessoais ou outros dados privados nos logs.

## Créditos

Velaris é desenvolvido pela **Caelum** e construído sobre o trabalho das comunidades [Arch Linux](https://archlinux.org/), [CachyOS](https://cachyos.org/), [KDE](https://kde.org/) e [Calamares](https://calamares.io/).

Este projeto é independente e não representa oficialmente os projetos upstream citados.

<div align="center">
  <sub>Built by <a href="https://github.com/Caeluum">Caelum</a> · Performance, stability and freedom.</sub>
</div>
