#!/bin/bash

function usage () {
  cat << EOF

  NAME

    $(basename $0) – Basic gsods odsx setup

  USAGE:

    $(basename $0) <gigashare dir>

  EXAMPLE:

    $(basename $0) /gigashare

EOF
exit
}

# Validate user gsods
if [[ "$(id -un)" != "gsods" ]]; then
    echo "This script must be run as user gsods"
    exit 1
fi

[[ $# -eq 0 || $1 == "-h" ]] && usage
[[ -z $1 ]] && { echo -e "\nMust provide a directory for gigashare as argument.\n" ; exit 1 ; }
[[ ! -d $1 ]] & { echo -e "\nThe gigashare directory does not exist.\n" ; exit 1 ; }
# Check if the environment variable is set
ENV_CONFIG_PATH="$1/env_config"
echo "ENV_CONFIG_PATH is set to: $ENV_CONFIG_PATH"
[[ ! -d "$ENV_CONFIG_PATH ]] && { echo -e "\nThe gigashare/env_config does not exist.\n" ; exit 1 ; }

# set app.config var
ENV_CONFIG_APP="$ENV_CONFIG_PATH/app.config"

read_property() {
  local prop_name="$1"
  local prop_value

  prop_value=$(grep "^$prop_name=" "$ENV_CONFIG_APP" | awk -F'=' '{print $2}')
  echo "$prop_value"
}

gigashare=$(read_property "app.gigashare.path")
gigawork=$(read_property "app.gigawork.path")
gigalog=$(read_property "app.gigalog.path")
gigapath=$(read_property "app.giga.path")
gigadatapath=$(read_property "app.gigadata.path")
gigainfluxpath=$(read_property "app.gigainfluxdata.path")

# Validate all required path keys are present in app.config
missing_paths=0
for key_var in "app.gigashare.path:$gigashare" "app.gigawork.path:$gigawork" "app.gigalog.path:$gigalog" "app.giga.path:$gigapath" "app.gigadata.path:$gigadatapath" "app.gigainfluxdata.path:$gigainfluxpath"; do
  key="${key_var%%:*}"
  val="${key_var#*:}"
  if [ -z "$val" ]; then
    echo "Error: '$key' is not set in $ENV_CONFIG_APP. All path keys are required."
    missing_paths=1
  fi
done
if [ "$missing_paths" -eq 1 ]; then
  exit 1
fi

## ~/.bashrc

cat >> ~/.bashrc <<EOF

# User specific aliases and functions
[ -f ~/.aliases ] && source ~/.aliases
alias odsx='cd /$app.giga.path/gs-odsx ; ./odsx.py'

GS_HOME=/$app.giga.path/gigaspaces-smart-ods
PATH=$PATH:$HOME/bin:/$app.giga.path/utils/auto_odsx:/$app.giga.path/utils:/opt/maven/bin
export PATH GS_HOME
export PYTHONPATH=/$app.giga.path/gs-odsx
export ODSXARTIFACTS=/$app.gigashare.path/current/
export ENV_CONFIG=/$app.gigashare.path/env_config/

EOF

# generate bash tab-completion code for the Python CLI program odsx.py
echo 'eval "$(register-python-argcomplete odsx.py)"' >> ~/.bashrc

pip3 install -r requirements.txt
