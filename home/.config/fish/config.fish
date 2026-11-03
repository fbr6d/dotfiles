# No "Welcome to fish" message when a shell starts
set -g fish_greeting

if status is-interactive
    starship init fish | source
end

# Default editor for git, yazi, sudoedit and other terminal tools
set -gx EDITOR nvim
set -gx VISUAL nvim
