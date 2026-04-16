#!/bin/bash
# setup-nonroot.sh - Run as root on the pivot machine.
# Prepares the filesystem, gsods user on pivot, and all remote servers
# for non-root ODSX operation. Reads config from gigashare/env_config/app.config
# and server IPs from host.yaml.

function usage () {
  cat << EOF

  NAME

    $(basename $0) – ODSX one-time root setup

  USAGE:

    $(basename $0) <gigashare dir> <gigashare.tgz> [--overwrite]

  OPTIONS:

    --overwrite   Re-extract gigashare.tgz even if gigashare dir is not empty,
                  overwrite sqlite files, and overwrite gsods SSH config.

  EXAMPLE:

    ./$(basename $0) /gigashare /giga/gigashare.tgz
    ./$(basename $0) /gigashare /giga/gigashare.tgz --overwrite

EOF
exit
}

set -e

# Parse --overwrite flag (accepted in any position)
OVERWRITE=false
_ARGS=()
for _arg in "$@"; do
    if [ "$_arg" = "--overwrite" ]; then
        OVERWRITE=true
    else
        _ARGS+=("$_arg")
    fi
done
set -- "${_ARGS[@]}"
unset _ARGS _arg

# Must run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root."
    exit 1
fi

[[ $# -eq 0 || $1 == "-h" ]] && usage
[[ -z $1 ]] && { echo -e "\nMust provide a directory for gigashare as argument.\n" ; exit 1 ; }
[[ ! -d $1 ]] && { echo -e "\nThe gigashare directory does not exist.\n" ; exit 1 ; }
[[ ! -s $2 ]] && { echo -e "\nThe gigashare.tgz is empty or does not exist.\n" ; exit 1 ; }

if [ -z "$(ls -A "$1" 2>/dev/null)" ]; then
    echo "Extracting gigashare..."
    tar xzf "$2" -C "$1"
elif $OVERWRITE; then
    echo "Overwrite mode: emptying $1 and re-extracting..."
    rm -rf "$1"/*
    tar xzf "$2" -C "$1"
else
    echo "$1 is not empty — skipping extraction. Use --overwrite to force re-extraction."
fi

ENV_CONFIG_PATH="$1/env_config"
echo "ENV_CONFIG_PATH is set to: $ENV_CONFIG_PATH"
[[ ! -d "$ENV_CONFIG_PATH" ]] && { echo -e "\nThe gigashare/env_config does not exist.\n" ; exit 1 ; }

APP_CONFIG="$ENV_CONFIG_PATH/app.config"
HOST_YAML="$ENV_CONFIG_PATH/host.yaml"

if [ ! -f "$APP_CONFIG" ]; then
    echo "Error: $APP_CONFIG not found."
    exit 1
fi

if [ ! -f "$HOST_YAML" ]; then
    echo "Error: $HOST_YAML not found."
    exit 1
fi

read_property() {
    local prop_name="$1"
    grep "^$prop_name=" "$APP_CONFIG" | awk -F'=' '{print $2}'
}

# Read all required path variables from app.config
GIGA_PATH=$(read_property "app.giga.path")
GIGA_SHARE=$(read_property "app.gigashare.path")
GIGA_WORK=$(read_property "app.gigawork.path")
GIGA_LOG=$(read_property "app.gigalog.path")
GIGA_DATA=$(read_property "app.gigadata.path")
GIGA_INFLUX=$(read_property "app.gigainfluxdata.path")

# Validate all required path keys are present in app.config
missing_paths=0
for key_var in "app.giga.path:$GIGA_PATH" "app.gigashare.path:$GIGA_SHARE" "app.gigawork.path:$GIGA_WORK" "app.gigalog.path:$GIGA_LOG" "app.gigadata.path:$GIGA_DATA" "app.gigainfluxdata.path:$GIGA_INFLUX"; do
  key="${key_var%%:*}"
  val="${key_var#*:}"
  if [ -z "$val" ]; then
    echo "Error: '$key' is not set in $APP_CONFIG. All path keys are required."
    missing_paths=1
  fi
done
if [ "$missing_paths" -eq 1 ]; then
  exit 1
fi

NOFILE_LIMIT=$(read_property "app.user.nofile.limit")
NOFILE_LIMIT=${NOFILE_LIMIT:-50000}

# Read remote hosts from host.yaml
ALL_HOSTS=$(grep -E '^\s+host[0-9]+\s*:' "$HOST_YAML" | awk -F':' '{gsub(/^[[:space:]]+|[[:space:]]+$/,"",$2); if($2!="") print $2}' | sort -u)
PIVOT_IP=$(hostname -I | awk '{print $1}')

# Non-pivot hosts only (NFS clients)
REMOTE_HOSTS=""
for _h in $ALL_HOSTS; do
    [ "$_h" != "$PIVOT_IP" ] && REMOTE_HOSTS="$REMOTE_HOSTS $_h"
done
REMOTE_HOSTS="${REMOTE_HOSTS# }"

echo "============================================"
echo "  ODSX Non-Root Setup"
echo "============================================"
echo "Pivot IP:  $PIVOT_IP"
echo "Giga dirs: $GIGA_PATH | $GIGA_SHARE | $GIGA_WORK | $GIGA_LOG | $GIGA_DATA | $GIGA_INFLUX"
echo "Remote hosts:"
for h in $ALL_HOSTS; do
    echo "  $h"
done
echo ""

# Ensure gsods user exists on pivot
if ! id "gsods" >/dev/null 2>&1; then
    useradd -m gsods
    echo "Created gsods user."
fi
GSODS_HOME=$(eval echo ~gsods)

# --- Create giga directories and set ownership ---
# $GIGA_INFLUX is intentionally NOT created here. It belongs to the influxdb
# system user (not gsods) and is created + chowned by influxdbctl.sh -i on
# whichever host runs the influxdb daemon. Pre-creating it here would leave
# an empty dir on every host and would be immediately clobbered by
# influxdbctl.sh's `chown -R influxdb:influxdb $dir` anyway.
echo ">>> Creating giga directories..."
mkdir -p $GIGA_LOG $GIGA_SHARE $GIGA_WORK $GIGA_PATH $GIGA_DATA
touch $GIGA_LOG/odsx.log

mkdir -p $GIGA_WORK/sqlite
if [ -z "$(ls -A "$GIGA_WORK/sqlite" 2>/dev/null)" ]; then
    cp $GIGA_SHARE/current/sqlite/* $GIGA_WORK/sqlite/
    echo "    SQLite files copied."
elif $OVERWRITE; then
    cp $GIGA_SHARE/current/sqlite/* $GIGA_WORK/sqlite/
    echo "    SQLite files overwritten (--overwrite)."
else
    echo "    $GIGA_WORK/sqlite/ is not empty — skipping sqlite copy. Use --overwrite to force."
fi

chown -R gsods:gsods $GIGA_PATH $GIGA_DATA $GIGA_LOG $GIGA_WORK $GIGA_SHARE
echo "    Directories created and ownership set."

# --- Step 1: Generate SSH key for gsods on pivot ---
echo ">>> Step 1: Generating SSH key for gsods on pivot..."
if [ ! -f "$GSODS_HOME/.ssh/id_ed25519" ]; then
    su - gsods -c 'ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519' 2>/dev/null
    echo "    Key generated."
else
    echo "    Key already exists, skipping."
fi

GSODS_PUBKEY=$(cat "$GSODS_HOME/.ssh/id_ed25519.pub")

# Create SSH config for gsods
if [ ! -f "$GSODS_HOME/.ssh/config" ] || $OVERWRITE; then
    install -m 600 -o gsods -g gsods /dev/null "$GSODS_HOME/.ssh/config"
    cat > "$GSODS_HOME/.ssh/config" << 'SSHCONFIG'
Host *
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ConnectTimeout 10
    LogLevel ERROR
SSHCONFIG
    if $OVERWRITE; then
        echo "    SSH config overwritten (--overwrite)."
    else
        echo "    SSH config created."
    fi
else
    echo "    SSH config already exists — skipping. Use --overwrite to force."
fi

# --- Step 2: Configure pivot ---
echo ">>> Step 2: Configuring pivot..."

# Enable linger
loginctl enable-linger gsods 2>/dev/null && echo "    Linger enabled." || echo "    Linger already enabled or not supported."

# Create user systemd dir
mkdir -p "$GSODS_HOME/.config/systemd/user/"
chown -R gsods:gsods "$GSODS_HOME/.config/"
echo "    User systemd directory ready."

# Create giga/bin for start/stop scripts
mkdir -p "$GIGA_PATH/bin"
chown gsods:gsods "$GIGA_PATH/bin"
echo "    $GIGA_PATH/bin ready."

# Set nofile limits (gsods-specific pattern to avoid touching other users)
sed -i '/gsods.*hard.*nofile/d' /etc/security/limits.conf
sed -i '/gsods.*soft.*nofile/d' /etc/security/limits.conf
echo "gsods hard nofile $NOFILE_LIMIT" >> /etc/security/limits.conf
echo "gsods soft nofile $NOFILE_LIMIT" >> /etc/security/limits.conf
echo "    nofile limits set to $NOFILE_LIMIT."

# Sudoers for third-party monitoring services (Grafana, InfluxDB, Telegraf)
cat > /etc/sudoers.d/odsx-monitoring << 'SUDOERS'
gsods ALL=(ALL) NOPASSWD: /bin/systemctl start grafana-server.service, /bin/systemctl stop grafana-server.service, /bin/systemctl restart grafana-server.service, /bin/systemctl status grafana-server.service, /bin/systemctl enable grafana-server.service
gsods ALL=(ALL) NOPASSWD: /bin/systemctl start influxdb.service, /bin/systemctl stop influxdb.service, /bin/systemctl restart influxdb.service, /bin/systemctl status influxdb.service, /bin/systemctl enable influxdb.service
gsods ALL=(ALL) NOPASSWD: /bin/systemctl start telegraf.service, /bin/systemctl stop telegraf.service, /bin/systemctl restart telegraf.service, /bin/systemctl status telegraf.service, /bin/systemctl enable telegraf.service
SUDOERS
chmod 0440 /etc/sudoers.d/odsx-monitoring
echo "    Sudoers for monitoring services configured."

# Set env vars in gsods .bashrc on pivot (idempotent)
if ! grep -q "export ENV_CONFIG=" "$GSODS_HOME/.bashrc" 2>/dev/null; then
    echo "export ENV_CONFIG=$ENV_CONFIG_PATH" >> "$GSODS_HOME/.bashrc"
    echo "    ENV_CONFIG added to gsods .bashrc."
fi
if ! grep -q "export PYTHONPATH=" "$GSODS_HOME/.bashrc" 2>/dev/null; then
    echo "export PYTHONPATH=$GIGA_PATH/gs-odsx" >> "$GSODS_HOME/.bashrc"
    echo "    PYTHONPATH added to gsods .bashrc."
fi
if ! grep -q "export ODSXARTIFACTS=" "$GSODS_HOME/.bashrc" 2>/dev/null; then
    echo "export ODSXARTIFACTS=$GIGA_SHARE/current/" >> "$GSODS_HOME/.bashrc"
    echo "    ODSXARTIFACTS added to gsods .bashrc."
fi
GSODS_UID=$(id -u gsods)
if ! grep -q "XDG_RUNTIME_DIR" "$GSODS_HOME/.bashrc" 2>/dev/null; then
    echo "export XDG_RUNTIME_DIR=/run/user/$GSODS_UID" >> "$GSODS_HOME/.bashrc"
    echo "export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$GSODS_UID/bus" >> "$GSODS_HOME/.bashrc"
    echo "    XDG_RUNTIME_DIR and DBUS_SESSION_BUS_ADDRESS added to gsods .bashrc."
fi
chown gsods:gsods "$GSODS_HOME/.bashrc"

# Set env vars in root's .bashrc on pivot (idempotent)
# So root can run standalone helper scripts (e.g. influxdbctl.sh) that
# read $ENV_CONFIG and $ODSXARTIFACTS without re-exporting them by hand.
ROOT_BASHRC="/root/.bashrc"
if ! grep -q "export ENV_CONFIG=" "$ROOT_BASHRC" 2>/dev/null; then
    echo "export ENV_CONFIG=$ENV_CONFIG_PATH" >> "$ROOT_BASHRC"
    echo "    ENV_CONFIG added to root .bashrc."
fi
if ! grep -q "export PYTHONPATH=" "$ROOT_BASHRC" 2>/dev/null; then
    echo "export PYTHONPATH=$GIGA_PATH/gs-odsx" >> "$ROOT_BASHRC"
    echo "    PYTHONPATH added to root .bashrc."
fi
if ! grep -q "export ODSXARTIFACTS=" "$ROOT_BASHRC" 2>/dev/null; then
    echo "export ODSXARTIFACTS=$GIGA_SHARE/current/" >> "$ROOT_BASHRC"
    echo "    ODSXARTIFACTS added to root .bashrc."
fi

echo "    Pivot configured."
echo ""

# --- Step 3: Set up NFS server on pivot ---
echo ">>> Step 3: Setting up NFS server on pivot..."

if ! rpm -q nfs-utils &>/dev/null; then
    yum install -y nfs-utils
    echo "    nfs-utils installed."
fi

# Add per-host export entries (idempotent)
for HOST in $REMOTE_HOSTS; do
    if ! grep -qF "$GIGA_SHARE $HOST(" /etc/exports 2>/dev/null; then
        echo "$GIGA_SHARE $HOST(rw,sync,no_root_squash,no_subtree_check)" >> /etc/exports
        echo "    Export added for $HOST."
    else
        echo "    Export for $HOST already present."
    fi
done

systemctl enable --now nfs-server
exportfs -ra
echo "    NFS server configured and exports refreshed."
echo ""

# --- Step 4: Configure each remote host ---
echo ">>> Step 4: Configuring remote hosts..."

for HOST in $REMOTE_HOSTS; do
    echo "  --- $HOST ---"

    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "$HOST" bash <<REMOTE_SCRIPT
        set -e

        # Ensure gsods user exists
        if ! id gsods &>/dev/null; then
            useradd gsods
            echo "    Created gsods user."
        fi

        GSODS_HOME=\$(eval echo ~gsods)

        # Set up SSH authorized_keys
        mkdir -p "\$GSODS_HOME/.ssh"
        chmod 700 "\$GSODS_HOME/.ssh"
        if ! grep -qF "$GSODS_PUBKEY" "\$GSODS_HOME/.ssh/authorized_keys" 2>/dev/null; then
            echo "$GSODS_PUBKEY" >> "\$GSODS_HOME/.ssh/authorized_keys"
            echo "    SSH key added."
        else
            echo "    SSH key already present."
        fi
        chmod 600 "\$GSODS_HOME/.ssh/authorized_keys"
        chown -R gsods:gsods "\$GSODS_HOME/.ssh"

        # Enable linger
        loginctl enable-linger gsods 2>/dev/null || true

        # Create user systemd dir
        mkdir -p "\$GSODS_HOME/.config/systemd/user/"
        chown -R gsods:gsods "\$GSODS_HOME/.config/"

        # Create giga directories and set ownership. -R on the local dirs heals
        # any pre-existing cruft (e.g. legacy /gigawork/sqlite files left over
        # from an older setup flow) so gsods can rm them later. $GIGA_SHARE is
        # chowned non-recursively because it becomes an NFS mount a few lines
        # down — recursing into it would try to chown the pivot-owned export.
        # $GIGA_INFLUX is not created on remote hosts — it belongs only on the
        # influxdb host and is provisioned by influxdbctl.sh.
        mkdir -p $GIGA_PATH $GIGA_DATA $GIGA_LOG $GIGA_WORK $GIGA_SHARE
        mkdir -p $GIGA_PATH/bin
        chown -R gsods:gsods $GIGA_PATH $GIGA_DATA $GIGA_LOG $GIGA_WORK
        chown gsods:gsods $GIGA_SHARE

        # Set up NFS client for gigashare
        if ! rpm -q nfs-utils &>/dev/null; then
            yum install -y nfs-utils 2>/dev/null || apt-get install -y nfs-common 2>/dev/null || true
            echo "    nfs-utils installed."
        fi

        # Add fstab entry (idempotent)
        # users: any user can mount/unmount without sudo
        if ! grep -qF "$PIVOT_IP:$GIGA_SHARE" /etc/fstab 2>/dev/null; then
            echo "$PIVOT_IP:$GIGA_SHARE  $GIGA_SHARE  nfs  defaults,_netdev,users  0  0" >> /etc/fstab
            echo "    fstab entry added."
        else
            echo "    fstab entry already present."
        fi

        # Mount if not already mounted
        if ! findmnt "$GIGA_SHARE" > /dev/null 2>&1; then
            mount "$GIGA_SHARE" && echo "    $GIGA_SHARE mounted." || echo "    WARNING: Failed to mount $GIGA_SHARE"
        else
            echo "    $GIGA_SHARE already mounted."
        fi

        # Verify mount
        if findmnt "$GIGA_SHARE" > /dev/null 2>&1; then
            echo "    Mount verified: $GIGA_SHARE is mounted."
        else
            echo "    WARNING: $GIGA_SHARE is NOT mounted after mount attempt."
        fi

        # Set nofile limits
        sed -i '/gsods.*hard.*nofile/d' /etc/security/limits.conf
        sed -i '/gsods.*soft.*nofile/d' /etc/security/limits.conf
        echo "gsods hard nofile $NOFILE_LIMIT" >> /etc/security/limits.conf
        echo "gsods soft nofile $NOFILE_LIMIT" >> /etc/security/limits.conf

        # Set env vars in gsods .bashrc (idempotent)
        if ! grep -q "export ENV_CONFIG=" "\$GSODS_HOME/.bashrc" 2>/dev/null; then
            echo "export ENV_CONFIG=$ENV_CONFIG_PATH" >> "\$GSODS_HOME/.bashrc"
        fi
        if ! grep -q "export PYTHONPATH=" "\$GSODS_HOME/.bashrc" 2>/dev/null; then
            echo "export PYTHONPATH=$GIGA_PATH/gs-odsx" >> "\$GSODS_HOME/.bashrc"
        fi

        GSODS_UID=\$(id -u gsods)
        if ! grep -q "XDG_RUNTIME_DIR" "\$GSODS_HOME/.bashrc" 2>/dev/null; then
            echo "export XDG_RUNTIME_DIR=/run/user/\$GSODS_UID" >> "\$GSODS_HOME/.bashrc"
            echo "export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/\$GSODS_UID/bus" >> "\$GSODS_HOME/.bashrc"
        fi

        chown gsods:gsods "\$GSODS_HOME/.bashrc"

        echo "    Done."
REMOTE_SCRIPT

done

echo ""
echo "============================================"
echo "  Setup complete."
echo ""
echo "  Verify NFS mounts on remote hosts:"
echo "    (from pivot, run: showmount -e $PIVOT_IP)"
echo ""
echo "  Verify SSH as gsods from pivot:"
echo "    su - gsods"
for HOST in $ALL_HOSTS; do
    echo "    ssh gsods@$HOST hostname"
done
echo ""
echo "  Then run ODSX as gsods:"
echo "    su - gsods"
echo "    cd $GIGA_PATH/gs-odsx"
echo "    ./odsx.py"
echo "============================================"
