#!/usr/bin/env bash
# configure_otel_identity.sh - stamp this cluster's OpenTelemetry resource
# identity into setenv-overrides.sh, so every GigaSpaces JVM on the host (the
# GSA and every GSC it spawns, which inherit its environment) exports it.
#
# WHY THIS EXISTS
#   The GigaSpaces 17.3.0 OTLP registry takes its OTel *resource* attributes
#   ONLY from the standard OTEL_* environment variables: its OtlpConfig
#   implementation returns null for every key, so there is no
#   metrics.otlp.resourceAttributes property to set and -D flags are ignored.
#   Without these variables Prometheus stores every cluster's series as
#   job="unknown_service", and several clusters pushing to one Prometheus
#   become indistinguishable.
#
#   Prometheus' OTLP receiver always derives these two labels, regardless of
#   its otlp.promote_resource_attributes setting:
#       job      = "<service.namespace>/<service.name>"
#       instance = "<service.instance.id>"
#   so exporting the two variables below is enough to separate clusters with
#   NO configuration change on the receiving Prometheus.
#
# Invoked from utils/ods_list.py:configureOtelIdentity() via
# build_remote_bash_cmd(), i.e. piped to `bash -s <target> <ns> <svc>` on the
# remote host with scripts/lib_app_config.sh prepended. Not run directly.
#
# Args:
#   $1  absolute path of the setenv-overrides.sh to edit
#   $2  service.namespace - this cluster's lookup group, e.g. gs-aws-env4
#   $3  service.name      - e.g. gigaspaces
#
# Idempotent: rewrites its own managed block rather than appending a new one,
# so repeated installs cannot accumulate duplicate exports.

set -u

TARGET="${1:-}"
OTEL_NS="${2:-}"
OTEL_SVC="${3:-}"

BEGIN_MARK="# --- BEGIN otel identity (managed by ODSX) ---"
END_MARK="# --- END otel identity ---"

fail() { echo "Error: $*" >&2; exit 1; }

# validate_nonempty_paths() comes from lib_app_config.sh, which
# build_remote_bash_cmd prepends. Guards the sed -i calls below from running
# against an empty path.
if declare -F validate_nonempty_paths >/dev/null 2>&1; then
    validate_nonempty_paths TARGET
else
    [ -n "$TARGET" ] || fail "no target file given"
fi

[ -n "$OTEL_NS" ]  || fail "no service.namespace given"
[ -n "$OTEL_SVC" ] || fail "no service.name given"
[ -f "$TARGET" ]   || fail "$TARGET does not exist"
[ -w "$TARGET" ]   || fail "$TARGET is not writable by $(id -un)"

# OTEL_RESOURCE_ATTRIBUTES is a comma-separated k=v list, so a comma or an '='
# inside a value silently splits it into bogus attributes; whitespace would
# break the export line itself. Reject rather than emit something subtly wrong.
case "$OTEL_NS$OTEL_SVC" in
    *,*)           fail "namespace/service must not contain a comma: '$OTEL_NS' '$OTEL_SVC'" ;;
    *=*)           fail "namespace/service must not contain '=': '$OTEL_NS' '$OTEL_SVC'" ;;
    *[[:space:]]*) fail "namespace/service must not contain whitespace: '$OTEL_NS' '$OTEL_SVC'" ;;
esac

# Rebuild the file in a temp copy, validate it, and only then write it back.
# A bad edit here would stop every GigaSpaces JVM on the host from starting, so
# the real file must never be in an unvalidated state.
TMP=$(mktemp "${TMPDIR:-/tmp}/setenv-overrides.XXXXXX") || fail "cannot create a temp file"
trap 'rm -f "$TMP"' EXIT

# Strip any previous managed block before re-appending, so the file cannot grow
# on every install. The BEGIN marker is matched on its prefix only: the
# standalone skill script writes the same markers with a different
# parenthetical, and the two must not stack up. Stray exports outside a block
# are dropped too - depending on their position they would otherwise override
# ours. Trailing blank lines are trimmed so repeated runs cannot accumulate
# them. awk, not `sed -i`: BSD sed needs an argument for -i, and sed -i also
# replaces the file's inode, which would change its owner to whoever runs the
# install.
awk '
    /^[[:space:]]*# --- BEGIN otel identity/                   { skip = 1; next }
    /^[[:space:]]*# --- END otel identity/                     { skip = 0; next }
    skip                                                       { next }
    /^[[:space:]]*export[[:space:]]+OTEL_SERVICE_NAME=/        { next }
    /^[[:space:]]*export[[:space:]]+OTEL_RESOURCE_ATTRIBUTES=/ { next }
    { keep[++n] = $0; if ($0 ~ /[^[:space:]]/) last = n }
    END { for (i = 1; i <= last; i++) print keep[i] }
' "$TARGET" > "$TMP" || fail "could not filter $TARGET"

{
    echo ""
    echo "$BEGIN_MARK"
    echo "# OTel resource identity -> Prometheus job/instance labels."
    echo "# service.namespace is this cluster's GigaSpaces lookup group, which"
    echo "# already uniquely names the grid, so the job label cannot drift from"
    echo "# the cluster it labels."
    echo "export OTEL_SERVICE_NAME=$OTEL_SVC"
    echo "export OTEL_RESOURCE_ATTRIBUTES=\"service.namespace=$OTEL_NS\""
    echo "$END_MARK"
} >> "$TMP"

# Prove the candidate parses and carries exactly the two exports BEFORE it
# replaces the live file.
bash -n "$TMP" || fail "generated file has a syntax error - $TARGET left untouched"
n=$(grep -c '^export[[:space:]]*OTEL_' "$TMP")
[ "$n" -eq 2 ] || fail "expected 2 OTEL_ exports, generated $n - $TARGET left untouched"

# Redirect rather than mv/sed -i: truncating the existing file keeps its inode,
# owner and mode, which matters where the tree is chowned to an applicative
# user after install.
cat "$TMP" > "$TARGET" || fail "could not write $TARGET"

n=$(grep -c '^export[[:space:]]*OTEL_' "$TARGET")
[ "$n" -eq 2 ] || fail "$TARGET has $n OTEL_ exports after the write, expected 2"

echo "otel identity set in $TARGET : service.name=$OTEL_SVC service.namespace=$OTEL_NS"
