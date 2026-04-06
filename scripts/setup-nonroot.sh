#!/bin/bash
# setup_nonroot.sh - Run as root on the pivot machine.
# Prepares gsods user on pivot and all remote servers for non-root ODSX operation.
# Reads server IPs from host.yaml.

set -e

ENV_CONFIG_PATH=$ENV_CONFIG
if [ -z "$ENV_CONFIG_PATH" ]; then
    echo "Error: ENV_CONFIG is not set. Please set it before running this script."
    exit 1
fi

HOST_YAML="$ENV_CONFIG_PATH/host.yaml"
APP_CONFIG="$ENV_CONFIG_PATH/app.config"

if [ ! -f "$HOST_YAML" ]; then
    echo "Error: $HOST_YAML not found."
    exit 1
fi

# Must run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root."
    exit 1
fi

read_property() {
    local prop_name="$1"
    grep "^$prop_name=" "$APP_CONFIG" | awk -F'=' '{print $2}'
}

# Extract all unique IPs from host.yaml
ALL_HOSTS=$(grep -E '^\s+host[0-9]+\s*:' "$HOST_YAML" | awk '{print $NF}' | sort -u)
PIVOT_IP=$(hostname -I | awk '{print $1}')

echo "============================================"
echo "  ODSX Non-Root Setup"
echo "============================================"
echo "Pivot IP: $PIVOT_IP"
echo "Remote hosts:"
for h in $ALL_HOSTS; do
    echo "  $h"
done
echo ""

GSODS_HOME=$(eval echo ~gsods)
GIGA_PATH=$(read_property "app.giga.path")
GIGA_PATH=${GIGA_PATH:-/giga}
NOFILE_LIMIT=$(read_property "app.user.nofile.limit")
NOFILE_LIMIT=${NOFILE_LIMIT:-50000}

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
echo "    SSH config created."

# --- Step 2: Configure pivot ---
echo ">>> Step 2: Configuring pivot..."

# Enable linger
loginctl enable-linger gsods 2>/dev/null && echo "    Linger enabled." || echo "    Linger already enabled or not supported."

# Create user systemd dir
mkdir -p "$GSODS_HOME/.config/systemd/user/"
chown -R gsods:gsods "$GSODS_HOME/.config/"
echo "    User systemd directory ready."

# Create /giga/bin
mkdir -p "$GIGA_PATH/bin"
chown gsods:gsods "$GIGA_PATH/bin"
echo "    $GIGA_PATH/bin ready."

# Set nofile limits
sed -i '/gsods.*hard.*nofile/d' /etc/security/limits.conf
sed -i '/gsods.*soft.*nofile/d' /etc/security/limits.conf
echo "gsods hard nofile $NOFILE_LIMIT" >> /etc/security/limits.conf
echo "gsods soft nofile $NOFILE_LIMIT" >> /etc/security/limits.conf
echo "    nofile limits set to $NOFILE_LIMIT."

# Sudoers for monitoring services
cat > /etc/sudoers.d/odsx-monitoring << 'SUDOERS'
gsods ALL=(ALL) NOPASSWD: /bin/systemctl start grafana-server.service, /bin/systemctl stop grafana-server.service, /bin/systemctl restart grafana-server.service, /bin/systemctl status grafana-server.service, /bin/systemctl enable grafana-server.service
gsods ALL=(ALL) NOPASSWD: /bin/systemctl start influxdb.service, /bin/systemctl stop influxdb.service, /bin/systemctl restart influxdb.service, /bin/systemctl status influxdb.service, /bin/systemctl enable influxdb.service
gsods ALL=(ALL) NOPASSWD: /bin/systemctl start telegraf.service, /bin/systemctl stop telegraf.service, /bin/systemctl restart telegraf.service, /bin/systemctl status telegraf.service, /bin/systemctl enable telegraf.service
SUDOERS
chmod 0440 /etc/sudoers.d/odsx-monitoring
echo "    Sudoers for monitoring services configured."

# Set ENV_CONFIG in gsods .bashrc on pivot
if ! grep -q "export ENV_CONFIG=" "$GSODS_HOME/.bashrc" 2>/dev/null; then
    echo "export ENV_CONFIG=$ENV_CONFIG_PATH" >> "$GSODS_HOME/.bashrc"
    echo "    ENV_CONFIG added to gsods .bashrc."
fi
if ! grep -q "export PYTHONPATH=" "$GSODS_HOME/.bashrc" 2>/dev/null; then
    echo "export PYTHONPATH=$GIGA_PATH/gs-odsx" >> "$GSODS_HOME/.bashrc"
    echo "    PYTHONPATH added to gsods .bashrc."
fi
if ! grep -q "export ODSXARTIFACTS=" "$GSODS_HOME/.bashrc" 2>/dev/null; then
    GIGASHARE=$(read_property "app.gigashare.path")
    echo "export ODSXARTIFACTS=${GIGASHARE}/current/" >> "$GSODS_HOME/.bashrc"
    echo "    ODSXARTIFACTS added to gsods .bashrc."
fi
GSODS_UID=$(id -u gsods)
if ! grep -q "XDG_RUNTIME_DIR" "$GSODS_HOME/.bashrc" 2>/dev/null; then
    echo "export XDG_RUNTIME_DIR=/run/user/$GSODS_UID" >> "$GSODS_HOME/.bashrc"
    echo "export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$GSODS_UID/bus" >> "$GSODS_HOME/.bashrc"
    echo "    XDG_RUNTIME_DIR and DBUS_SESSION_BUS_ADDRESS added to gsods .bashrc."
fi
chown gsods:gsods "$GSODS_HOME/.bashrc"

echo "    Pivot configured."
echo ""

# --- Step 3: Configure each remote host ---
echo ">>> Step 3: Configuring remote hosts..."

for HOST in $ALL_HOSTS; do
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

        # Create /giga/bin
        mkdir -p "$GIGA_PATH/bin"
        chown gsods:gsods "$GIGA_PATH/bin" 2>/dev/null || true

        # Set nofile limits
        sed -i '/gsods.*hard.*nofile/d' /etc/security/limits.conf
        sed -i '/gsods.*soft.*nofile/d' /etc/security/limits.conf
        echo "gsods hard nofile $NOFILE_LIMIT" >> /etc/security/limits.conf
        echo "gsods soft nofile $NOFILE_LIMIT" >> /etc/security/limits.conf

        # Set ENV_CONFIG in gsods .bashrc
        if ! grep -q "export ENV_CONFIG=" "\$GSODS_HOME/.bashrc" 2>/dev/null; then
            echo "export ENV_CONFIG=$ENV_CONFIG_PATH" >> "\$GSODS_HOME/.bashrc"
        fi

        # Set XDG_RUNTIME_DIR and DBUS_SESSION_BUS_ADDRESS for systemctl --user over SSH
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
