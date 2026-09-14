#!/usr/bin/env bash
#
# influxdbctl.sh — install/remove InfluxDB on the local host without going
# through the ODSX menu. Mirrors the atomic actions performed by
# scripts/servers_influxdb_install.sh and scripts/servers_influxdb_remove.sh,
# with fixes applied:
#   * template data dir is parameterized from app.gigainfluxdata.path
#   * `CREATE DATABASE mydb` is piped into influx -execute (idempotent)
#   * config-file append is idempotent (marker-bounded)
#
# Data directory is always read from $ENV_CONFIG/app.config (key
# app.gigainfluxdata.path) — the same source the rest of ODSX uses. To
# deploy to a different path, edit app.config, do not override here.
#
# Requires: $ENV_CONFIG set, $ODSXARTIFACTS set (for install), sudo, yum.

set -euo pipefail

usage() {
    cat <<EOF
Usage: $(basename "$0") {-i|-r|-h} [--purge]

  -i            Install InfluxDB on this host. Data dir is read from
                app.gigainfluxdata.path in \$ENV_CONFIG/app.config.
  -r            Remove InfluxDB from this host (stop, yum erase, delete
                /etc/influxdb/). Data directory is left intact unless
                --purge is given.
  --purge       (with -r) Also delete the InfluxDB data directory
                (<data-dir>/influxdb/{data,meta,wal}) after removal.
                Passing --purge is itself the confirmation — no prompt.
  -h            Show this help

Environment:
  ENV_CONFIG     Required. Directory containing app.config.
  ODSXARTIFACTS  Required for -i. Path containing influx/*.rpm and
                 influx/config/influxdb.conf.template (e.g. /gigashare/current).
EOF
}

# Load shared read_property helper.
source "$(dirname "$0")/lib_app_config.sh"

resolve_data_dir() {
    [ -n "${ENV_CONFIG:-}" ] && [ -f "$ENV_CONFIG/app.config" ] || {
        echo "Error: ENV_CONFIG not set or app.config not found" >&2
        exit 1
    }
    local dir
    dir=$(read_property app.gigainfluxdata.path)
    [ -n "$dir" ] || {
        echo "Error: cannot read app.gigainfluxdata.path from \$ENV_CONFIG/app.config" >&2
        exit 1
    }
    printf '%s\n' "$dir"
}

install_influxdb() {
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

    local dir
    dir=$(resolve_data_dir)
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
    local purge=$1

    if systemctl list-unit-files 2>/dev/null | grep -q '^influxdb\.service'; then
        sudo systemctl stop influxdb.service 2>/dev/null || true
        sudo systemctl disable influxdb.service 2>/dev/null || true
    fi
    sudo yum erase -y influxdb || true
    sudo rm -rf /etc/influxdb/

    if [ "$purge" = "yes" ]; then
        local data_dir target
        data_dir=$(resolve_data_dir)
        target="$data_dir/influxdb"
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
    echo "Error: --purge is only valid with -r" >&2
    exit 2
fi

case $action in
    install) install_influxdb ;;
    remove)  remove_influxdb "$purge" ;;
    *)       usage; exit 2 ;;
esac
