#!/usr/bin/env bash
#
# telegrafctl.sh — Install/remove Telegraf on all cluster hosts based on
# their role in host.yaml. Runs as root on the pivot, SSHes to each host.
#
# Roles: manager (base metrics), space (+ WAL size), pivot (+ monitoring scripts).
# DI and NB are out of scope.
#
# Artifacts expected under $ODSXARTIFACTS/telegraf/:
#   *.rpm                              Telegraf RPM
#   config/pivot/pivot.telegraf.conf   Extra inputs for pivot
#   config/space/space.telegraf.conf   Extra inputs for space
#   scripts/pivot/*.sh                 Pivot monitoring scripts
#   scripts/space/telegraf_wal-size.sh WAL size script for space hosts
#
# Requires: $ENV_CONFIG, $ODSXARTIFACTS (for -i), yq, SSH root access to all hosts.

set -euo pipefail

SCRIPT_NAME=$(basename "$0")

usage() {
    cat <<EOF
Usage: $SCRIPT_NAME {-i|-r|-h} [--purge]

  -i            Install Telegraf on all cluster hosts per role.
  -r            Remove Telegraf from all cluster hosts.
  --purge       (with -r) Also delete custom metric scripts from the
                bin directory on each host. Passing --purge is itself
                the confirmation — no prompt.
  -h            Show this help.

Roles and what gets deployed:
  all hosts     RPM + base config (system metrics → InfluxDB)
  space         + space.telegraf.conf, telegraf_wal-size.sh
  pivot         + pivot.telegraf.conf, pu_status.sh,
                  space-status.gc-state.sh

Environment:
  ENV_CONFIG     Required. Directory containing app.config and host.yaml.
  ODSXARTIFACTS  Required for -i. Contains telegraf/ subdirectory.
EOF
}

die() { echo "Error: $*" >&2; exit 1; }

SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"

get_hosts_by_role() {
    local role=$1
    yq -r ".servers.${role} // {} | values[]" "$HOST_YAML" 2>/dev/null || true
}

declare -A HOST_ROLES=()

build_host_roles() {
    local role ip
    for role in manager space pivot; do
        for ip in $(get_hosts_by_role "$role"); do
            HOST_ROLES[$ip]="${HOST_ROLES[$ip]:-}${HOST_ROLES[$ip]:+ }$role"
        done
    done
    [ ${#HOST_ROLES[@]} -gt 0 ] || die "no manager/space/pivot hosts found in $HOST_YAML"
}

build_influx_urls() {
    local urls="" ip
    for ip in $(get_hosts_by_role influxdb); do
        [ -n "$urls" ] && urls+=","
        urls+="\"http://${ip}:8086\""
    done
    [ -n "$urls" ] || die "no influxdb hosts found in $HOST_YAML"
    echo "$urls"
}

generate_base_config() {
    local influx_urls=$1
    cat <<EOF
[agent]
  interval = "10s"
  round_interval = true
  metric_batch_size = 1000
  metric_buffer_limit = 10000
  collection_jitter = "0s"
  flush_interval = "10s"
  flush_jitter = "0s"
  precision = ""
  debug = false
  logtarget = "file"
  logfile = "/var/log/telegraf/telegraf.log"
  hostname = ""
  omit_hostname = false

[[outputs.influxdb]]
  urls = [$influx_urls]

[[inputs.cpu]]
  percpu = true
  totalcpu = true
  collect_cpu_time = false
  report_active = false

[[inputs.disk]]
  ignore_fs = ["tmpfs", "devtmpfs", "devfs", "iso9660", "overlay", "aufs", "squashfs"]

[[inputs.diskio]]

[[inputs.kernel]]

[[inputs.mem]]

[[inputs.processes]]

[[inputs.swap]]

[[inputs.system]]

[[inputs.systemd_units]]
  timeout = "5s"
  unittype = "service"
EOF
}

build_full_config() {
    local influx_urls=$1 src=$2
    local has_pivot=$3 has_space=$4

    generate_base_config "$influx_urls"

    # Telegraf runs as its own 'telegraf' user (created by the RPM), so monitoring
    # scripts must live in /usr/local/bin/ — NOT in gsods-owned paths like
    # $giga_bin. The configs ship referencing /usr/local/bin/ already, so we
    # append them verbatim.
    if [ "$has_pivot" = "true" ] && [ -f "$src/config/pivot/pivot.telegraf.conf" ]; then
        printf '\n# Telegraf pivot config START\n'
        cat "$src/config/pivot/pivot.telegraf.conf"
        printf '\n# Telegraf pivot config END\n'
    fi

    if [ "$has_space" = "true" ] && [ -f "$src/config/space/space.telegraf.conf" ]; then
        printf '\n# Telegraf space config START\n'
        cat "$src/config/space/space.telegraf.conf"
        printf '\n# Telegraf space config END\n'
    fi
}

install_on_host() {
    local host=$1
    local roles="${HOST_ROLES[$host]}"
    local src="$ODSXARTIFACTS/telegraf"

    local has_pivot=false has_space=false
    for role in $roles; do
        case $role in
            pivot) has_pivot=true ;;
            space) has_space=true ;;
        esac
    done

    echo "  --- $host [$roles] ---"

    build_full_config "$INFLUX_URLS" "$src" "$has_pivot" "$has_space" \
        | ssh $SSH_OPTS "$host" 'mkdir -p /etc/telegraf && cat > /etc/telegraf/telegraf.conf'
    echo "    Config deployed."

    # shellcheck disable=SC2086
    ssh $SSH_OPTS "$host" bash -s \
        "$src" "$has_pivot" "$has_space" <<'REMOTE'
set -e
src=$1; has_pivot=$2; has_space=$3

# Telegraf runs as its own 'telegraf' user and cannot read gsods-owned paths,
# so monitoring scripts go into /usr/local/bin/. This script runs as root on
# the remote host (SSH target), so writing to /usr/local/bin/ is fine.
bin=/usr/local/bin

if ! rpm -q telegraf >/dev/null 2>&1; then
    rpm_file=$(find "$src" -maxdepth 1 -name '*.rpm' | head -n1)
    [ -n "$rpm_file" ] || { echo "    Error: no RPM in $src"; exit 1; }
    yum localinstall -y "$rpm_file"
    echo "    RPM installed."
else
    echo "    RPM already installed ($(rpm -q telegraf))."
fi

if [ "$has_pivot" = "true" ]; then
    for f in "$src/scripts/pivot/"*.sh; do
        [ -f "$f" ] || continue
        bname=$(basename "$f")
        [ "$bname" = "test.sh" ] && continue
        cp "$f" "$bin/"
    done
    # pivot.telegraf.conf references gc-state.sh but artifact is space-status.gc-state.sh
    [ -f "$bin/space-status.gc-state.sh" ] && \
        ln -snf space-status.gc-state.sh "$bin/gc-state.sh"
    echo "    Pivot scripts deployed."
fi

if [ "$has_space" = "true" ]; then
    [ -f "$src/scripts/space/telegraf_wal-size.sh" ] && \
        cp "$src/scripts/space/telegraf_wal-size.sh" "$bin/"
    echo "    Space scripts deployed."
fi

chmod +x "$bin/pu_status.sh" "$bin/space-status.gc-state.sh" \
         "$bin/telegraf_wal-size.sh" 2>/dev/null || true
chown -R telegraf:telegraf /etc/telegraf
systemctl enable telegraf.service
systemctl restart telegraf.service

for _ in $(seq 1 10); do
    systemctl is-active --quiet telegraf.service && break
    sleep 1
done
if systemctl is-active --quiet telegraf.service; then
    echo "    Telegraf running."
else
    echo "    WARNING: Telegraf failed to start."
fi
REMOTE
}

remove_from_host() {
    local host=$1 purge=$2

    echo "  --- $host ---"

    # shellcheck disable=SC2086
    ssh $SSH_OPTS "$host" bash -s "$purge" <<'REMOTE'
set -e
purge=$1
bin=/usr/local/bin

if systemctl list-unit-files 2>/dev/null | grep -q '^telegraf\.service'; then
    systemctl stop telegraf.service 2>/dev/null || true
    systemctl disable telegraf.service 2>/dev/null || true
fi
yum erase -y telegraf 2>/dev/null || true
rm -rf /etc/telegraf/

if [ "$purge" = "yes" ]; then
    rm -f "$bin/pu_status.sh" \
          "$bin/space-status.gc-state.sh" \
          "$bin/gc-state.sh" \
          "$bin/telegraf_wal-size.sh"
    echo "    Custom scripts purged."
fi

echo "    Telegraf removed."
REMOTE
}

APP_CONFIG=""
HOST_YAML=""
INFLUX_URLS=""

resolve_globals() {
    : "${ENV_CONFIG:?ENV_CONFIG must be set}"
    APP_CONFIG="$ENV_CONFIG/app.config"
    HOST_YAML="$ENV_CONFIG/host.yaml"
    [ -f "$APP_CONFIG" ] || die "$APP_CONFIG not found"
    [ -f "$HOST_YAML" ] || die "$HOST_YAML not found"
    command -v yq >/dev/null 2>&1 || die "yq is required but not found"
}

install_all() {
    : "${ODSXARTIFACTS:?ODSXARTIFACTS must be set}"
    resolve_globals
    INFLUX_URLS=$(build_influx_urls)
    build_host_roles

    local rpm_file
    rpm_file=$(find "$ODSXARTIFACTS/telegraf" -maxdepth 1 -name '*.rpm' -printf '%f\n' | head -n1)
    [ -n "$rpm_file" ] || die "no RPM found in $ODSXARTIFACTS/telegraf/"

    echo "Installing Telegraf on ${#HOST_ROLES[@]} host(s)..."
    echo "  RPM:              $rpm_file"
    echo "  InfluxDB targets: $INFLUX_URLS"
    echo "  Scripts dir:      /usr/local/bin (telegraf user owned)"
    echo ""

    for host in "${!HOST_ROLES[@]}"; do
        install_on_host "$host"
        echo ""
    done
    echo "Done."
}

remove_all() {
    local purge=$1
    resolve_globals
    build_host_roles

    echo "Removing Telegraf from ${#HOST_ROLES[@]} host(s)..."
    echo ""

    for host in "${!HOST_ROLES[@]}"; do
        remove_from_host "$host" "$purge"
        echo ""
    done
    echo "Done."
}

action=""
purge=no
args=()
for a in "$@"; do
    case $a in
        --purge) purge=yes ;;
        *) args+=("$a") ;;
    esac
done
set -- "${args[@]+"${args[@]}"}"

while getopts ":irh" opt; do
    case $opt in
        i) action=install ;;
        r) action=remove ;;
        h) usage; exit 0 ;;
        \?) echo "Unknown option: -$OPTARG" >&2; usage; exit 2 ;;
    esac
done

if [ "$purge" = "yes" ] && [ "$action" != "remove" ]; then
    die "--purge is only valid with -r"
fi

case $action in
    install) install_all ;;
    remove)  remove_all "$purge" ;;
    *)       usage; exit 2 ;;
esac
