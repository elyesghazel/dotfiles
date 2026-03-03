# 1. arch specific paths
set -gx BIZ_PATH $HOME/projects/03_business
set -gx EDU_PATH $HOME/projects/02_education
set -gx PLAY_PATH $HOME/projects/04_playground

fish_add_path $HOME/.platformio/penv/bin

# abbreviations
abbr -a hyperc "nano ~/.config/hypr/hyprland.conf"
