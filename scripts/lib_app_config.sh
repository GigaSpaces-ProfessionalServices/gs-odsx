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
