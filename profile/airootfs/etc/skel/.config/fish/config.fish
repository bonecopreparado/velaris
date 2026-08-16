# Velaris — default Fish configuration

set -gx EDITOR kate
set -gx VISUAL kate
set -gx BROWSER firefox
set -gx TERMINAL konsole

if status is-interactive
    set -g fish_greeting

    # Fish provides autosuggestions and syntax highlighting natively.
    set -g fish_color_command cyan
    set -g fish_color_param normal
    set -g fish_color_error brred
    set -g fish_color_autosuggestion brblack

    alias ls='ls --color=auto'
    alias ll='ls -lah --color=auto'
    alias la='ls -A --color=auto'
    alias grep='grep --color=auto'
    alias ip='ip --color=auto'
    alias diff='diff --color=auto'

    abbr --add update 'sudo pacman -Syu'
    abbr --add install 'sudo pacman -S'
    abbr --add remove 'sudo pacman -Rns'
    abbr --add search 'pacman -Ss'
    abbr --add mem 'free -h'
    abbr --add disk 'df -h'
    abbr --add ports 'ss -tulanp'

    # Show system information once per login session, not for every terminal.
    if set -q XDG_RUNTIME_DIR
        set -l fastfetch_marker "$XDG_RUNTIME_DIR/velaris-fastfetch-shown"
        if not test -e "$fastfetch_marker"
            command touch "$fastfetch_marker" 2>/dev/null
            command fastfetch
        end
    end
end

function cleanup --description 'Clean the package cache and remove orphan packages'
    sudo paccache -r
    set -l orphans (pacman -Qdtq)
    if test (count $orphans) -gt 0
        sudo pacman -Rns -- $orphans
    else
        echo 'No orphan packages found.'
    end
end

function mirrors --description 'Select recent and responsive HTTPS mirrors'
    sudo reflector --latest 20 --protocol https --sort rate --save /etc/pacman.d/mirrorlist
end
