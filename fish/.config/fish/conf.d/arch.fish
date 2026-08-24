# 1. arch specific paths
set -gx BIZ_PATH $HOME/projects/03_business
set -gx EDU_PATH $HOME/projects/02_education
set -gx PLAY_PATH $HOME/projects/04_playground

fish_add_path $HOME/.platformio/penv/bin

# abbreviations
abbr -a hyperc "nano ~/.config/hypr/hyprland.conf"
abbr -a start_wg "sudo systemctl start wg-quick@wg0"
abbr -a stop_wg "sudo systemctl stop wg-quick@wg0"
