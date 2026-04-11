#!/usr/bin/env bash
#
# influxdbctl.sh — install/remove InfluxDB on the local host without going
# through the ODSX menu. Mirrors the atomic actions performed by
# scripts/servers_influxdb_install.sh and scripts/servers_influxdb_remove.sh,
# with fixes applied:
#   * template data dir is parameterized via sed so a custom -d works
#   * `CREATE DATABASE mydb` is piped into influx -execute (idempotent)
#
# Requires: $ODSXARTIFACTS set (for install), sudo, yum.
# Reads $ENV_CONFIG/app.config for app.gigainfluxdata.path default when -d omitted.

set -euo pipefail

usage() {
    cat <<EOF
Usage: $(basename "$0") {-i|-r|-h} [-d <data-dir>] [--purge]

  -i            Install InfluxDB on this host
  -r            Remove InfluxDB from this host
  -d <dir>      Data directory. For -i, where to place data; for -r --purge,
                which directory to delete. Defaults to app.gigainfluxdata.path
                from \$ENV_CONFIG/app.config.
  --purge       (with -r) Also delete the InfluxDB data directory
                (<data-dir>/influxdb/{data,meta,wal}) after removal. Without
                --purge, data is left intact so a reinstall can reuse it.
                Passing --purge is itself the confirmation — no prompt.
  -h            Show this help

Environment:
  ODSXARTIFACTS  Required for -i. Path containing influx/*.rpm and
                 influx/config/influxdb.conf.template (e.g. /gigashare/current).
  ENV_CONFIG     Optional. Used to read app.gigainfluxdata.path default.
EOF
}

resolve_data_dir() {
    local dir=$1
    if [ -z "$dir" ]; then
        dir=$(read_app_config app.gigainfluxdata.path || true)
    fi
    [ -n "$dir" ] || { echo "Error: no -d given and app.gigainfluxdata.path unreadable" >&2; exit 1; }
    printf '%s\n' "$dir"
}

read_app_config() {
    local key=$1
    [ -n "${ENV_CONFIG:-}" ] && [ -f "$ENV_CONFIG/app.config" ] || return 1
    awk -F'=' -v k="$key" '$1==k {sub(/^[ \t]+/,"",$2); print $2; exit}' \
        "$ENV_CONFIG/app.config"
}

install_influxdb() {
    local dir=$1
    : "${ODSXARTIFACTS:?ODSXARTIFACTS must be set}"

    if rpm -q influxdb >/dev/null 2>&1; then
        echo "InfluxDB is already installed ($(rpm -q influxdb))."
        echo "Remove it first with: $(basename "$0") -r   (add --purge to also delete data)"
        exit 1
    fi

    local src="$ODSXARTIFACTS/influx"
    local rpm
    rpm=$(find "$src" -maxdepth 1 -name '*.rpm' -printf '%p\n' | head -n1)
    [ -n "$rpm" ] || { echo "Error: no RPM found in $src"; exit 1; }

    dir=$(resolve_data_dir "$dir")
    echo "InfluxDB data dir: $dir"
    echo "Installing RPM:    $rpm"

    sudo yum install -y "$rpm"

    sudo sed -i "s|/var/lib/influxdb/|$dir/influxdb/|g" /etc/influxdb/influxdb.conf

    sudo mkdir -p "$dir/influxdb/data" "$dir/influxdb/meta" "$dir/influxdb/wal"
    sudo chmod 755 "$dir"

    local tpl="$src/config/influxdb.conf.template"
    if [ ! -f "$tpl" ]; then
        echo "Warning: template $tpl missing — skipping config append"
    else
        # Idempotency: drop any previously-appended block so re-runs don't stack.
        if sudo grep -q '# Influxdb config START' /etc/influxdb/influxdb.conf; then
            sudo sed -i '/# Influxdb config START/,/# Influxdb config END/d' \
                /etc/influxdb/influxdb.conf
        fi

        # Comment out the stock [data] block on first run; no-op on re-runs
        # because it's already commented.
        if sudo grep -v '^ *#' /etc/influxdb/influxdb.conf | grep -q '\[data\]'; then
            local start end
            start=$(sudo grep -n -v '^ *\(--\|#\)' /etc/influxdb/influxdb.conf \
                    | grep '\[data\]' | cut -d: -f1 | head -n1)
            end=$(sudo sed -n '/series-id-set-cache-size = 100/=' /etc/influxdb/influxdb.conf \
                  | head -n1)
            if [ -n "$start" ] && [ -n "$end" ]; then
                sudo sed -i "$start,$end s/^/#/" /etc/influxdb/influxdb.conf
            fi
        fi

        {
            echo
            echo "# Influxdb config START"
            sed "s|/gigainfluxdata|$dir|g" "$tpl"
            echo "# Influxdb config END"
        } | sudo tee -a /etc/influxdb/influxdb.conf > /dev/null
    fi

    sudo chown -R influxdb:influxdb "$dir"
    sudo systemctl enable influxdb.service
    sudo systemctl restart influxdb.service

    for _ in $(seq 1 15); do
        sudo systemctl is-active --quiet influxdb.service && break
        sleep 1
    done
    sudo systemctl is-active --quiet influxdb.service \
        || { echo "Error: influxdb failed to start"; exit 1; }

    for _ in $(seq 1 10); do
        influx -execute 'SHOW DATABASES' >/dev/null 2>&1 && break
        sleep 1
    done
    influx -execute 'CREATE DATABASE mydb'
    echo "InfluxDB installed and mydb created."
}

remove_influxdb() {
    local purge=$1 data_dir=$2

    if systemctl list-unit-files 2>/dev/null | grep -q '^influxdb\.service'; then
        sudo systemctl stop influxdb.service 2>/dev/null || true
        sudo systemctl disable influxdb.service 2>/dev/null || true
    fi
    sudo yum erase -y influxdb || true
    sudo rm -rf /etc/influxdb/

    if [ "$purge" = "yes" ]; then
        data_dir=$(resolve_data_dir "$data_dir")
        local target="$data_dir/influxdb"
        if [ ! -d "$target" ]; then
            echo "Purge requested but $target does not exist — nothing to delete."
            return 0
        fi
        echo "Deleting InfluxDB data directory: $target"
        sudo rm -rf "$target"
        echo "Purged $target."
    else
        echo "InfluxDB removed. Data directory left intact (use --purge to delete)."
    fi
}

action=""
data_dir=""
purge=no
args=()
for a in "$@"; do
    case $a in
        --purge) purge=yes ;;
        *) args+=("$a") ;;
    esac
done
set -- "${args[@]+"${args[@]}"}"

while getopts ":irhd:" opt; do
    case $opt in
        i) action=install ;;
        r) action=remove ;;
        h) usage; exit 0 ;;
        d) data_dir=$OPTARG ;;
        \?) echo "Unknown option: -$OPTARG" >&2; usage; exit 2 ;;
        :)  echo "Option -$OPTARG requires an argument" >&2; usage; exit 2 ;;
    esac
done

if [ "$purge" = "yes" ] && [ "$action" != "remove" ]; then
    echo "Error: --purge is only valid with -r" >&2
    exit 2
fi

case $action in
    install) install_influxdb "$data_dir" ;;
    remove)  remove_influxdb "$purge" "$data_dir" ;;
    *)       usage; exit 2 ;;
esac
