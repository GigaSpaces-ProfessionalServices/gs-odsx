# Scripts directory — operational deep-dives

This file is auto-loaded when working in `scripts/`. Architectural context and project-wide conventions are in the root `CLAUDE.md` (one level up). This file holds the step-by-step walkthroughs for the setup scripts and standalone third-party control scripts — content that's load-bearing when editing those scripts but noise during higher-level work.

## Setup scripts (split by privilege level)

Setup is split into two scripts. Both are idempotent and safe to re-run.

**Typical workflow:**
1. `user-setup.sh -d /gigashare -u gsods -tar /path/gigashare.tgz` — extract tgz, create dirs, local setup
2. `root-setup.sh -d /gigashare` — user creation, NFS, sudoers, parent-dir chown (requires extracted gigashare from step 1)
3. `user-setup.sh -d /gigashare -u gsods` — re-run to deploy SSH keys and configure remote hosts

### `scripts/user-setup.sh` — run as the app user on the pivot
**Usage**: `user-setup.sh -d <gigashare dir> -u <username> [-tar <gigashare.tgz>] [--overwrite]`

The main setup script. Handles gigashare extraction, directory creation, SSH keys, user environment, GigaSpaces installation, and Python dependencies. The `-u` flag makes the username configurable (e.g. `gsods`, `sods`). The script validates it's running as that user.

On the first run (before `root-setup.sh`), remote host steps are skipped gracefully — the script detects unreachable hosts and prints a message to re-run after `root-setup.sh`.

Steps performed:
1. **Gigashare extraction** (if `-tar` given): extracts tgz into `-d` dir — skips if dir is not empty (or re-extracts with `--overwrite`)
2. **Giga directories**: Creates `$GIGA_PATH`, `$GIGA_SHARE`, `$GIGA_LOG`, `$GIGA_DATA`, `$GIGA_WORK`, `$GIGA_PATH/bin` — no chown needed (app user owns them by creation). `$GIGA_INFLUX` is not created — it belongs to the `influxdb` system user.
3. **SQLite copy**: Copies `$GIGA_SHARE/current/sqlite/*` to `$GIGA_WORK/sqlite/` — skips if not empty (or overwrites with `--overwrite`)
4. **Staged CEF logging config**: rewrites the `com.gs.CEFRollingFileHandler.filename-pattern` in `$GIGA_SHARE/current/gs/config/log/xap_logging.properties` and `.cef` to the `@GIGALOGPATH@` placeholder, by calling `configure_cef_logging.sh --pattern-only`. The shipped files hardcode `/gigalogs/CEF`, which no app user can create where `app.gigalog.path` differs. The placeholder — not this pivot's own log root — keeps `current/` valid for every cluster reading the same shared tree; `configureCefLogging()` resolves it per host at install. **Always runs** (idempotent and corrective, so not gated on `--overwrite`), and is placed before the steps that can `exit 1` on a missing prerequisite. No-ops on `.without-cef`, whose `handlers=` line does not enable CEF.
5. **SSH key generation**: Generates ed25519 key in `~/.ssh/` — skips if exists
6. **SSH config**: Creates `~/.ssh/config` — skips if exists (or overwrites with `--overwrite`)
7. **SSH key deployment**: Deploys pubkey to each remote host via SSH. If a host is unreachable (user not yet created by `root-setup.sh`), skips with a warning.
8. **Local directories**: Creates `~/.config/systemd/user/`
9. **nofile limits**: Sets `ulimit -Sn` in `~/.bashrc` and `DefaultLimitNOFILE` in `~/.config/systemd/user.conf` (RHEL 9 default hard limit of 524288 is sufficient — no `/etc/security/limits.conf` needed)
10. **`.bashrc` environment** (each line guarded by `grep -q`):
   - `ENV_CONFIG`, `PYTHONPATH`, `ODSXARTIFACTS`, `XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS`
   - Aliases (`odsx`), `GS_HOME`, `PATH` (with `auto_odsx`, `utils`), argcomplete
11. **Remote hosts** (SSH as the app user — skipped if unreachable):
    - Creates giga directories (`$GIGA_PATH`, `$GIGA_LOG`, `$GIGA_DATA`, `$GIGA_WORK`, `$GIGA_PATH/bin`)
    - Creates `~/.config/systemd/user/`
    - Sets nofile limits (`.bashrc` + `systemd/user.conf`)
    - Sets `ENV_CONFIG`, `PYTHONPATH`, `XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS` in `~/.bashrc`
12. **GigaSpaces install** (idempotent, requires `yq` and `unzip`):
    - Finds latest `gigaspaces-smart*.zip` in `$GIGA_PATH` — exits with error if none found
    - Copies zip to `$GIGA_SHARE/current/gs/` — skips if already present
    - Unzips into `$GIGA_PATH` — skips if extracted dir exists
    - Creates symlink `gigaspaces-smart-ods -> <extracted dir>` via `ln -snf`
    - **Always** refreshes `GS_MANAGER_SERVERS` in `setenv-overrides.sh` from `host.yaml`
13. **Python dependencies**: offline from `$GIGA_SHARE/current/python/` if present, otherwise from PyPI

### `scripts/root-setup.sh` — run once as root on the pivot
**Usage**: `root-setup.sh -d <gigashare dir>`

Lightweight root-only script. Requires gigashare to be already extracted (by `user-setup.sh -tar` or manually) so that `app.config` and `host.yaml` are readable.

Steps performed:
1. Validates root, reads `app.config` and `host.yaml` from `<gigashare dir>/env_config/`. Reads all 6 path roots and the app user.
2. **Pivot**: Creates app user (if not exists), enables linger, creates `/etc/sudoers.d/odsx-monitoring`, sets `ENV_CONFIG`/`PYTHONPATH`/`ODSXARTIFACTS` in `/root/.bashrc`
3. **NFS server**: Installs `nfs-utils`, adds per-host export entries, enables `nfs-server`
4. **Per-remote-host loop** (via SSH as root):
   - Creates app user, enables linger
   - **Path-root parent prep**: For each unique parent dir of the 6 path roots (computed via `dirname`, deduped, `/` skipped), runs `mkdir -p <parent>` and `chown -R $APP_USER:$APP_USER <parent>`. This is what lets `user-setup.sh` (running as the app user) later mkdir leaf dirs under non-default roots like `/v/campus/vi/cs/eqrisk/josroden/`. **Recursive chown is intentional** — assumes the parent dir is exclusively for ODSX content. Default `/giga`-style roots have parent `/`, which is skipped.
   - Creates `$GIGA_SHARE` mount point + `chown gsods`, installs `nfs-utils`, adds fstab entry, mounts NFS

## Standalone Control Scripts (root-only, outside ODSX menu)

These scripts perform install/remove operations directly on target hosts, bypassing the ODSX interactive menu. They run as **root** and are designed for initial cluster setup or one-off maintenance. gsods only has `sudo` permissions for start/stop/enable/disable/restart of these third-party services via the sudoers whitelist.

### `scripts/influxdbctl.sh` — InfluxDB install/remove on the local host
**Usage**: `influxdbctl.sh {-i|-r|-h} [--purge]`

Run directly on the InfluxDB host (no SSH). Reads data directory from `app.gigainfluxdata.path` in `$ENV_CONFIG/app.config` (no `-d` override — edit `app.config` to change). Atomic steps for `-i`:
1. Guard: `rpm -q influxdb` — refuses to install if already present (must `-r` first)
2. Locate RPM in `$ODSXARTIFACTS/influx/*.rpm`
3. `yum localinstall`
4. `sed` rewrite default data path → `$dir/influxdb/` in `/etc/influxdb/influxdb.conf`
5. `mkdir -p $dir/influxdb/{data,meta,wal}`, `chmod 755`
6. Comment out stock `[data]` block, append template **parameterized** via `sed` so `$dir` takes effect (marker-bounded `# Influxdb config START/END` for idempotency — strip previous block before appending)
7. `chown -R influxdb:influxdb $dir`
8. `systemctl enable/restart influxdb`, poll for active
9. `influx -execute 'CREATE DATABASE mydb'` (idempotent)

**Fixes over original ODSX `servers_influxdb_install.sh`**:
- Template config is parameterized (original hardcoded `/gigainfluxdata`, ignoring operator's data dir choice)
- `CREATE DATABASE` actually executes (original typed it to the shell, not piped to influx)
- Config append is idempotent (original stacked duplicate blocks on re-run)
- `chmod 755` instead of `chmod 777`
- No `install.tar` upload/extraction (was dead weight for influxdb — the RPM and config come from `$ODSXARTIFACTS`)

Remove (`-r`): stop, disable, `yum erase`, `rm -rf /etc/influxdb/`. Data directory left intact unless `--purge` is passed.

**Install-status check** (`utils/ods_list.py`): `isInstalledAndGetVersionInflux()` was checking `~/.config/systemd/user/influx*` (wrong — InfluxDB uses system-level systemd, not `--user`). Fixed to `rpm -q influxdb && ls /usr/lib/systemd/system/influxdb.service` — both must succeed for `Installed=Yes`.

### `scripts/telegrafctl.sh` — Telegraf install/remove on all cluster hosts
**Usage**: `telegrafctl.sh {-i|-r|-h} [--purge]`

Run as root on the pivot. SSHes to every manager, space, and pivot host listed in `host.yaml`. Requires `yq` for YAML parsing. DI and NB roles are out of scope.

Atomic steps for `-i` (per host):
1. Build full config locally: embedded base config (agent + system inputs + InfluxDB output) + role-specific appendix from `$ODSXARTIFACTS/telegraf/config/{pivot,space}/` — appended **verbatim**, no path rewriting
2. Pipe config to remote host → `/etc/telegraf/telegraf.conf` (full overwrite each run — inherently idempotent)
3. SSH: `yum localinstall` RPM from NFS share (skip if already installed)
4. SSH: copy role-specific scripts to `/usr/local/bin/` (pivot gets `pu_status.sh`, `space-status.gc-state.sh`; space gets `telegraf_wal-size.sh`)
5. SSH: create `/usr/local/bin/gc-state.sh` → `space-status.gc-state.sh` symlink (artifact name doesn't match config reference)
6. SSH: `chown -R telegraf:telegraf /etc/telegraf`, `systemctl enable/restart telegraf`, poll for active

**Why `/usr/local/bin/` and not `/giga/bin/`**: the telegraf daemon runs as its own `telegraf` user (created by the RPM postinstall), not as gsods or root. It has no read/exec access to gsods-owned paths like `/giga/bin/`. `telegrafctl.sh` runs as root on the remote host (via SSH), so writing to `/usr/local/bin/` is not a privilege issue — and the shipped `pivot.telegraf.conf` / `space.telegraf.conf` already reference `/usr/local/bin/` paths, so no rewriting is needed.

Role-to-config mapping:

| Role | Base config | Custom config | Custom scripts |
|---|---|---|---|
| manager | yes | — | — |
| space | yes | `space.telegraf.conf` | `telegraf_wal-size.sh` |
| pivot | yes | `pivot.telegraf.conf` | `pu_status.sh`, `space-status.gc-state.sh` |

Remove (`-r`): SSHes to each host — stop, disable, `yum erase`, `rm -rf /etc/telegraf/`. With `--purge`: also deletes custom scripts from `/usr/local/bin/` (`pu_status.sh`, `space-status.gc-state.sh`, `gc-state.sh`, `telegraf_wal-size.sh`).

**Removed artifacts** (not used in this gsods variant): `test.sh` (hardcoded customer-specific DB2 table names, old `/dbagiga/` paths), `pipeline-state.sh` (depended on `test.sh` for DB2 pipeline timestamp), `shob_status.sh` (SHOB freshness — pipelines/DI not in scope). Also removed: `readFromShob-1.0.0.jar` (Java JAR used by `test.sh`/`shob_status.sh`). The `pipeline-state.sh` had a graceful fallback when `test.sh` was missing, but is itself removed since pipelines are out of scope.

**Artifacts location**: `$ODSXARTIFACTS/telegraf/` on NFS share:
```
telegraf/
  telegraf-*.rpm
  config/pivot/pivot.telegraf.conf
  config/space/space.telegraf.conf
  scripts/pivot/pu_status.sh
  scripts/pivot/space-status.gc-state.sh
  scripts/space/telegraf_wal-size.sh
```
