<div align="center">
  <h1>Velaris</h1>
  <p>Arch Linux com kernel CachyOS e KDE Plasma, focada em desempenho previsível e estabilidade</p>

  ![Base](https://img.shields.io/badge/base-Arch_Linux-1793D1?style=flat-square&logo=arch-linux)
  ![Kernel](https://img.shields.io/badge/kernel-CachyOS_BORE+LTO-orange?style=flat-square)
  ![DE](https://img.shields.io/badge/DE-KDE_Plasma-blue?style=flat-square&logo=kde)
  ![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
</div>

---

## Sobre

**Velaris** é uma distribuição Linux baseada em Arch, com KDE Plasma 6 e uma seleção enxuta de aplicativos. O projeto busca desempenho real sem depender de ajustes globais agressivos que prejudiquem compatibilidade, áudio, gráficos ou máquinas com pouca memória.

## Stack

| Componente       | Escolha                        |
|-----------------|-------------------------------|
| Base            | Arch Linux                    |
| Kernel          | `linux-cachyos`               |
| Scheduler       | BORE (Budget Order-Robust)    |
| Compilação      | LTO (Link Time Optimization)  |
| Desktop         | KDE Plasma (debloated)        |
| Display Manager | SDDM                          |
| Audio           | PipeWire                      |
| Init            | systemd                       |

## Pilares do projeto

- **Desempenho:** kernel CachyOS, ZRAM, Ananicy C++, `irqbalance` e SquashFS com Zstd.
- **Estabilidade:** limites seguros de writeback, `earlyoom`, uma única pilha de rede e configurações gráficas conservadoras.
- **Instalação limpa:** o Calamares usa configurações próprias da Velaris e não copia usuário, autologin, sudo ou privilégios da sessão live.
- **Compatibilidade:** Wayland é a sessão principal, com Plasma X11 disponível como alternativa.

## Validar antes do build

```bash
python3 scripts/validate-profile.py
```

O validador confere a estrutura do Calamares, os arquivos YAML, a separação entre live e sistema instalado, os pacotes essenciais e a sintaxe dos scripts.

## Build no GitHub Codespaces

### 1. Abrir o Codespace
Clique em **Code → Codespaces → Create codespace on main**  
O ambiente Arch Linux sobe automaticamente.

### 2. Rodar o build
```bash
sudo ./build.sh
```

A ISO e seu SHA-256 ficarão em `out/velaris-*.iso` e `out/velaris-*.iso.sha256`.

### 3. Baixar a ISO
No painel do Codespaces, vá em **Explorer → out/** e faça o download da ISO.

## Build com Docker (local)
```bash
docker build -t velaris-builder .devcontainer/
docker run --privileged \
  -v "$(pwd)":/workspace \
  -w /workspace \
  velaris-builder \
  ./build.sh
```

O build apaga apenas resultados antigos dentro de `work/` e arquivos `.iso` anteriores em `out/`.

## Runner self-hosted

O GitHub Actions usa a máquina x86-64 chamada `lenovo-server`, com as labels padrão `self-hosted`, `Linux` e `X64`. Ela precisa manter o GitHub Actions Runner e o Docker ativos; o job usa um contêiner Arch Linux privilegiado porque o `mkarchiso` precisa montar a imagem.

Por segurança, pull requests vindos de forks não executam no `lenovo-server`. Builds manuais, pushes na `main` e PRs criados por branches deste próprio repositório podem usar a máquina. Ao terminar, o workflow remove `work/` e `out/` para não deixar arquivos pertencentes ao root travando a próxima execução.

## Testar a instalação

Use uma VM com disco virtual vazio e siga [docs/TESTING.md](docs/TESTING.md). O teste precisa confirmar, entre outros pontos, que o usuário live `velaris` não existe depois da instalação e que o Calamares não abre novamente.

O estado técnico atual e as decisões desta revisão estão em [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

## Estrutura do Repositório
```
Velaris/
├── .devcontainer/          # Ambiente Codespaces (Arch Linux)
├── .github/workflows/      # GitHub Actions (build automático)
├── docs/                   # Status técnico e checklist de teste
├── profile/                # Perfil archiso
│   ├── airootfs/           # Arquivos que vão para o rootfs
│   ├── efiboot/            # Boot UEFI
│   ├── grub/               # Boot BIOS legado
│   ├── packages.x86_64     # Lista de pacotes
│   ├── pacman.conf         # Pacman do build
│   └── profiledef.sh       # Definição do perfil
├── scripts/                # Validação estática do perfil
└── build.sh                # Script de build principal
```

## Licença
MIT — feito com ☕ pelo time Caelum 
