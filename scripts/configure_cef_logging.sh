#!/usr/bin/env bash
# configure_cef_logging.sh - make CEF (Common Event Format) audit logging
# actually work on this host: put the handler class on the JVM boot classpath
# and point it at this environment's log root.
#
# WHY THIS EXISTS
#   xap_logging.properties names com.gs.CEFRollingFileHandler in its
#   `handlers=` line, but that class ships in CEFLogger-1.0-SNAPSHOT.jar, which
#   lives only on the shared filesystem. java.util.logging resolves handler
#   classes with the *application* classloader at LogManager init, so unless the
#   jar is on the JVM's -classpath every GigaSpaces process on the host prints
#
#       Can't load log handler "com.gs.CEFRollingFileHandler"
#       java.lang.ClassNotFoundException: com.gs.CEFRollingFileHandler
#
#   and silently logs no CEF at all. Only the security install flows ever copied
#   the jar, so every non-security cluster hit this.
#
#   lib/required/ is the right target: GsPremiumCommandFactory appends any jar
#   it does not recognise there to the boot classpath it emits, and the GSA,
#   GSM, LUS and every GSC share that classpath. GS_CLASSPATH_EXT is NOT an
#   alternative - setenv-overrides.sh advertises it, but 17.3.0 emits an
#   identical service-grid command with and without it.
#
#   The shipped filename-pattern is a hardcoded /gigalogs/CEF literal, which is
#   wrong on any cluster whose app.gigalog.path is not /gigalogs - the handler
#   then fails with "Failed to create directories: /gigalogs/CEF". This script
#   rewrites that one property to the resolved log root.
#
#   Do NOT add a mkdir for the CEF directory: com.gigaspaces.logger.
#   RollingFileHandler.createParentDirectories() creates the leaf itself. What
#   it cannot do is create a parent it has no permission for, which is the real
#   failure the rewrite below prevents.
#
# Invoked from utils/ods_list.py:configureCefLogging() via
# build_remote_bash_cmd(), i.e. piped to `bash -s <cfg> <jar> <dir> <logroot>`
# on the remote host with scripts/lib_app_config.sh prepended. Not run directly.
#
# Args:
#   $1  absolute path of the deployed xap_logging.properties to edit
#   $2  absolute path of the CEF jar to deploy (on the shared filesystem)
#   $3  directory to deploy the jar into, i.e. <gs home>/lib/required/
#   $4  this environment's log root, i.e. app.gigalog.path
#
# Idempotent: a no-op once the jar matches and the pattern is already resolved,
# so repeated installs cannot duplicate anything. Exits 0 doing nothing when the
# deployed config does not enable CEF.

set -u

CFG="${1:-}"
JAR_SRC="${2:-}"
JAR_DIR="${3:-}"
LOG_ROOT="${4:-}"

PROP="com.gs.CEFRollingFileHandler.filename-pattern"
CEF_BASENAME="{date,yyyy-MM-dd~HH.mm}-CEF-gigaspaces-{service}-{host}-{pid}.log"

fail() { echo "Error: $*" >&2; exit 1; }

# Value of an active (uncommented) property, or "" when it has none.
# Matched literally rather than with a regex: the key is full of dots, and the
# value is full of braces and commas, so treating either as a pattern invites
# a subtly wrong match.
active_prop_value() {
    awk -v prop="$1" '
        {
            line = $0
            sub(/^[[:space:]]+/, "", line)
            if (index(line, prop) != 1) next
            rest = substr(line, length(prop) + 1)
            sub(/^[[:space:]]+/, "", rest)
            if (index(rest, "=") != 1) next
            sub(/^=[[:space:]]*/, "", rest)
            sub(/[[:space:]]+$/, "", rest)
            print rest
        }
    ' "$2"
}

# validate_nonempty_paths() comes from lib_app_config.sh, which
# build_remote_bash_cmd prepends. Guards the writes below from running against
# an empty path.
if declare -F validate_nonempty_paths >/dev/null 2>&1; then
    validate_nonempty_paths CFG JAR_SRC JAR_DIR LOG_ROOT
else
    for _v in CFG JAR_SRC JAR_DIR LOG_ROOT; do
        [ -n "${!_v}" ] || fail "no $_v given"
    done
fi

[ -f "$CFG" ] || fail "$CFG does not exist"

# Nothing to do unless an *active* handlers line asks for the CEF handler. This
# keeps the jar off clusters that deliberately run the without-cef config, and
# makes the script safe to call unconditionally from every install flow.
case "$(active_prop_value handlers "$CFG")" in
    *com.gs.CEFRollingFileHandler*) ;;
    *) echo "CEF logging is not enabled in $CFG - nothing to do"; exit 0 ;;
esac

# ---------------------------------------------------------------------------
# 1. Put the handler class on the boot classpath.
# ---------------------------------------------------------------------------
[ -f "$JAR_SRC" ] || fail "CEF jar $JAR_SRC not found - stage it on the shared filesystem first"
[ -d "$JAR_DIR" ] || fail "$JAR_DIR does not exist - is GigaSpaces installed on this host?"
[ -w "$JAR_DIR" ] || fail "$JAR_DIR is not writable by $(id -un)"

# app.cefLogging.jar.target conventionally ends in "/", so strip it rather than
# emit lib/required//CEFLogger... in every log line.
JAR_DIR="${JAR_DIR%/}"
JAR_DST="$JAR_DIR/$(basename "$JAR_SRC")"
if [ -f "$JAR_DST" ] && cmp -s "$JAR_SRC" "$JAR_DST"; then
    echo "CEF jar already current at $JAR_DST"
else
    # Copy to a temp file in the SAME directory and rename, rather than writing
    # over $JAR_DST in place: a running JVM holds the old jar open, and
    # truncating it under a live process corrupts its view of the archive. The
    # rename is atomic and gives the new file its own inode, so running JVMs
    # keep the jar they started with until they restart.
    TMP_JAR=$(mktemp "$JAR_DIR/.cef-jar.XXXXXX") || fail "cannot create a temp file in $JAR_DIR"
    trap 'rm -f "$TMP_JAR"' EXIT
    cat "$JAR_SRC" > "$TMP_JAR"    || fail "could not copy $JAR_SRC"
    chmod 644 "$TMP_JAR"           || fail "could not chmod $TMP_JAR"
    cmp -s "$JAR_SRC" "$TMP_JAR"   || fail "copy of $JAR_SRC is truncated - $JAR_DST left untouched"
    mv -f "$TMP_JAR" "$JAR_DST"    || fail "could not install $JAR_DST"
    trap - EXIT
    echo "CEF jar deployed to $JAR_DST"
fi

# ---------------------------------------------------------------------------
# 2. Point the handler at this environment's log root.
# ---------------------------------------------------------------------------
WANT="$LOG_ROOT/CEF/$CEF_BASENAME"

if [ "$(active_prop_value "$PROP" "$CFG")" = "$WANT" ]; then
    echo "$PROP already set to $WANT in $CFG"
    exit 0
fi

[ -w "$CFG" ] || fail "$CFG is not writable by $(id -un)"

# Rebuild in a temp copy, validate, and only then write back. A bad edit here
# would stop every GigaSpaces JVM on the host from initialising its logging, so
# the real file must never be left in an unvalidated state.
TMP=$(mktemp "${TMPDIR:-/tmp}/xap_logging.XXXXXX") || fail "cannot create a temp file"
trap 'rm -f "$TMP"' EXIT

# Replace the property wherever it is defined, and append it if it was only ever
# present commented out. Only this one line is touched - everything else,
# including comments and the other handlers' settings, is passed through
# verbatim.
awk -v prop="$PROP" -v want="$WANT" '
    {
        line = $0
        sub(/^[[:space:]]+/, "", line)
        if (index(line, prop) == 1) {
            rest = substr(line, length(prop) + 1)
            sub(/^[[:space:]]+/, "", rest)
            if (index(rest, "=") == 1) {
                if (!done) { print prop " = " want; done = 1 }
                next
            }
        }
        print
    }
    END { if (!done) print prop " = " want }
' "$CFG" > "$TMP" || fail "could not rewrite $CFG"

n=$(active_prop_value "$PROP" "$TMP" | wc -l)
[ "$n" -eq 1 ] || fail "expected 1 active $PROP line, generated $n - $CFG left untouched"
[ "$(active_prop_value "$PROP" "$TMP")" = "$WANT" ] \
    || fail "generated $PROP does not match the intended value - $CFG left untouched"

# Redirect rather than mv: truncating the existing file keeps its inode, owner
# and mode, which matters where the tree is chowned to an applicative user
# after install. Safe for a properties file - java.util.logging reads it once,
# at JVM startup.
cat "$TMP" > "$CFG" || fail "could not write $CFG"

echo "$PROP set to $WANT in $CFG"
echo "note: the CEF directory is created by RollingFileHandler on first write"
