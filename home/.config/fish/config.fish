# No "Welcome to fish" message when a shell starts
set -g fish_greeting

if status is-interactive
    starship init fish | source
end

# Own commands (reboot-keep, power-confirm, ...): terminals started from the
# desktop don't get ~/.local/bin in PATH otherwise
fish_add_path -g ~/.local/bin

# Default editor for git, yazi, sudoedit and other terminal tools
set -gx EDITOR nvim
set -gx VISUAL nvim
