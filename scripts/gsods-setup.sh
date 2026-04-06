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
[[ ! -d $1 ]] && { echo -e "\nThe gigashare directory does not exist.\n" ; exit 1 ; }

# Check if the environment variable is set
ENV_CONFIG_PATH="$1/env_config"
echo "ENV_CONFIG_PATH is set to: $ENV_CONFIG_PATH"
[[ ! -d "$ENV_CONFIG_PATH" ]] && { echo -e "\nThe gigashare/env_config does not exist.\n" ; exit 1 ; }

# set app.config var
ENV_CONFIG_APP="$ENV_CONFIG_PATH/app.config"

if [ ! -f "$ENV_CONFIG_APP" ]; then
    echo "Error: $ENV_CONFIG_APP not found."
    exit 1
fi

read_property() {
  local prop_name="$1"
  local prop_value

  prop_value=$(grep "^$prop_name=" "$ENV_CONFIG_APP" | awk -F'=' '{print $2}')
  echo "$prop_value"
}

gigapath=$(read_property "app.giga.path")
gigashare=$(read_property "app.gigashare.path")

# Validate required path keys are present in app.config
missing_paths=0
for key_var in "app.giga.path:$gigapath" "app.gigashare.path:$gigashare"; do
  key="${key_var%%:*}"
  val="${key_var#*:}"
  if [ -z "$val" ]; then
    echo "Error: '$key' is not set in $ENV_CONFIG_APP."
    missing_paths=1
  fi
done
if [ "$missing_paths" -eq 1 ]; then
  exit 1
fi

## ~/.bashrc — append each item only if not already present

if ! grep -q "source ~/.aliases" ~/.bashrc 2>/dev/null; then
    echo '[ -f ~/.aliases ] && source ~/.aliases' >> ~/.bashrc
fi

if ! grep -q "alias odsx=" ~/.bashrc 2>/dev/null; then
    echo "alias odsx='cd $gigapath/gs-odsx ; ./odsx.py'" >> ~/.bashrc
fi

if ! grep -q "export GS_HOME=" ~/.bashrc 2>/dev/null; then
    echo "export GS_HOME=$gigapath/gigaspaces-smart-ods" >> ~/.bashrc
fi

if ! grep -q "$gigapath/utils/auto_odsx" ~/.bashrc 2>/dev/null; then
    echo "export PATH=\$PATH:\$HOME/bin:$gigapath/utils/auto_odsx:$gigapath/utils:/opt/maven/bin" >> ~/.bashrc
fi

if ! grep -q "export PYTHONPATH=" ~/.bashrc 2>/dev/null; then
    echo "export PYTHONPATH=$gigapath/gs-odsx" >> ~/.bashrc
fi

if ! grep -q "export ODSXARTIFACTS=" ~/.bashrc 2>/dev/null; then
    echo "export ODSXARTIFACTS=$gigashare/current/" >> ~/.bashrc
fi

if ! grep -q "export ENV_CONFIG=" ~/.bashrc 2>/dev/null; then
    echo "export ENV_CONFIG=$ENV_CONFIG_PATH" >> ~/.bashrc
fi

# generate bash tab-completion code for the Python CLI program odsx.py
if ! grep -q "register-python-argcomplete" ~/.bashrc 2>/dev/null; then
    echo 'eval "$(register-python-argcomplete odsx.py)"' >> ~/.bashrc
fi

pip3 install -r $gigapath/gs-odsx/requirements.txt
