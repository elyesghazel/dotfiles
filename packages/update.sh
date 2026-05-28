#!/bin/bash

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACMAN_LIST="$DOTFILES/packages/pacman.txt"
AUR_LIST="$DOTFILES/packages/aur.txt"

_require_pacman() {
    if ! command -v pacman &> /dev/null; then
        echo "pacman not found (WSL/non-Arch). Skipping."
        exit 0
    fi
}

cmd_update() {
    _require_pacman
    pacman -Qqen > "$PACMAN_LIST"
    pacman -Qqem > "$AUR_LIST"
    echo "Package lists updated:"
    printf "  Official  %d packages → packages/pacman.txt\n" "$(wc -l < "$PACMAN_LIST")"
    printf "  AUR       %d packages → packages/aur.txt\n"    "$(wc -l < "$AUR_LIST")"
}

cmd_list() {
    printf "── Official (%d) ─────────────────────────────────────────\n" "$(wc -l < "$PACMAN_LIST")"
    paste - - - - < "$PACMAN_LIST" | column -t -s $'\t'
    printf "\n── AUR (%d) ──────────────────────────────────────────────\n" "$(wc -l < "$AUR_LIST")"
    paste - - - - < "$AUR_LIST" | column -t -s $'\t'
}

cmd_diff() {
    _require_pacman
    echo "── In system but NOT in lists ──"
    echo "  Official:"
    comm -23 <(pacman -Qqen | sort) <(sort "$PACMAN_LIST") | sed 's/^/    /'
    echo "  AUR:"
    comm -23 <(pacman -Qqem | sort) <(sort "$AUR_LIST") | sed 's/^/    /'
    echo "── In lists but NOT installed ──"
    echo "  Official:"
    comm -13 <(pacman -Qqen | sort) <(sort "$PACMAN_LIST") | sed 's/^/    /'
    echo "  AUR:"
    comm -13 <(pacman -Qqem | sort) <(sort "$AUR_LIST") | sed 's/^/    /'
}

case "${1:-help}" in
    update) cmd_update ;;
    list)   cmd_list   ;;
    diff)   cmd_diff   ;;
    *)
        echo "Usage: packages/update.sh <command>"
        echo ""
        echo "Commands:"
        echo "  update   Export currently installed packages to lists"
        echo "  list     Show all packages in the lists (columnar)"
        echo "  diff     Show differences between system and lists"
        ;;
esac
