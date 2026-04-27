#!/bin/bash
# user-setup.sh — Run as the app user on the pivot machine.
# Handles gigashare extraction, giga directory creation, SSH key
# generation + deployment, user environment setup (pivot + remote),
# GigaSpaces installation, and Python dependencies.
#
# Designed to be idempotent — safe to re-run. On the first run (before
# root-setup.sh), remote host steps will be skipped with a warning.
# After root-setup.sh creates remote users and NFS, re-run this script
# to complete remote host configuration and SSH key deployment.
#
# Prerequisites:
#   - App user exists on pivot (root-setup.sh or admin)
#   - Gigashare dir exists and is writable by app user
#
# Typical workflow:
#   1. user-setup.sh -d /gigashare -u gsods -tar /path/gigashare.tgz
#   2. root-setup.sh -d /gigashare       (as root)
#   3. user-setup.sh -d /gigashare -u gsods   (re-run for remote hosts)

# Load shared read_property helper (no-op when piped over SSH; see lib_app_config.sh).
[ -r "$(dirname "$0")/lib_app_config.sh" ] && source "$(dirname "$0")/lib_app_config.sh"

function usage () {
  cat << EOF

  NAME

    $(basename $0) – App user ODSX setup

  USAGE

    $(basename $0) -d <gigashare dir> -u <username> [-tar <gigashare.tgz>] [--overwrite]

  OPTIONS

    -d <dir>      Gigashare directory (e.g. /gigashare)
    -u <user>     App username (e.g. gsods)
    -tar <tgz>    Gigashare tarball to extract into -d (optional; skipped
                  if -d is already populated, unless --overwrite)
    --overwrite   Re-extract tgz, overwrite sqlite files, overwrite SSH config

  EXAMPLES

    # First run — extract tgz and set up pivot:
    ./$(basename $0) -d /gigashare -u gsods -tar /giga/gigashare.tgz

    # After root-setup.sh — complete remote host config:
    ./$(basename $0) -d /gigashare -u gsods

EOF
exit
}

set -e

# --- Parse arguments ---
GIGASHARE_DIR=""
APP_USER=""
TGZ_FILE=""
OVERWRITE=false

# Extract multi-char flags (--overwrite, -tar) before getopts.
# getopts only handles single-letter options, so anything longer
# must be consumed here.
_ARGS=()
_consume_tar=false
for _arg in "$@"; do
    if $_consume_tar; then
        TGZ_FILE=$_arg
        _consume_tar=false
        continue
    fi
    case "$_arg" in
        --overwrite) OVERWRITE=true ;;
        -tar)        _consume_tar=true ;;
        *)           _ARGS+=("$_arg") ;;
    esac
done
$_consume_tar && { echo "Error: -tar requires a path argument." >&2; usage; }
set -- "${_ARGS[@]+"${_ARGS[@]}"}"
unset _ARGS _arg _consume_tar

while getopts ":d:u:h" opt; do
    case $opt in
        d) GIGASHARE_DIR=$OPTARG ;;
        u) APP_USER=$OPTARG ;;
        h) usage ;;
        \?) echo "Unknown option: -$OPTARG" >&2; usage ;;
        :)  echo "Option -$OPTARG requires an argument" >&2; usage ;;
    esac
done

[[ -z "$GIGASHARE_DIR" ]] && { echo "Error: -d <gigashare dir> is required."; usage; }
[[ -z "$APP_USER" ]] && { echo "Error: -u <username> is required."; usage; }
[[ ! -d "$GIGASHARE_DIR" ]] && { echo "Error: $GIGASHARE_DIR does not exist."; exit 1; }

# Validate running as the specified user
if [[ "$(id -un)" != "$APP_USER" ]]; then
    echo "Error: This script must be run as user $APP_USER (currently $(id -un))."
    exit 1
fi

# --- Step 1: Gigashare extraction ---
if [ -n "$TGZ_FILE" ]; then
    echo ">>> Step 1: Gigashare extraction..."
    if [ ! -s "$TGZ_FILE" ]; then
        echo "Error: $TGZ_FILE is empty or does not exist."
        exit 1
    fi
    if [ -z "$(ls -A "$GIGASHARE_DIR" 2>/dev/null)" ]; then
        echo "    Extracting $TGZ_FILE into $GIGASHARE_DIR ..."
        tar xzf "$TGZ_FILE" -C "$GIGASHARE_DIR"
        echo "    Done."
    elif $OVERWRITE; then
        echo "    Overwrite mode: clearing $GIGASHARE_DIR and re-extracting..."
        rm -rf "$GIGASHARE_DIR"/*
        tar xzf "$TGZ_FILE" -C "$GIGASHARE_DIR"
        echo "    Done."
    else
        echo "    $GIGASHARE_DIR is not empty — skipping extraction. Use --overwrite to force."
    fi
else
    echo ">>> Step 1: No -tar given — skipping gigashare extraction."
fi

# --- Config paths ---
ENV_CONFIG_PATH="$GIGASHARE_DIR/env_config"
[[ ! -d "$ENV_CONFIG_PATH" ]] && { echo "Error: $ENV_CONFIG_PATH does not exist. Extract gigashare first (-tar)."; exit 1; }

APP_CONFIG="$ENV_CONFIG_PATH/app.config"
HOST_YAML="$ENV_CONFIG_PATH/host.yaml"
[[ ! -f "$APP_CONFIG" ]] && { echo "Error: $APP_CONFIG not found."; exit 1; }
[[ ! -f "$HOST_YAML" ]] && { echo "Error: $HOST_YAML not found."; exit 1; }


GIGA_PATH=$(read_property "app.giga.path")
GIGA_SHARE=$(read_property "app.gigashare.path")
GIGA_LOG=$(read_property "app.gigalog.path")
GIGA_DATA=$(read_property "app.gigadata.path")
GIGA_WORK=$(read_property "app.gigawork.path")

# Validate required path keys
missing_paths=0
for key_var in "app.giga.path:$GIGA_PATH" "app.gigashare.path:$GIGA_SHARE" "app.gigalog.path:$GIGA_LOG" "app.gigadata.path:$GIGA_DATA" "app.gigawork.path:$GIGA_WORK"; do
    key="${key_var%%:*}"
    val="${key_var#*:}"
    if [ -z "$val" ]; then
        echo "Error: '$key' is not set in $APP_CONFIG."
        missing_paths=1
    fi
done
[[ "$missing_paths" -eq 1 ]] && exit 1

NOFILE_LIMIT=$(read_property "app.user.nofile.limit")
NOFILE_LIMIT=${NOFILE_LIMIT:-50000}

# --- Determine hosts ---
ALL_HOSTS=$(grep -E '^\s+host[0-9]+\s*:' "$HOST_YAML" | awk -F':' '{gsub(/^[[:space:]]+|[[:space:]]+$/,"",$2); if($2!="") print $2}' | sort -u)
PIVOT_IP=$(hostname -I | awk '{print $1}')

REMOTE_HOSTS=""
for _h in $ALL_HOSTS; do
    [ "$_h" != "$PIVOT_IP" ] && REMOTE_HOSTS="$REMOTE_HOSTS $_h"
done
REMOTE_HOSTS="${REMOTE_HOSTS# }"

echo ""
echo "============================================"
echo "  ODSX User Setup ($APP_USER)"
echo "============================================"
echo "Pivot IP:     $PIVOT_IP"
echo "Giga path:    $GIGA_PATH"
echo "Gigashare:    $GIGA_SHARE"
echo "nofile limit: $NOFILE_LIMIT"
echo "Remote hosts: ${REMOTE_HOSTS:-none}"
echo ""

# --- Step 2: Create giga directories ---
echo ">>> Step 2: Creating giga directories..."
mkdir -p $GIGA_PATH $GIGA_SHARE $GIGA_LOG $GIGA_DATA $GIGA_WORK
mkdir -p $GIGA_PATH/bin
touch $GIGA_LOG/odsx.log
echo "    Directories created."

# --- Step 3: SQLite copy ---
echo ">>> Step 3: SQLite files..."
mkdir -p $GIGA_WORK/sqlite
if [ -z "$(ls -A "$GIGA_WORK/sqlite" 2>/dev/null)" ]; then
    if ls $GIGA_SHARE/current/sqlite/* > /dev/null 2>&1; then
        cp $GIGA_SHARE/current/sqlite/* $GIGA_WORK/sqlite/
        echo "    SQLite files copied."
    else
        echo "    No sqlite source files found in $GIGA_SHARE/current/sqlite/ — skipping."
    fi
elif $OVERWRITE; then
    cp $GIGA_SHARE/current/sqlite/* $GIGA_WORK/sqlite/
    echo "    SQLite files overwritten (--overwrite)."
else
    echo "    $GIGA_WORK/sqlite/ is not empty — skipping. Use --overwrite to force."
fi

# --- Step 4: SSH key generation ---
echo ">>> Step 4: SSH key..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh

if [ ! -f ~/.ssh/id_ed25519 ]; then
    ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
    echo "    Key generated."
else
    echo "    Key already exists."
fi

# --- Step 5: SSH config ---
echo ">>> Step 5: SSH config..."
if [ ! -f ~/.ssh/config ] || $OVERWRITE; then
    cat > ~/.ssh/config << 'SSHCONFIG'
Host *
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ConnectTimeout 10
    LogLevel ERROR
SSHCONFIG
    chmod 600 ~/.ssh/config
    if $OVERWRITE; then
        echo "    SSH config overwritten (--overwrite)."
    else
        echo "    SSH config created."
    fi
else
    echo "    SSH config exists — skipping. Use --overwrite to force."
fi

# --- Step 6: SSH key deployment to remote hosts ---
if [ -n "$REMOTE_HOSTS" ]; then
    echo ">>> Step 6: SSH key deployment..."
    PUBKEY=$(cat ~/.ssh/id_ed25519.pub)
    for HOST in $REMOTE_HOSTS; do
        # Test if we can already SSH to this host
        if ssh -o ConnectTimeout=5 -o BatchMode=yes "$HOST" true 2>/dev/null; then
            # Check if key is already deployed
            if ssh -o ConnectTimeout=5 "$HOST" "grep -qF '$PUBKEY' ~/.ssh/authorized_keys 2>/dev/null"; then
                echo "  $HOST — key already deployed."
            else
                ssh -o ConnectTimeout=5 "$HOST" "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$PUBKEY' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
                echo "  $HOST — key deployed."
            fi
        else
            echo "  $HOST — cannot connect (user may not exist yet). Run root-setup.sh first, then re-run this script."
        fi
    done
else
    echo ">>> Step 6: No remote hosts — skipping SSH key deployment."
fi

# --- Step 7: Local directories ---
echo ">>> Step 7: Local directories..."
mkdir -p ~/.config/systemd/user/
echo "    ~/.config/systemd/user/ ready."

# --- Step 8: nofile limits ---
echo ">>> Step 8: nofile limits..."
if ! grep -q "ulimit -Sn" ~/.bashrc 2>/dev/null; then
    echo "ulimit -Sn $NOFILE_LIMIT" >> ~/.bashrc
    echo "    ulimit -Sn $NOFILE_LIMIT added to .bashrc."
else
    echo "    ulimit already in .bashrc."
fi
mkdir -p ~/.config/systemd
cat > ~/.config/systemd/user.conf << EOF
[Manager]
DefaultLimitNOFILE=$NOFILE_LIMIT
EOF
echo "    systemd user.conf set to $NOFILE_LIMIT."

# --- Step 9: .bashrc environment ---
echo ">>> Step 9: .bashrc environment..."

if ! grep -q "export ENV_CONFIG=" ~/.bashrc 2>/dev/null; then
    echo "export ENV_CONFIG=$ENV_CONFIG_PATH" >> ~/.bashrc
    echo "    ENV_CONFIG added."
fi
if ! grep -q "export PYTHONPATH=" ~/.bashrc 2>/dev/null; then
    echo "export PYTHONPATH=$GIGA_PATH/gs-odsx" >> ~/.bashrc
    echo "    PYTHONPATH added."
fi
if ! grep -q "export ODSXARTIFACTS=" ~/.bashrc 2>/dev/null; then
    echo "export ODSXARTIFACTS=$GIGA_SHARE/current/" >> ~/.bashrc
    echo "    ODSXARTIFACTS added."
fi

MY_UID=$(id -u)
if ! grep -q "XDG_RUNTIME_DIR" ~/.bashrc 2>/dev/null; then
    echo "export XDG_RUNTIME_DIR=/run/user/$MY_UID" >> ~/.bashrc
    echo "export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$MY_UID/bus" >> ~/.bashrc
    echo "    XDG_RUNTIME_DIR and DBUS_SESSION_BUS_ADDRESS added."
fi

# Aliases and PATH (pivot only)
if ! grep -q "source ~/.aliases" ~/.bashrc 2>/dev/null; then
    echo '[ -f ~/.aliases ] && source ~/.aliases' >> ~/.bashrc
fi
if ! grep -q "alias odsx=" ~/.bashrc 2>/dev/null; then
    echo "alias odsx='cd $GIGA_PATH/gs-odsx ; ./odsx.py'" >> ~/.bashrc
fi
if ! grep -q "export GS_HOME=" ~/.bashrc 2>/dev/null; then
    echo "export GS_HOME=$GIGA_PATH/gigaspaces-smart-ods" >> ~/.bashrc
fi
if ! grep -q "$GIGA_PATH/utils/auto_odsx" ~/.bashrc 2>/dev/null; then
    echo "export PATH=\$PATH:\$HOME/bin:$GIGA_PATH/utils/auto_odsx:$GIGA_PATH/utils:/opt/maven/bin" >> ~/.bashrc
fi

# Bash tab-completion for odsx.py
if ! grep -q "register-python-argcomplete" ~/.bashrc 2>/dev/null; then
    echo 'eval "$(register-python-argcomplete odsx.py)"' >> ~/.bashrc
fi

echo "    .bashrc configured."

# --- Step 10: Configure remote hosts ---
if [ -n "$REMOTE_HOSTS" ]; then
    echo ">>> Step 10: Configuring remote hosts..."
    REMOTE_FAILED=false
    for HOST in $REMOTE_HOSTS; do
        echo "  --- $HOST ---"
        if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$HOST" true 2>/dev/null; then
            echo "    Cannot connect — skipping. Run root-setup.sh first, then re-run this script."
            REMOTE_FAILED=true
            continue
        fi
        ssh -o ConnectTimeout=10 "$HOST" bash -s \
            "$NOFILE_LIMIT" "$ENV_CONFIG_PATH" "$GIGA_PATH" "$GIGA_LOG" "$GIGA_DATA" "$GIGA_WORK" << 'REMOTE'
set -e
NOFILE_LIMIT=$1
ENV_CONFIG_PATH=$2
GIGA_PATH=$3
GIGA_LOG=$4
GIGA_DATA=$5
GIGA_WORK=$6

# Giga directories
mkdir -p "$GIGA_PATH" "$GIGA_LOG" "$GIGA_DATA" "$GIGA_WORK"
mkdir -p "$GIGA_PATH/bin"

# Systemd user dirs
mkdir -p ~/.config/systemd/user/

# nofile limits
if ! grep -q "ulimit -Sn" ~/.bashrc 2>/dev/null; then
    echo "ulimit -Sn $NOFILE_LIMIT" >> ~/.bashrc
fi
mkdir -p ~/.config/systemd
cat > ~/.config/systemd/user.conf << USERCONF
[Manager]
DefaultLimitNOFILE=$NOFILE_LIMIT
USERCONF

# Env vars
if ! grep -q "export ENV_CONFIG=" ~/.bashrc 2>/dev/null; then
    echo "export ENV_CONFIG=$ENV_CONFIG_PATH" >> ~/.bashrc
fi
if ! grep -q "export PYTHONPATH=" ~/.bashrc 2>/dev/null; then
    echo "export PYTHONPATH=$GIGA_PATH/gs-odsx" >> ~/.bashrc
fi

MY_UID=$(id -u)
if ! grep -q "XDG_RUNTIME_DIR" ~/.bashrc 2>/dev/null; then
    echo "export XDG_RUNTIME_DIR=/run/user/$MY_UID" >> ~/.bashrc
    echo "export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$MY_UID/bus" >> ~/.bashrc
fi

echo "    Done."
REMOTE
    done
    if $REMOTE_FAILED; then
        echo ""
        echo "    Some remote hosts were unreachable. After root-setup.sh, re-run:"
        echo "    ./$(basename "$0") -d $GIGASHARE_DIR -u $APP_USER"
    fi
else
    echo ">>> Step 10: No remote hosts — skipping."
fi
echo ""

# --- Step 11: GigaSpaces installation ---
echo ">>> Step 11: GigaSpaces installation..."

# Check prerequisites
if ! command -v yq &>/dev/null; then
    echo "Error: 'yq' is not installed. Please install yq before running this script."
    exit 1
fi
if ! command -v unzip &>/dev/null; then
    echo "Error: 'unzip' is not installed. Please install unzip before running this script."
    exit 1
fi

# Find latest GigaSpaces zip
shopt -s nullglob
gs_zips=("$GIGA_PATH"/gigaspaces-smart*.zip)
shopt -u nullglob
if [ ${#gs_zips[@]} -eq 0 ]; then
    echo "Error: No gigaspaces-smart*.zip found in $GIGA_PATH. Please stage the GigaSpaces zip before running this script."
    exit 1
fi
latest_zip=$(ls -1t "${gs_zips[@]}" | head -n 1)
zip_basename=$(basename "$latest_zip")
echo "    GigaSpaces zip: $latest_zip"

# Copy to gigashare (idempotent)
mkdir -p "$GIGA_SHARE/current/gs"
if [ ! -f "$GIGA_SHARE/current/gs/$zip_basename" ]; then
    cp "$latest_zip" "$GIGA_SHARE/current/gs/$zip_basename"
    echo "    Copied to $GIGA_SHARE/current/gs/."
else
    echo "    Already in $GIGA_SHARE/current/gs/."
fi

# Unzip (idempotent)
extracted_dir_name="${zip_basename%.zip}"
if [ ! -d "$GIGA_PATH/$extracted_dir_name" ]; then
    (cd "$GIGA_PATH" && unzip -q "$latest_zip")
    echo "    Unzipped to $GIGA_PATH/$extracted_dir_name."
else
    echo "    $GIGA_PATH/$extracted_dir_name already exists."
fi

# Symlink (idempotent)
symlink="$GIGA_PATH/gigaspaces-smart-ods"
if [ "$(readlink "$symlink" 2>/dev/null)" != "$GIGA_PATH/$extracted_dir_name" ]; then
    ln -snf "$GIGA_PATH/$extracted_dir_name" "$symlink"
    echo "    Symlink: $symlink -> $GIGA_PATH/$extracted_dir_name"
else
    echo "    Symlink already correct."
fi

# GS_MANAGER_SERVERS in setenv-overrides.sh (always refresh)
setenv_overrides="$symlink/bin/setenv-overrides.sh"
if [ -f "$HOST_YAML" ] && [ -f "$setenv_overrides" ]; then
    manager_ips=$(yq -r '.servers.manager[]' "$HOST_YAML" 2>/dev/null | paste -sd',' -)
    if [ -n "$manager_ips" ]; then
        sed -i '/^export GS_MANAGER_SERVERS=/d' "$setenv_overrides"
        echo "export GS_MANAGER_SERVERS=$manager_ips" >> "$setenv_overrides"
        echo "    GS_MANAGER_SERVERS=$manager_ips"
    else
        echo "    Warning: No manager IPs in $HOST_YAML — skipping GS_MANAGER_SERVERS."
    fi
else
    echo "    Warning: host.yaml or setenv-overrides.sh not found — skipping GS_MANAGER_SERVERS."
fi

# --- Step 12: Python dependencies ---
echo ">>> Step 12: Python dependencies..."
if ls "$GIGA_SHARE/current/python/"* > /dev/null 2>&1; then
    echo "    Offline packages found — installing from $GIGA_SHARE/current/python"
    pip3 install --no-index --find-links="$GIGA_SHARE/current/python" -r "$GIGA_PATH/gs-odsx/scripts/requirements.txt"
else
    echo "    No offline packages — installing from PyPI"
    pip3 install -r "$GIGA_PATH/gs-odsx/scripts/requirements.txt"
fi

echo ""
echo "============================================"
echo "  User setup complete ($APP_USER)."
echo ""
echo "  Source your updated profile:"
echo "    source ~/.bashrc"
echo ""
echo "  Run ODSX:"
echo "    cd $GIGA_PATH/gs-odsx"
echo "    ./odsx.py"
echo "============================================"
