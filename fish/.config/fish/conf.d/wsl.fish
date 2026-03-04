# 1. wsl specific paths
set -gx BIZ_PATH $HOME/projects/03_business
set -gx EDU_PATH $HOME/projects/02_education
set -gx PLAY_PATH $HOME/projects/04_playground

# 2. navigation abbreviations
abbr -a cdbiz "cd $BIZ_PATH"
abbr -a cdedu "cd $EDU_PATH"
abbr -a cdplay "cd $PLAY_PATH"

set -e HTTP_PROXY
set -e HTTPS_PROXY
set -e http_proxy
set -e https_proxy
set -e NO_PROXY
set -e no_proxy

