# 1. wsl specific paths
set -gx BIZ_PATH $HOME/projects/03_business
set -gx EDU_PATH $HOME/projects/02_education
set -gx PLAY_PATH $HOME/projects/04_playground
set -x NODE_EXTRA_CA_CERTS "/etc/ssl/certs/ca-certificates.crt"
set -x NODE_OPTIONS "--use-openssl-ca"

# 2. navigation abbreviations
abbr -a cdbiz "cd $BIZ_PATH"
abbr -a cdedu "cd $EDU_PATH"
abbr -a cdplay "cd $PLAY_PATH"


nvm use latest
