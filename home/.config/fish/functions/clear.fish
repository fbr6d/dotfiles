# clear also wipes the scrollback: kitty's terminfo has no E3 entry, so the
# plain clear leaves everything above the screen; \e[3J clears it in kitty
function clear --wraps clear --description 'Clear the screen and scrollback'
    command clear $argv
    printf '\e[3J'
end
