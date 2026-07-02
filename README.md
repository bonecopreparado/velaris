<div align="center">
  <h1>Velaris</h1>
  <p>Distro Linux baseada em Arch com kernel CachyOS BORE+LTO e KDE Plasma debloated</p>

  ![Base](https://img.shields.io/badge/base-Arch_Linux-1793D1?style=flat-square&logo=arch-linux)
  ![Kernel](https://img.shields.io/badge/kernel-CachyOS_BORE+LTO-orange?style=flat-square)
  ![DE](https://img.shields.io/badge/DE-KDE_Plasma-blue?style=flat-square&logo=kde)
  ![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
</div>

---

## Sobre

**Velaris** é uma distribuição Linux baseada em Arch, batizada com o nome da Velaris  
Focada em performance, leveza e uma experiência KDE Plasma limpa — sem bloatware.

## Stack

| Componente       | Escolha                        |
|-----------------|-------------------------------|
| Base            | Arch Linux                    |
| Kernel          | `linux-cachyos-bore-lto`      |
| Scheduler       | BORE (Budget Order-Robust)    |
| Compilação      | LTO (Link Time Optimization)  |
| Desktop         | KDE Plasma (debloated)        |
| Display Manager | SDDM                          |
| Audio           | PipeWire                      |
| Init            | systemd                       |

## Build no GitHub Codespaces

### 1. Abrir o Codespace
Clique em **Code → Codespaces → Create codespace on main**  
O ambiente Arch Linux sobe automaticamente.

### 2. Rodar o build
```bash
sudo ./build.sh
```

A ISO ficará em `out/Velaris-*.iso`.

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

## Estrutura do Repositório
```
Velaris/
├── .devcontainer/          # Ambiente Codespaces (Arch Linux)
├── .github/workflows/      # GitHub Actions (build automático)
├── profile/                # Perfil archiso
│   ├── airootfs/           # Arquivos que vão para o rootfs
│   ├── efiboot/            # Boot UEFI
│   ├── grub/               # Boot BIOS legado
│   ├── packages.x86_64     # Lista de pacotes
│   ├── pacman.conf         # Pacman do build
│   └── profiledef.sh       # Definição do perfil
└── build.sh                # Script de build principal
```

## Licença
MIT — feito com ☕ pelo time Caelum 
