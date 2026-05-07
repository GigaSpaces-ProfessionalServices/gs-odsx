# shellcheck shell=bash
# lib_app_config.sh — shared helper for reading app.config from bash.
#
# Provides one function:
#   read_property KEY [APP_CONFIG_PATH]
#     - Reads KEY=value from app.config (default: $ENV_CONFIG/app.config)
#     - Resolves ${app.*.path} placeholders against the same file
#
# Usage:
#   source "$(dirname "$0")/lib_app_config.sh"
#   db=$(read_property app.dataengine.db2-feeder.sqlite.dbfile)
#
# Mirrors expand_path_placeholders() in utils/ods_app_config.py so Python
# and bash readers stay in lockstep.

read_property() {
    local key="$1"
    # Resolution order for the config path:
    #   1) explicit second argument
    #   2) $APP_CONFIG  (set by user-setup.sh / root-setup.sh / a few installers)
    #   3) $ENV_CONFIG_PATH  (set by most install/remove scripts to the .config file)
    #   4) $ENV_CONFIG/app.config  (the standard runtime layout)
    local cfg="${2:-${APP_CONFIG:-${ENV_CONFIG_PATH:-${ENV_CONFIG}/app.config}}}"
    # If the resolved path is a directory (some scripts set ENV_CONFIG_PATH
    # to the env_config dir, not the file), append /app.config.
    [[ -d "$cfg" ]] && cfg="$cfg/app.config"
    local raw
    raw=$(awk -F'=' -v k="$key" '$1==k {sub(/^[^=]*=/,""); print; exit}' "$cfg")
    while [[ "$raw" =~ \$\{(app\.[a-z]+\.path)\} ]]; do
        local ref="${BASH_REMATCH[1]}"
        local val
        val=$(awk -F'=' -v k="$ref" '$1==k {sub(/^[^=]*=/,""); print; exit}' "$cfg")
        raw="${raw//\$\{${ref}\}/${val}}"
    done
    printf '%s\n' "$raw"
}

# Wait up to 15s for the user systemd bus socket to appear. Race avoidance
# for `systemctl --user` calls on freshly-provisioned hosts where
# loginctl enable-linger may have only just started the user manager and
# /run/user/$UID/bus hasn't materialized yet.
#
# Bails loudly on timeout — better than letting the following systemctl call
# fail with the cryptic "Failed to connect to bus: No such file or directory".
#
#   export XDG_RUNTIME_DIR=/run/user/$(id -u)
#   export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus
#   wait_for_user_bus
#   systemctl --user enable foo.service
wait_for_user_bus() {
    local _bus="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/bus"
    local _i
    for _i in $(seq 1 15); do
        [ -S "$_bus" ] && return 0
        sleep 1
    done
    echo "Error: user systemd bus did not appear at $_bus within 15s." >&2
    echo "       Linger may not be enabled for $(id -un). Diagnose with:" >&2
    echo "       loginctl show-user \$(id -un) -p Linger" >&2
    exit 1
}

# Refuse to proceed if any of the named variables is empty/unset.
# Use BEFORE any destructive op on a value that came from read_property:
# an empty value would expand "$VAR/*" to "/*" or "find $VAR/" to "find /"
# and walk the root filesystem.
#
#   gigapath=$(read_property "app.giga.path")
#   gigaworkPath=$(read_property "app.gigawork.path")
#   validate_nonempty_paths gigapath gigaworkPath
validate_nonempty_paths() {
    local _name
    for _name in "$@"; do
        if [ -z "${!_name}" ]; then
            echo "Error: \$$_name is empty — refusing to run destructive ops." >&2
            echo "       Check that lib_app_config.sh is in scope and app.config" >&2
            echo "       is readable on this host (env: ENV_CONFIG=$ENV_CONFIG)." >&2
            exit 1
        fi
    done
}
