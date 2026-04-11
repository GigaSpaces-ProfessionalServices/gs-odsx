#!/bin/bash

function usage () {
  cat << EOF

  NAME

    ./$(basename $0) – Basic gsods odsx setup

  USAGE:

    ./$(basename $0) <gigashare dir>

  EXAMPLE:

    ./$(basename $0) /gigashare

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

## GigaSpaces Installation

# Check prerequisites
if ! command -v yq &>/dev/null; then
    echo "Error: 'yq' is not installed. Please install yq before running this script."
    exit 1
fi
if ! command -v unzip &>/dev/null; then
    echo "Error: 'unzip' is not installed. Please install unzip before running this script."
    exit 1
fi

# Step 1: Find latest GigaSpaces zip in gigapath
shopt -s nullglob
gs_zips=("$gigapath"/gigaspaces-smart*.zip)
shopt -u nullglob
if [ ${#gs_zips[@]} -eq 0 ]; then
    echo "Error: No gigaspaces-smart*.zip found in $gigapath. Please stage the GigaSpaces zip before running this script."
    exit 1
fi
# Pick the latest by modification time
latest_zip=$(ls -1t "${gs_zips[@]}" | head -n 1)
zip_basename=$(basename "$latest_zip")
echo "GigaSpaces zip: $latest_zip"

# Step 2: Copy zip to gigashare (idempotent)
mkdir -p "$gigashare/current/gs"
if [ ! -f "$gigashare/current/gs/$zip_basename" ]; then
    echo "Copying $zip_basename to $gigashare/current/gs/ ..."
    cp "$latest_zip" "$gigashare/current/gs/$zip_basename"
    echo "    Copied."
else
    echo "    $zip_basename already present in $gigashare/current/gs/, skipping copy."
fi

# Step 3: Unzip into gigapath (idempotent — derive extracted dir name from zip)
# Strip the .zip suffix to get expected dir name
extracted_dir_name="${zip_basename%.zip}"
if [ ! -d "$gigapath/$extracted_dir_name" ]; then
    echo "Unzipping $zip_basename into $gigapath ..."
    (cd "$gigapath" && unzip -q "$latest_zip")
    echo "    Unzipped to $gigapath/$extracted_dir_name."
else
    echo "    $gigapath/$extracted_dir_name already exists, skipping unzip."
fi

# Step 4: Create/update symlink gigaspaces-smart-ods -> extracted dir (idempotent)
symlink="$gigapath/gigaspaces-smart-ods"
if [ "$(readlink "$symlink" 2>/dev/null)" != "$gigapath/$extracted_dir_name" ]; then
    ln -snf "$gigapath/$extracted_dir_name" "$symlink"
    echo "Symlink: $symlink -> $gigapath/$extracted_dir_name"
else
    echo "    Symlink $symlink already correct, skipping."
fi

# Step 5: Set GS_MANAGER_SERVERS in setenv-overrides.sh from host.yaml (idempotent)
host_yaml="$ENV_CONFIG_PATH/host.yaml"
setenv_overrides="$symlink/bin/setenv-overrides.sh"

if [ ! -f "$host_yaml" ]; then
    echo "Warning: $host_yaml not found — skipping GS_MANAGER_SERVERS update."
elif [ ! -f "$setenv_overrides" ]; then
    echo "Warning: $setenv_overrides not found — skipping GS_MANAGER_SERVERS update."
else
    manager_ips=$(yq -r '.servers.manager[]' "$host_yaml" 2>/dev/null | paste -sd',' -)
    if [ -z "$manager_ips" ]; then
        echo "Warning: No manager IPs found in $host_yaml — skipping GS_MANAGER_SERVERS update."
    else
        # Remove all existing GS_MANAGER_SERVERS lines then append the current value
        sed -i '/^export GS_MANAGER_SERVERS=/d' "$setenv_overrides"
        echo "export GS_MANAGER_SERVERS=$manager_ips" >> "$setenv_overrides"
        echo "GS_MANAGER_SERVERS set to $manager_ips in $setenv_overrides"
    fi
fi

## Python dependencies

if ls $gigashare/current/python/* > /dev/null 2>&1; then
    echo "Offline packages found — installing from $gigashare/current/python"
    pip3 install --no-index --find-links=$gigashare/current/python -r $gigapath/gs-odsx/scripts/requirements.txt
else
    echo "No offline packages found — installing from PyPI"
    pip3 install -r $gigapath/gs-odsx/scripts/requirements.txt
fi
