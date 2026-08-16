# Velaris — estado do projeto

Atualizado em 15 de agosto de 2026.

## Resumo

A Velaris é uma distribuição Arch Linux para x86-64 com KDE Plasma 6, kernel `linux-cachyos`, SDDM, PipeWire e Calamares. O objetivo técnico é equilibrar três pontos: inicialização e resposta rápidas, estabilidade em hardware variado e uma instalação que não carregue resíduos da sessão live.

## Estado desta revisão

| Área | Alteração | Resultado esperado |
|---|---|---|
| Calamares | Instâncias e arquivos `*_velaris.conf` próprios | Evita colisões com configurações pertencentes ao pacote `cachyos-calamares` |
| Slideshow | Layout responsivo, wallpaper existente e ciclo de vida da API 2 | Evita tela vazia durante a instalação e mantém a identidade visual |
| Sistema instalado | `unpackfs` com exclusões, `removeuser` e limpeza obrigatória | Remove conta live, autologin, sudo sem senha, regra Polkit, instalador e pacotes exclusivos do live |
| Polkit live | Ação e caminho exatos do Calamares, limitados ao usuário local ativo | O instalador abre elevado sem liberar outros programas via `pkexec` |
| Usuário | Root bloqueado, senha mínima de 8 caracteres e home `0700` | Padrão mais seguro sem impedir administração via sudo |
| Boot | GRUB explícito, fallback UEFI e configuração própria | Evita herdar o bootloader padrão de outra distribuição |
| Initramfs live | Hooks atuais de microcode, KMS, Plymouth e Archiso, sem lista fixa de GPUs | Boot gráfico mais compatível e menos módulos forçados |
| Plymouth | Tema especial apenas no primeiro boot | Depois do primeiro início, o tema normal é restaurado e o initramfs é reconstruído |
| Gráficos | Remoção de variáveis globais e do Xorg que desativava aceleração | Mesa, Xorg e o compositor escolhem o caminho correto para cada GPU |
| Memória | ZRAM com `swappiness=100`, `page-cluster=0`, `earlyoom` e writeback absoluto | Melhor resposta sob pressão sem overcommit agressivo |
| Memória comprimida | `zswap.enabled=0` em todas as rotas de boot e `systemd-oomd` desativado | Evita compressão e políticas de OOM duplicadas |
| Processos | Ananicy C++ acompanhado das regras CachyOS | O daemon possui regras reais para aplicar |
| Shell | Fish como padrão e Fastfetch uma vez por sessão | Sugestões e realce nativos sem hooks Zsh executados a cada tecla |
| Impressão | `cups.socket` no lugar de `cups.service` permanente | O daemon só inicia quando há trabalho de impressão |
| Armazenamento | Btrfs com `compress=zstd:1`, `fstrim.timer` e `paccache.timer` | Menor uso de disco e manutenção periódica sem descarte síncrono |
| Rede | NetworkManager com `wpa_supplicant`; espera online desativada | Menos serviços concorrentes e boot mais direto |
| Internacionalização | Live em inglês, teclado US, UTC e mirrors globais | Padrão adequado a usuários internacionais e ajustável no Calamares |
| Repositórios | Assinaturas obrigatórias e mirrorlist oficial do CachyOS | Evita configuração insegura ou lista local envelhecida |
| Sessão | `plasma-x11-session` incluído | Wayland continua padrão, com X11 disponível para compatibilidade |
| Imagem | SquashFS Zstd nível 15 | Leitura e instalação mais rápidas, aceitando uma ISO possivelmente maior |
| CI | Runner self-hosted `lenovo-server`, Linux x86-64, dentro de contêiner Arch | Usa a máquina Oracle para o build e bloqueia execução de código vindo de forks |

## Validação já automatizada

`scripts/validate-profile.py` verifica:

- sintaxe YAML dos arquivos do Calamares;
- existência dos recursos de branding e ciclo de vida do slideshow;
- existência e referências das instâncias `module@id`;
- ordem de remoção da conta live e criação do usuário final;
- exclusão de autologin, sudo, Polkit e arquivos do instalador;
- pacotes obrigatórios, duplicatas e pilhas de rede concorrentes;
- ausência de renderização por software forçada e `TrustAll`;
- ajustes de ZRAM, writeback, GRUB, initramfs live e primeiro boot;
- Fish, ativação do CUPS por socket, política única de OOM e compressão Btrfs;
- locale inglês, teclado US, UTC, URLs da organização e mirrors globais;
- sintaxe Bash e formato de `iso_name`.

O GitHub Actions executa essa validação antes de chamar `mkarchiso`.

O job também confirma que está executando no runner chamado exatamente `lenovo-server` e limpa os diretórios grandes ao final, inclusive quando uma etapa falha.

## Pendente para considerar a correção comprovada

A validação estática não substitui uma instalação completa. Ainda é obrigatório:

1. gerar a ISO no GitHub Actions ou em um host Arch Linux;
2. inicializar a ISO em uma VM UEFI com disco virtual vazio;
3. executar o Calamares, incluindo um teste de particionamento automático;
4. reiniciar duas vezes e executar o checklist de `docs/TESTING.md`;
5. guardar o log do Calamares e o resultado de `systemctl --failed` se algo falhar.

Até esse teste passar, o estado correto é **corrigido e validado estaticamente, aguardando prova de instalação em VM**.
