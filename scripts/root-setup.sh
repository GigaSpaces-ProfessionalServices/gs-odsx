#!/bin/bash
# root-setup.sh — Run once as root on the pivot machine.
# Creates the app user, enables linger, sets up NFS, and configures
# sudoers. Requires gigashare to be already extracted (by user-setup.sh
# or manually) so that app.config and host.yaml are readable.
#
# Typical workflow:
#   1. user-setup.sh -d /gigashare -u <appuser> -tar /path/gigashare.tgz
#   2. root-setup.sh -d /gigashare       (this script)
#   3. user-setup.sh -d /gigashare -u <appuser>   (re-run for remote hosts)

# Load shared read_property helper (no-op when piped over SSH; see lib_app_config.sh).
[ -r "$(dirname "$0")/lib_app_config.sh" ] && source "$(dirname "$0")/lib_app_config.sh"

function usage () {
  cat << EOF

  NAME

    $(basename $0) – ODSX one-time root setup

  USAGE

    $(basename $0) -d <gigashare dir>

  OPTIONS

    -d <dir>      Gigashare directory (e.g. /gigashare)

  PREREQUISITE

    Gigashare must already be extracted (app.config and host.yaml must exist
    inside <gigashare dir>/env_config/). Use user-setup.sh -tar to extract.

  EXAMPLE

    ./$(basename $0) -d /gigashare

  NEXT STEP

    After this script completes, re-run user-setup.sh as the app user
    to deploy SSH keys and configure remote hosts:
      su - <appuser>
      cd /giga/gs-odsx/scripts
      ./user-setup.sh -d /gigashare -u <appuser>

EOF
exit
}

set -e

# Must run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root."
    exit 1
fi

[[ $# -eq 0 ]] && usage

# Pre-scan for help/info flags (also accepts the legacy positional usage hint)
for _arg in "$@"; do
    case "$_arg" in
        -h|--help) usage ;;
        --info) _SHOW_INFO=true ;;
    esac
done

[[ "${_SHOW_INFO:-false}" == "true" ]] && {
  cat <<'INFO'

  root-setup.sh — What it does
  ============================

  Prerequisite: Gigashare must already be extracted (by user-setup.sh -tar
  or manually) so app.config and host.yaml exist.

  Config reading:
    - Reads app.giga.path, app.gigashare.path, app.gigainfluxdata.path,
      and app.server.user from app.config
    - Reads all host IPs from host.yaml, determines which are remote
      (non-pivot)

  Step 1 — Pivot configuration:
    1. Creates the app user (useradd -m) if it doesn't exist
    2. Enables systemd linger for the app user (so user services survive
       logout)
    3. Writes /etc/sudoers.d/odsx-monitoring — passwordless sudo for the
       app user to start/stop/restart/status/enable Grafana, InfluxDB,
       and Telegraf system services
    4. Appends ENV_CONFIG, PYTHONPATH, ODSXARTIFACTS to root's .bashrc
       (idempotent, skips if already present)

  Step 2 — NFS server on pivot:
    1. Installs nfs-utils if missing
    2. Adds per-remote-host export entries to /etc/exports (idempotent)
    3. Enables nfs-server and refreshes exports

  Step 3 — Per-remote-host loop (via SSH as root):
    1. Creates the app user if it doesn't exist
    2. Enables linger
    3. Creates the gigashare mount point directory, chowns it to the app
       user
    4. Installs nfs-utils if missing
    5. Adds an fstab entry for the NFS mount (idempotent, uses 'users'
       option so the app user can mount/umount without sudo)
    6. Mounts the NFS share if not already mounted
    7. Verifies the mount succeeded

  In short: it does the things that require root — user creation, linger,
  sudoers, NFS server/client setup — on the pivot and all remote hosts.
  Everything else (SSH keys, env vars, GS install, directories) is
  handled by user-setup.sh.

INFO
  exit
}
GIGASHARE_DIR=""
while getopts ":d:h" opt; do
    case $opt in
        d) GIGASHARE_DIR=$OPTARG ;;
        h) usage ;;
        \?) echo "Unknown option: -$OPTARG" >&2; usage ;;
        :)  echo "Option -$OPTARG requires an argument" >&2; usage ;;
    esac
done

[[ -z "$GIGASHARE_DIR" ]] && { echo -e "\nMust provide a gigashare directory via -d.\n" ; usage ; }
[[ ! -d "$GIGASHARE_DIR" ]] && { echo -e "\nThe gigashare directory does not exist.\n" ; exit 1 ; }

ENV_CONFIG_PATH="$GIGASHARE_DIR/env_config"
echo "ENV_CONFIG_PATH is set to: $ENV_CONFIG_PATH"
[[ ! -d "$ENV_CONFIG_PATH" ]] && { echo -e "\nThe gigashare/env_config does not exist. Extract gigashare first.\n" ; exit 1 ; }

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


# Read required variables from app.config
GIGA_PATH=$(read_property "app.giga.path")
GIGA_SHARE=$(read_property "app.gigashare.path")
GIGA_INFLUX=$(read_property "app.gigainfluxdata.path")
GIGA_DATA=$(read_property "app.gigadata.path")
GIGA_LOG=$(read_property "app.gigalog.path")
GIGA_WORK=$(read_property "app.gigawork.path")
APP_USER=$(read_property "app.server.user")
APP_USER=${APP_USER:-gsods}

# OS prereqs installed on the pivot and every remote host.
PREREQ_PACKAGES="bc python3.9 python3-pip java-17-openjdk-devel nc jq bind-utils git wget vim nfs-utils expect mlocate bash-completion zip unzip"
YQ_URL="https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64"

# Validate required keys
missing_paths=0
for key_var in "app.giga.path:$GIGA_PATH" \
               "app.gigashare.path:$GIGA_SHARE" \
               "app.gigainfluxdata.path:$GIGA_INFLUX" \
               "app.gigadata.path:$GIGA_DATA" \
               "app.gigalog.path:$GIGA_LOG" \
               "app.gigawork.path:$GIGA_WORK"; do
  key="${key_var%%:*}"
  val="${key_var#*:}"
  if [ -z "$val" ]; then
    echo "Error: '$key' is not set in $APP_CONFIG."
    missing_paths=1
  fi
done
if [ "$missing_paths" -eq 1 ]; then
  exit 1
fi

# Compute unique parent directories of all 6 path roots. Each is mkdir'd
# and chowned -R to APP_USER on every remote host, so that user-setup.sh
# (running as APP_USER) can later mkdir the leaf paths under them.
# Parents that resolve to "/" (the default top-level layout, e.g. /giga,
# /gigashare) are skipped — chowning "/" would be catastrophic.
PATH_PARENTS=$(
    for p in "$GIGA_PATH" "$GIGA_SHARE" "$GIGA_INFLUX" \
             "$GIGA_DATA"  "$GIGA_LOG"   "$GIGA_WORK"; do
        d=$(dirname "$p")
        case "$d" in /|.|"") ;; *) printf '%s\n' "$d" ;; esac
    done | sort -u
)

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
echo "  ODSX Root Setup"
echo "============================================"
echo "Pivot IP:     $PIVOT_IP"
echo "App user:     $APP_USER"
echo "Giga share:   $GIGA_SHARE"
echo "Remote hosts:"
for h in $ALL_HOSTS; do
    echo "  $h"
done
echo ""

# Ensure app user exists on pivot
if ! id "$APP_USER" >/dev/null 2>&1; then
    useradd -m "$APP_USER"
    echo "Created $APP_USER user."
fi

# --- Step 0: Install prereq packages on pivot ---
echo ">>> Step 0: Installing prereq packages on pivot..."
dnf -y install $PREREQ_PACKAGES
if [ ! -x /usr/local/bin/yq ]; then
    wget -qO /usr/local/bin/yq "$YQ_URL" && chmod +x /usr/local/bin/yq
    echo "    yq installed to /usr/local/bin/yq."
else
    echo "    yq already present."
fi
echo ""

# --- Step 1: Configure pivot (root-only operations) ---
echo ">>> Step 1: Configuring pivot (root-only)..."

# Enable linger
loginctl enable-linger "$APP_USER" 2>/dev/null && echo "    Linger enabled." || echo "    Linger already enabled or not supported."

# Sudoers for third-party monitoring services (Grafana, InfluxDB, Telegraf)
cat > /etc/sudoers.d/odsx-monitoring <<SUDOERS
$APP_USER ALL=(ALL) NOPASSWD: /bin/systemctl start grafana-server.service, /bin/systemctl stop grafana-server.service, /bin/systemctl restart grafana-server.service, /bin/systemctl status grafana-server.service, /bin/systemctl enable grafana-server.service
$APP_USER ALL=(ALL) NOPASSWD: /bin/systemctl start influxdb.service, /bin/systemctl stop influxdb.service, /bin/systemctl restart influxdb.service, /bin/systemctl status influxdb.service, /bin/systemctl enable influxdb.service
$APP_USER ALL=(ALL) NOPASSWD: /bin/systemctl start telegraf.service, /bin/systemctl stop telegraf.service, /bin/systemctl restart telegraf.service, /bin/systemctl status telegraf.service, /bin/systemctl enable telegraf.service
SUDOERS
chmod 0440 /etc/sudoers.d/odsx-monitoring
echo "    Sudoers for monitoring services configured."

# Set env vars in root's .bashrc on pivot (idempotent)
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

# --- Step 2: Set up NFS server on pivot ---
echo ">>> Step 2: Setting up NFS server on pivot..."

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

# Read the app user's pubkey from the pivot (generated by user-setup.sh step 4).
# It's seeded into each remote's authorized_keys so user-setup.sh's BatchMode
# SSH probe in step 6 can connect on the next pass.
APP_USER_HOME=$(getent passwd "$APP_USER" | cut -d: -f6)
APP_PUBKEY=""
if [ -n "$APP_USER_HOME" ] && [ -f "$APP_USER_HOME/.ssh/id_ed25519.pub" ]; then
    APP_PUBKEY=$(cat "$APP_USER_HOME/.ssh/id_ed25519.pub")
    echo "Found $APP_USER pubkey on pivot — will seed it on each remote."
else
    echo "WARNING: No pubkey at $APP_USER_HOME/.ssh/id_ed25519.pub — run user-setup.sh"
    echo "         once on the pivot to generate one, then re-run root-setup.sh."
fi
echo ""

# --- Step 3: Configure each remote host (root-only operations) ---
echo ">>> Step 3: Configuring remote hosts (root-only)..."

for HOST in $REMOTE_HOSTS; do
    echo "  --- $HOST ---"

    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "$HOST" bash <<REMOTE_SCRIPT
        set -e

        # Ensure app user exists
        if ! id $APP_USER &>/dev/null; then
            useradd $APP_USER
            echo "    Created $APP_USER user."
        fi

        # Seed the pivot's app-user pubkey into the remote's authorized_keys
        # FIRST, before anything that might fail. This guarantees user-setup.sh's
        # BatchMode SSH probe (step 6) can always connect, even if a later step
        # in this heredoc errors out. Idempotent: grep -qF before append.
        if [ -n "$APP_PUBKEY" ]; then
            REMOTE_HOME=\$(getent passwd $APP_USER | cut -d: -f6)
            install -d -m 700 -o $APP_USER -g $APP_USER "\$REMOTE_HOME/.ssh"
            touch "\$REMOTE_HOME/.ssh/authorized_keys"
            if ! grep -qF "$APP_PUBKEY" "\$REMOTE_HOME/.ssh/authorized_keys" 2>/dev/null; then
                echo "$APP_PUBKEY" >> "\$REMOTE_HOME/.ssh/authorized_keys"
                echo "    Pivot pubkey seeded into $APP_USER authorized_keys."
            else
                echo "    Pivot pubkey already present in $APP_USER authorized_keys."
            fi
            chown $APP_USER:$APP_USER "\$REMOTE_HOME/.ssh/authorized_keys"
            chmod 600 "\$REMOTE_HOME/.ssh/authorized_keys"
        fi

        # Install prereq packages. Non-fatal: a missing package on one host
        # shouldn't abort the rest of remote setup. The warning surfaces the
        # failure so it can be diagnosed without blocking everything else.
        if ! dnf -y install $PREREQ_PACKAGES; then
            echo "    WARNING: dnf install reported failures — check repo availability for: $PREREQ_PACKAGES"
        fi
        if [ ! -x /usr/local/bin/yq ]; then
            if wget -qO /usr/local/bin/yq "$YQ_URL" && chmod +x /usr/local/bin/yq; then
                echo "    yq installed to /usr/local/bin/yq."
            else
                echo "    WARNING: yq fetch failed from $YQ_URL"
                rm -f /usr/local/bin/yq
            fi
        else
            echo "    yq already present."
        fi

        # Enable linger and ensure the user manager is up with a live bus socket.
        # Robust against three known failure modes:
        #   1. enable-linger silently fails (we used to swallow errors with || true)
        #   2. enable-linger sets the flag but doesn't start user@\$UID until next
        #      boot/login on some systemd configs — explicit start fixes this
        #   3. user manager is running but /run/user/\$UID/ got wiped (zombie state,
        #      e.g. after the rm -rf /* incident) — restart the manager to recreate
        #      the bus socket
        loginctl enable-linger $APP_USER
        _uid=\$(id -u $APP_USER)
        systemctl start user@\$_uid.service 2>/dev/null || true
        for _i in \$(seq 1 15); do
            [ -S "/run/user/\$_uid/bus" ] && break
            sleep 1
        done
        # Zombie recovery: manager active but bus missing → restart
        if [ ! -S "/run/user/\$_uid/bus" ] && systemctl is-active user@\$_uid.service >/dev/null 2>&1; then
            echo "    User manager active but /run/user/\$_uid/bus missing — restarting"
            systemctl restart user@\$_uid.service
            for _i in \$(seq 1 15); do
                [ -S "/run/user/\$_uid/bus" ] && break
                sleep 1
            done
        fi
        if [ ! -S "/run/user/\$_uid/bus" ]; then
            echo "    ERROR: /run/user/\$_uid/bus did not appear after enabling linger and (re)starting user@\$_uid.service" >&2
            journalctl -u user@\$_uid.service --no-pager -n 20 >&2 || true
            exit 1
        fi
        echo "    Linger enabled and user bus is live at /run/user/\$_uid/bus."

        # Prepare parent directories of all 6 path roots: mkdir -p and
        # chown -R to APP_USER. This is what allows user-setup.sh to
        # later create leaf dirs (giga, gigalogs, gigadata, gigawork,
        # gigashare, gigainfluxdata) as APP_USER without sudo.
        # No-op when path roots live directly under "/" (default layout).
        for parent in $PATH_PARENTS; do
            mkdir -p "\$parent"
            chown -R $APP_USER:$APP_USER "\$parent"
            echo "    parent ready: \$parent (chowned -R to $APP_USER)"
        done

        # Create gigashare mount point
        mkdir -p $GIGA_SHARE
        chown $APP_USER:$APP_USER $GIGA_SHARE

        # Set up NFS client for gigashare
        if ! rpm -q nfs-utils &>/dev/null; then
            yum install -y nfs-utils 2>/dev/null || apt-get install -y nfs-common 2>/dev/null || true
            echo "    nfs-utils installed."
        fi

        # Add fstab entry (idempotent)
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

        echo "    Done."
REMOTE_SCRIPT

done

echo ""
echo "============================================"
echo "  Root setup complete."
echo ""
echo "  Next step — re-run user-setup.sh as the app user to"
echo "  deploy SSH keys and configure remote hosts:"
echo "    su - $APP_USER"
echo "    cd $GIGA_PATH/gs-odsx/scripts"
echo "    ./user-setup.sh -d $GIGA_SHARE -u $APP_USER"
echo ""
echo "  Verify NFS mounts on remote hosts:"
echo "    showmount -e $PIVOT_IP"
echo "============================================"
