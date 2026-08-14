# Checklist de teste da ISO Velaris

Use sempre uma máquina virtual com **disco virtual vazio**. Não aponte o instalador de teste para um disco que contenha arquivos importantes.

## 1. Preparar a VM

Configuração mínima recomendada para o teste:

- firmware UEFI;
- 2 vCPUs;
- 4 GiB de RAM;
- disco virtual de 30 GiB ou maior;
- rede habilitada;
- controladora gráfica padrão da VM, sem arquivo Xorg forçado.

Faça também uma rodada com 2 GiB de RAM para observar ZRAM e `earlyoom` sob pressão.

## 2. Conferir a sessão live

1. Confirme o autologin do usuário `velaris`.
2. Abra o Calamares pelo ícone e pelo autostart.
3. Confirme que o instalador não abre em branco e que logo, textos e slideshow aparecem.
4. Teste rede, áudio, resolução da tela e bloqueio de sessão.
5. No terminal, confirme que a renderização por software não foi forçada:

   ```bash
   printenv LIBGL_ALWAYS_SOFTWARE
   ```

   O resultado esperado é vazio.

## 3. Instalar

1. Escolha um nome de usuário diferente de `velaris`.
2. Teste primeiro o particionamento automático em um disco virtual vazio.
3. Em uma segunda VM, teste o particionamento manual.
4. Se houver opção de criptografia, faça uma rodada separada com LUKS.
5. Conclua a instalação e reinicie sem a mídia ISO conectada.

## 4. Validar o sistema instalado

Execute os comandos abaixo com o usuário criado no Calamares.

### Identidade live removida

```bash
getent passwd velaris
test ! -e /home/velaris
test ! -e /etc/sddm.conf.d/autologin.conf
test ! -e ~/.config/autostart/calamares.desktop
test ! -e /usr/share/applications/calamares.desktop
```

`getent` não deve imprimir nada e os comandos `test` devem terminar sem saída.

### Privilégios e instalador

```bash
sudo -n true
pacman -Q cachyos-calamares mkinitcpio-archiso syslinux
```

O primeiro comando deve recusar sudo sem senha. O segundo deve informar que os três pacotes exclusivos do live não estão instalados. Depois, confirme que `sudo true` funciona usando a senha do usuário.

### Serviços e boot

```bash
systemctl --failed --no-pager
systemctl is-enabled NetworkManager.service sddm.service ananicy-cpp.service ufw.service
systemctl is-enabled NetworkManager-wait-online.service
plymouth-set-default-theme
test ! -e /var/lib/velaris/firstboot-plymouth
```

Resultados esperados:

- nenhuma unidade em estado `failed`;
- os quatro serviços principais habilitados;
- `NetworkManager-wait-online` desabilitado;
- tema Plymouth igual a `velaris`;
- marcador do primeiro boot removido.

Reinicie uma segunda vez para garantir que o initramfs restaurado inicia normalmente.

### Memória e desempenho

```bash
swapon --show
sysctl vm.swappiness vm.page-cluster vm.dirty_bytes vm.dirty_background_bytes
systemctl status ananicy-cpp.service earlyoom.service --no-pager
```

Confirme a presença de ZRAM, `swappiness = 100`, `page-cluster = 0` e os dois serviços sem falhas.

### KDE e gráficos

1. Entre na sessão Plasma Wayland e confirme painel, bloqueio, suspensão, áudio e navegador.
2. Saia da sessão, selecione Plasma X11 no SDDM e entre novamente.
3. Confirme que `printenv LIBGL_ALWAYS_SOFTWARE` continua vazio nas duas sessões.
4. Se possível, repita em uma VM diferente para cobrir outro driver virtual.

## 5. Informações para um relatório de falha

Anexe ao issue:

```bash
fastfetch
systemctl --failed --no-pager
journalctl -b -p warning..alert --no-pager
```

Para falhas do instalador, copie também `/root/.cache/calamares/session.log` ainda na sessão live, antes de reiniciar.
