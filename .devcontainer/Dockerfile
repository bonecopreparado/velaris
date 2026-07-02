FROM archlinux:latest

LABEL maintainer="Velaris"
LABEL description="Velaris — Ambiente de build (Arch Linux)"

# Atualiza o sistema e instala dependências de build
RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
        archiso \
        git \
        base-devel \
        wget \
        curl \
        sudo \
        vim \
        neovim \
        zsh \
        bash-completion \
        squashfs-tools \
        libisoburn \
        dosfstools \
        mtools \
        erofs-utils \
        openssl \
        gnupg \
    && pacman -Scc --noconfirm

# Garante que /dev/fuse exista (necessário para squashfs dentro de containers)
RUN mknod /dev/fuse c 10 229 || true

WORKDIR /workspace
