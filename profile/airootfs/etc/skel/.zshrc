# Velaris — ZSH config padrão

# Prompt minimalista com cor
autoload -U colors && colors
PROMPT="%{$fg_bold[cyan]%}%n%{$reset_color%}@%{$fg[blue]%}%m%{$reset_color%} %{$fg_bold[white]%}%~%{$reset_color%} %# "

# Histórico
HISTSIZE=10000
SAVEHIST=10000
HISTFILE=~/.zsh_history
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_SPACE
setopt SHARE_HISTORY

# Autocomplete
autoload -U compinit && compinit
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'

# ── Aliases do sistema ───────────────────────────────────────────────────────
alias ls='ls --color=auto'
alias ll='ls -lah --color=auto'
alias la='ls -A --color=auto'
alias grep='grep --color=auto'
alias ip='ip --color=auto'
alias diff='diff --color=auto'

# ── Aliases Velaris ───────────────────────────────────────────────────────────
alias update='sudo pacman -Syu'
alias install='sudo pacman -S'
alias remove='sudo pacman -Rns'
alias search='pacman -Ss'
alias cleanup='sudo pacman -Sc && sudo pacman -Rns $(pacman -Qdtq) 2>/dev/null; echo "Sistema limpo!"'
alias mirrors='sudo reflector --country Brazil,US --age 12 --protocol https --sort rate --save /etc/pacman.d/mirrorlist && echo "Mirrors atualizados!"'
alias mem='free -h'
alias disk='df -h'
alias ports='ss -tulanp'
alias reload='source ~/.zshrc'

# Fastfetch no terminal interativo
[[ $- == *i* ]] && fastfetch
