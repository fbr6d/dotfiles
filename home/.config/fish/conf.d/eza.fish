# ls → eza: colors, Nerd Font icons, folders first (falls back to plain ls if eza is missing)
if status is-interactive; and type -q eza
    alias ls 'eza --icons --group-directories-first'
    # long list: permissions, size (human), date, git status
    alias ll 'eza -l --icons --group-directories-first --git --time-style=long-iso'
    # include hidden files
    alias la 'eza -a --icons --group-directories-first'
    alias lla 'eza -la --icons --group-directories-first --git --time-style=long-iso'
    alias l lla
    # tree view (2 levels; deeper with e.g. lt -L 3)
    alias lt 'eza --tree --level=2 --icons --group-directories-first'
end
