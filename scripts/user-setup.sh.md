• user-setup.sh is the non-root/app-user setup script for an ODSX installation. It is meant to run on the pivot machine as the
  application user, before and after root-setup.sh.

  Typical flow:

  ./user-setup.sh -d /gigashare -tar /path/gigashare.tgz
  sudo ./root-setup.sh -d /gigashare
  ./user-setup.sh -d /gigashare

  Inputs
  Usage is defined at user-setup.sh:31:

  ./user-setup.sh -d <gigashare dir> [-u <username>] [-tar <gigashare.tgz>] [--overwrite] [--ksh]

  - -d <dir>: required. Existing gigashare directory.
  - -u <user>: optional. App user. Defaults to the user running the script via id -un.
  - -tar <tgz>: optional. Tarball to extract into the gigashare directory.
  - --overwrite: forces destructive/replace behavior in several places.
  - --ksh: also creates .kshrc from .bashrc.

  Startup Validation
  The script starts with set -e, so most command failures stop execution.

  It validates:

  - -d was provided.
  - The gigashare directory exists.
  - The current Unix user matches -u, or if -u was omitted, matches the default current user.
  - $GIGASHARE_DIR/env_config exists.
  - app.config and host.yaml exist under env_config.

  It sources lib_app_config.sh:1 if present, mainly for read_property.

  Step 1: Gigashare Extraction
  At user-setup.sh:110:

  If -tar is supplied:

  - Verifies the tarball exists and is non-empty.
  - If the gigashare directory is empty, extracts the tarball there.
  - If the directory is non-empty and --overwrite is not set, skips extraction.
  - If --overwrite is set, runs:

  rm -rf "$GIGASHARE_DIR"/*
  tar xzf "$TGZ_FILE" -C "$GIGASHARE_DIR"

  That is the script’s most destructive operation.

  If -tar is not supplied:

  - Empty gigashare: says extraction is skipped and later errors with guidance to extract first.
  - Non-empty gigashare: silently treats it as already staged and does not mention -tar.

  Config Loading
  At user-setup.sh:137, it expects:

  <gigashare>/env_config/app.config
  <gigashare>/env_config/host.yaml

  It reads these app properties:

  - app.giga.path
  - app.gigashare.path
  - app.gigalog.path
  - app.gigadata.path
  - app.gigawork.path
  - app.gigainfluxdata.path
  - app.user.nofile.limit, defaulting to 50000

  It exits if any required path property is empty.

  Host Detection
  At user-setup.sh:176:

  - Parses host.yaml for lines like host1: <ip>, host2: <ip>.
  - Gets the pivot IP with hostname -I | awk '{print $1}'.
  - Treats every parsed host except the pivot IP as a remote host.

  Then it prints a setup banner showing app user, pivot IP, giga path, gigashare, nofile limit, and remote hosts.

  Step 2: Create Local Giga Directories
  At user-setup.sh:197, it creates:

  - $GIGA_PATH
  - $GIGA_SHARE
  - $GIGA_LOG
  - $GIGA_DATA
  - $GIGA_WORK
  - $GIGA_PATH/bin

  It also creates/touches:

  $GIGA_LOG/odsx.log

  Step 3: SQLite Files
  At user-setup.sh:204:

  - Creates $GIGA_WORK/sqlite.
  - If that directory is empty, copies files from:

  $GIGA_SHARE/current/sqlite/*

  - If destination is non-empty, skips copy.
  - With --overwrite, copies again over existing files.

  Step 4: SSH Key
  At user-setup.sh:221:

  - Creates ~/.ssh.
  - Sets it to 700.
  - Generates ~/.ssh/id_ed25519 with no passphrase if it does not already exist.

  It does not overwrite an existing SSH key.

  Step 5: SSH Config
  At user-setup.sh:233:

  Creates ~/.ssh/config if missing, or overwrites it with --overwrite.

  The config disables strict host key checking:

  Host *
      StrictHostKeyChecking no
      UserKnownHostsFile /dev/null
      ServerAliveInterval 30
      ServerAliveCountMax 3
      ConnectTimeout 10
      LogLevel ERROR

  This makes automation easier, but weakens SSH host identity checking.

  Step 6: SSH Key Deployment
  At user-setup.sh:255:

  For each remote host:

  - Tries passwordless/batch SSH.
  - If SSH works, checks whether the local public key is already in remote ~/.ssh/authorized_keys.
  - If absent, appends it and fixes permissions.
  - If SSH does not work, it skips that host and tells you to run root-setup.sh first, then rerun this script.

  This is why the script is intended to run twice: before root setup for pivot prep, and after root setup for remote user SSH/config.

  Step 7: Local Systemd User Directory
  At user-setup.sh:277:

  Creates:

  ~/.config/systemd/user/

  Step 8: File Descriptor Limits
  At user-setup.sh:282:

  - Adds this to ~/.bashrc if no existing ulimit -Sn line is found:

  ulimit -Sn <NOFILE_LIMIT>

  - Writes:

  ~/.config/systemd/user.conf

  [Manager]
  DefaultLimitNOFILE=<NOFILE_LIMIT>

  This affects user-level systemd services.

  Step 9: Local Shell Environment
  At user-setup.sh:297, it appends missing exports to ~/.bashrc:

  export ENV_CONFIG=<gigashare>/env_config
  export GIGA_PATH=<from app.config>
  export GIGA_SHARE=<from app.config>
  export GIGA_LOG=<from app.config>
  export GIGA_DATA=<from app.config>
  export GIGA_WORK=<from app.config>
  export GIGA_INFLUX=<from app.config>
  export PYTHONPATH=$GIGA_PATH/gs-odsx
  export ODSXARTIFACTS=$GIGA_SHARE/current/
  export XDG_RUNTIME_DIR=/run/user/<uid>
  export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/<uid>/bus
  export GS_HOME=$GIGA_PATH/gigaspaces-smart-ods

  It also adds:

  [ -f ~/.aliases ] && source ~/.aliases
  alias odsx='cd $GIGA_PATH/gs-odsx ; ./odsx.py'
  export PATH=$PATH:$HOME/bin:$GIGA_PATH/utils/auto_odsx:$GIGA_PATH/utils:/opt/maven/bin
  eval "$(register-python-argcomplete odsx.py)"

  Most of these are guarded by grep, so reruns usually do not duplicate lines.

  Optional .kshrc Creation
  At user-setup.sh:365:

  If --ksh is passed:

  - Creates ~/.kshrc from ~/.bashrc.
  - Removes the bash-only register-python-argcomplete line.
  - Converts source X to POSIX/ksh-compatible . X.
  - Skips if .kshrc exists, unless --overwrite is also passed.

  Step 10: Remote Host Configuration
  At user-setup.sh:381:

  For every reachable remote host, it runs an inline bash script over SSH.

  On each remote host it:

  - Creates $GIGA_PATH, $GIGA_LOG, $GIGA_DATA, $GIGA_WORK.
  - Creates $GIGA_PATH/bin.
  - Creates ~/.config/systemd/user/.
  - Adds ulimit -Sn <limit> to remote ~/.bashrc if absent.
  - Writes remote ~/.config/systemd/user.conf.
  - Adds the same core env vars to remote ~/.bashrc.
  - Optionally creates remote .kshrc if --ksh was passed.

  Remote hosts that fail SSH are skipped, and the script prints a rerun command.

  Step 11: GigaSpaces Installation
  At user-setup.sh:483:

  First it requires local commands:

  - yq
  - unzip

  Then it:

  - Finds the newest zip matching:

  $GIGA_PATH/gigaspaces-smart*.zip

  - Checks existing GigaSpaces zips in:

  $GIGA_SHARE/current/gs/

  - If --overwrite is given, deletes all existing gigaspaces-smart*.zip files there and copies the newest zip from $GIGA_PATH.
  - If more than one gigaspaces-smart*.zip file exists there, treats it like --overwrite: deletes all and copies the newest zip from $GIGA_PATH.
  - If exactly one gigaspaces-smart*.zip file exists there and its filename matches the newest zip from $GIGA_PATH, leaves it in place and does not copy.
  - If exactly one gigaspaces-smart*.zip file exists there but it does not match the newest zip from $GIGA_PATH, replaces it with the newest zip.
  - If no matching zip exists there, copies the newest zip from $GIGA_PATH.
  - Does not create $GIGA_SHARE/current/gs; that directory is expected to already exist.

  - Unzips it into $GIGA_PATH if not already extracted.
  - Creates/updates this symlink:

  $GIGA_PATH/gigaspaces-smart-ods -> $GIGA_PATH/<extracted zip dir>

  Then it configures GigaSpaces managers:

  - Reads manager IPs from host.yaml using:

  yq -r '.servers.manager[]' "$HOST_YAML"

  - Joins them with commas.
  - Removes any existing export GS_MANAGER_SERVERS=... line from:

  $GIGA_PATH/gigaspaces-smart-ods/bin/setenv-overrides.sh

  - Appends the fresh value.

  Step 12: Python Dependencies
  At user-setup.sh:550:

  If offline Python packages exist under:

  $GIGA_SHARE/current/python/

  it installs with:

  pip3 install --no-index --find-links="$GIGA_SHARE/current/python" \
    -r "$GIGA_PATH/gs-odsx/scripts/requirements.txt"

  Otherwise it installs from PyPI:

  pip3 install -r "$GIGA_PATH/gs-odsx/scripts/requirements.txt"

  End State
  On success, the script tells the user to reload shell config:

  source ~/.bashrc

  and run ODSX:

  cd $GIGA_PATH/gs-odsx
  ./odsx.py

  Important Side Effects
  The script modifies local user files:

  - ~/.bashrc
  - optionally ~/.kshrc
  - ~/.ssh/id_ed25519
  - ~/.ssh/config
  - ~/.config/systemd/user.conf

  It may also modify remote user files on reachable hosts.

  It writes/copies content under the configured ODSX paths, installs Python packages with pip3, unzips GigaSpaces, and updates
  GigaSpaces setenv-overrides.sh.

  The main destructive path is --overwrite with -tar, which clears contents directly under $GIGASHARE_DIR.
