# Project: ODSX (gsods / non-root variant)

ODSX is a menu-driven CLI administration tool for managing GigaSpaces XAP/Smart ODS clusters. It is built primarily in Python 3 with Bash scripts for remote execution. The source repo is `gs-odsx`.

**This project (`odsx-gsods`) focuses on running ODSX as the non-root `gsods` user** on branch `gs-odsx-non-root`. The sibling project `odsx` covers the original root-based deployment. Changes specific to non-root operation (setup scripts, NFS sharing, `systemctl --user`, SSH user centralization, prerequisite-check cleanup, etc.) live here.

## Core Principles
**IMPORTANT**: Whenever you write code, it MUST follow SOLID design principles. Never write code that violates these principles. If you do, you will be asked to refactor it.
- "Any operation that deletes data must require explicit confirmation."
- "Never log secrets (tokens, passwords, key material)."

## Architecture Overview

### Entry Point
- `odsx.py` is the main entry point. It displays an ASCII logo via `pyfiglet`, reads the security profile from `app.config`, discovers cluster hosts from `host.yaml`, and renders a menu tree driven by CSV files.

### Menu-Driven Design
The core pattern uses CSV files as menu definitions with a naming convention that maps directly to script files:
- **Menu path**: `MENU -> SERVERS -> MANAGER -> LIST`
- **CSV file**: `csv/menu_servers_manager.csv`
- **Script**: `scripts/odsx_servers_manager_list.py`
- **Security variant**: `scripts/odsx_security_servers_manager_list.py`

The main menu (`csv/menu.csv`) offers: Settings, Servers, Data Engine, Space, Object, Monitors, Data Validator, Tiered Storage, Utilities.

### Remote Execution Pattern
1. A Python script reads config and determines the target host(s).
2. It constructs an SSH command (with or without PEM key based on `cluster.usingPemFile` in `app.config`).
3. It either pipes a Bash script to the remote host (`ssh host bash < script.sh params`) or executes commands directly.
4. `ThreadPoolExecutor` is used for parallel operations across multiple nodes.

## Environment Variables
Set by `scripts/user-setup.sh` (in each app user's `.bashrc`) and required at runtime:
```
PYTHONPATH=<project_home_dir>            # e.g. /giga/gs-odsx
ODSXARTIFACTS=<app.gigashare.path>/current/   # e.g. /gigashare/current/
ENV_CONFIG=<app.gigashare.path>/env_config/   # e.g. /gigashare/env_config/
```
The literal values are derived from `app.gigashare.path` in `app.config` at setup time. With an exotic config like `app.gigashare.path=/v/campus/vi/cs/eqrisk/josroden/gigashare`, `.bashrc` will export the corresponding paths.

**Important**: `ENV_CONFIG` must be set not only on the pivot machine but also on all remote target servers (managers, spaces, etc.). The bash scripts executed via SSH on those servers (e.g., `servers_manager_remove.sh`) read `$ENV_CONFIG` to locate `app.config`. If it is not set on the remote host, the script will fail with `"Error: is not set"`.

## Directory Structure

### Repository Layout
```
gs-odsx/
  odsx.py                  -- Main entry point
  config/                  -- Config file templates (app.config, app.yaml, host.yaml, cluster.config, etc.)
  csv/                     -- 146 CSV menu definition files (backbone of the UI)
  scripts/                 -- ~600 Python/Bash operational scripts
  utils/                   -- ~30 shared utility modules (SSH, SCP, config readers, validators)
  install/                 -- systemd service files (gs.service, gsa.service, gsc.service, etc.)
  systemServices/          -- Additional service definitions (health check, catalogue, retention, object mgmt)
  node_rebalancer/         -- Java-based recovery service (odsxrecovery.service)
  unit-test/               -- 12 test files
  backup/                  -- Cluster config backup snapshots
  logs/                    -- Local log directory (gitignored)
```

### Deployed Filesystem Layout

| Path | Purpose |
|---|---|
| `/giga/` | Base install directory for GigaSpaces and ODSX on each server |
| `/giga/gigaspaces-smart-ods` | Symlink to current GigaSpaces installation (e.g. `-> gigaspaces-smart-cache-enterprise-17.1.5`) |
| `/giga/gigaspaces-smart-ods/bin/` | GS binaries including `gs.sh` for controlling and querying the cluster |
| `/giga/gigaspaces-smart-ods/bin/setenv-overrides.sh` | XAP installation definitions, JVM options, license, manager servers |
| `/gigashare/` | Shared filesystem (NFS/EFS mounted), accessible from all servers |
| `/gigashare/current/` (`$ODSXARTIFACTS`) | Common artifacts for all clusters: GS binaries, JARs, configs, feeder artifacts |
| `/gigashare/env_config/` (`$ENV_CONFIG`) | Per-environment/cluster configs: `app.config`, `host.yaml`, security files |
| `/gigalogs/` | Log files on all servers (including `odsx.log`) |
| `/gigadata/` | Data files on manager and space servers |
| `/gigawork/` | SQLite databases on the pivot machine; data files on space servers |
| `/gigashare/current/gs/` | GS installation zip (e.g. `gigaspaces-smart-cache-enterprise-17.1.5.zip`) |
| `/gigashare/current/gs/16.4/` | Legacy v16.4 binary for running the old WebUI (`gs-webui.sh`) since v17.1.x replaced it with ops-ui |

## Configuration Files

### `app.config` (at `$ENV_CONFIG/app.config`)
The central configuration hub. A flat key=value property file read by `utils/ods_app_config.py` using the `configobj` library. **Duplicate keys will cause a `DuplicateError` at parse time**, crashing any script that imports config (not just the script that reads the duplicate key).

**Path-bearing values use `${app.*.path}` placeholders** that resolve against the 6 path-root keys at the bottom of the file (`app.giga.path`, `app.gigashare.path`, `app.gigalog.path`, `app.gigadata.path`, `app.gigawork.path`, `app.gigainfluxdata.path`). Example: `app.manager.security.config.ldap.target.file=${app.giga.path}/gs_config/ldap-security-config.xml`. Editing one path-root key propagates to every dependent value. See [`${app.*.path}` Placeholder System](#appath-placeholder-system) for details.

Contains:
- **Security profile**: `app.setup.profile=security` (or blank for non-security)
- **Environment**: `app.setup.env=dr` (uncomment for DR; hides DI menu items)
- **PEM file settings**: `cluster.usingPemFile`, `cluster.pemFile` for SSH auth
- **Manager config**: JVM options (separate for security/non-security), GS manager options, NIC address
- **Space config**: GSC count, GSC memory, zones, target directories
- **Data engine configs**: DB2, MSSQL, MySQL, Oracle, Oracle ERP feeders with connection details and batch sizes
- **Tiered storage**: Partitions, zones, deploy/demote timeouts
- **Data integration (DI)**: Kafka/ZooKeeper base paths and ports
- **Monitoring**: Telegraf, Kapacitor, Grafana, InfluxDB settings
- **Vault**: `app.vault.use=true`, vault JAR location, DB location
- **IIDR/CDC**: Access server, Kafka agent, Oracle agent ports and hosts

### `host.yaml` (at `$ENV_CONFIG/host.yaml`)
Defines server roles and their IP addresses. If a role is not in use, its IP is absent. Roles:
- `manager` (typically 3), `space` (typically 2+)
- `dataIntegration`, `dataIntegrationSubscriptionManager`
- `iidrdataIntegration`, `iidrAccessServer`, `iidrKafkaAgent`, `iidrOracleAgent`
- `grafana`, `influxdb`
- `nb_applicative`, `nb_management` (NorthBound)
- `data_validator_server`, `data_validator_agent`
- `pivot` (localhost — the admin/control machine)
- `cockpit`

### `cluster.config` (at `config/cluster.config`)
A JSON file representing runtime cluster state. Auto-generated from `host.yaml` by `discoverHostConfig()` in `utils/ods_cluster_config.py` on each ODSX startup. Uses a lock file mechanism (`cluster.config.lock`) with retry logic to prevent concurrent writes. Tracks all nodes by category: managers, spaces, nb, grafana, influxdb, dataIntegration, iidrdataIntegration, dataValidation, dataEngine, etc. **Node ordering in `cluster.config` (and therefore in ODSX menu tables) preserves the insertion order from `host.yaml`** — SrNo. 1 is always the first host listed under that role in `host.yaml`.

### `dih-package.json` (at `config/dih-package.json`)
Defines downloadable artifacts for DIH installations. Each artifact has an `id`, `url`, and `action` (`"download"`, `"run"`, or `"download_and_run"`). Parsed by `utils/odsx_dih_package.py`. Key artifacts:
- **`xap`**: The GigaSpaces Smart Cache zip (HTTPS URL from S3). Downloaded during manager install to `$ODSXARTIFACTS/gs/`.
- **DI artifacts** (`di-mdm`, `di-processor`, `di-flink`, `di-manager`, `di-subscription-manager`, `di-transformations`): Use `s3://` protocol URLs requiring `boto3`.
- **`kafka`**, **`zookeeper`**: Standard HTTPS downloads from Apache archives.

### `app.yaml` (at `$ODSXARTIFACTS/odsx/app.yaml`)
Defines the artifact-to-filepath mapping for the shared filesystem. Maps artifact names to file paths within `/gigashare/current/` and `/gigashare/env_config/`. Sections cover GS binaries, database feeder JARs (DB2, MSSQL, MySQL, Oracle), Kafka, Telegraf, Kapacitor, security JARs/configs, object management, retention, data validation, and Grafana.

## Key Utility Modules (`utils/`)

| Module | Purpose |
|---|---|
| `ods_app_config.py` | Reads/writes `app.config` (`readValuefromAppConfig()`, `readValueByConfigObj()`) and `app.yaml` (`readValueFromYaml()`). Also exports `expand_path_placeholders()` (resolves `${app.*.path}` in any string) and `render_install_templates()` (in-place placeholder substitution for `install/**/*.{service,yml,yaml}` — called by install scripts before building `install.tar`). |
| `ods_cluster_config.py` | Cluster config management, host discovery via `discoverHostConfig()`, data model classes (~1700 lines). Class hierarchy: `Clusters` -> `Cluster` -> `AllServers` -> `{Managers, Spaces, NB, Grafana, ...}` -> `Node/Host` |
| `ods_ssh.py` | SSH command execution (supports PEM and password-based auth) |
| `ods_scp.py` | SCP file transfer to/from remote hosts |
| `ods_validation.py` | Server status checks, port availability checks |
| `ods_space.py` | Space-related utility functions |
| `ods_list.py` | RPM validation, metrics XML/properties propagation, OTel cluster identity (`configureOtelIdentity()`, `getClusterLookupGroup()`) |
| `odsx_keypress.py` | User input handling with ESC support for menu navigation |
| `odsx_print_tabular_data.py` | Tabular output formatting (uses `tabulate`) |
| `odsx_dataengine_utilities.py` | Data engine utility functions |
| `odsx_db2feeder_utilities.py` | DB2 feeder-specific utilities |
| `odsx_retentionmanager_utilities.py` | Retention manager utilities |
| `odsx_space_shutdown_reload_utilities.py` | Space shutdown/reload orchestration |
| `odsx_vault_cred_details.sh` | Vault password retrieval via Java JAR |
| `odsx_dih_package.py` | Parses `dih-package.json`, downloads artifacts (HTTP and S3 via lazy-loaded `boto3`), supports `download`/`run`/`download_and_run` actions |
| `server_discovery.py` | Server auto-discovery |

## Security Profile

### How It Works
The security profile is determined at startup by reading `app.setup.profile` from `app.config`:
- If `app.setup.profile=security`, the cluster operates in security mode.
- If `app.setup.profile=` (blank), the cluster is non-security.

### Script Routing
`app.security.menu` in `app.config` lists which menu items have security variants: `manager,space,tieredstorage,feeder,mq,object,dataengine`. When the profile is `security`, `odsx.py` replaces `odsx` with `odsx_security` in the script filename. If the security variant doesn't exist, it falls back to the non-security version. CSV menu files also have security variants (e.g. `csv/menu_security_servers_manager.csv`).

### What Security Mode Adds
- JVM options include `-Dcom.gs.security.enabled=true`, `-Dcom.gigaspaces.security.audit.enabled=true`, LDAP truststore settings
- LDAP integration (`ldap-security-config.xml`, Spring Security LDAP JARs)
- Vault integration for password management
- CEF (Common Event Format) audit logging
- Security-specific JARs copied to `/giga/gs_jars/`

## GigaSpaces Version Context
- **Primary version**: GigaSpaces Smart Cache Enterprise **17.1.x**
- **Legacy version**: **16.4.x** (retained solely for the old WebUI which was dropped in v17)
- **Product names**: `gigaspaces-smart-cache-enterprise`, `gigaspaces-smart-ods-enterprise`
- **REST API**: Port **8090**, `/v2/` endpoints (e.g. `http://<manager>:8090/v2/info`)
- **Install target**: `/giga/` with symlink `/giga/gigaspaces-smart-ods -> gigaspaces-smart-cache-enterprise-17.1.x`

## Major Feature Areas

### Server Lifecycle Management
Install, start, stop, restart, rolling restart, upgrade, rollback, and remove operations for managers, spaces, GSCs (GigaSpaces Containers), and processing units.

#### Manager Install Download Flow
1. The Python script (`odsx_servers_manager_install.py`) reads `dih-package.json` to get the XAP artifact URL.
2. It downloads the XAP zip to `$ODSXARTIFACTS/gs/` on the pivot machine (shared filesystem). If the file already exists, the download is skipped.
3. It SSHes to each manager and runs `servers_manager_install.sh` with param1=`true` (AirGap mode).
4. The bash script installs from the shared filesystem — no download occurs on the remote manager.

#### Space Install
Space install does **not** download XAP. It assumes the zip is already staged at `$ODSXARTIFACTS/gs/` (from a prior manager install or manual staging). It passes `sourceInstallerDirectory` to `servers_space_install.sh` which installs from the shared filesystem.

### Data Engines / Feeders
Supports multiple database feeder types: DB2, MSSQL, MySQL, Oracle, Oracle ERP. Each has its own scripts, config sections in `app.config`, JAR artifacts in `app.yaml`, and utility modules.

### Data Integration (DI)
Kafka/ZooKeeper integration for data integration pipelines. Includes IIDR/CDC (Change Data Capture) with Access Server, Kafka Agent, and Oracle Agent components.
All DI/IIDR services: "di-flink-jobmanager" "di-flink-taskmanager" "di-manager" "di-mdm" "odsxzookeeper" "odsxkafka" "iidr_as_inst" "iidr_kafka_inst" "di-subscription-manager-iidr" "iidr_oracle_inst"

#### DI Filesystem Layout
On each DI server, a `setenv.sh` is generated during DI install in the gsods home directory. It exports path variables (`KAFKAPATH`, `KAFKA_DATA_PATH`, `KAFKA_LOGS_PATH`, `ZOOKEEPERPATH`, `ZOOKEEPER_DATA_PATH`, `ZOOKEEPER_LOGS_PATH`). The remove script sources this to know which paths to delete.

| Component | Binaries (`/giga/`) | Data (`/gigadata/`) | Logs (`/gigalogs/`) |
|---|---|---|---|
| Kafka | `/giga/kafka_2.13-*/` | `/gigadata/kafka/` | `/gigalogs/kafka/` |
| ZooKeeper | `/giga/apache-zookeeper-*/` | `/gigadata/zookeeper/` | `/gigalogs/zookeeper/` |
| DI MDM | `/giga/di-mdm/` | — | `/gigalogs/di-mdm/` |
| DI Manager | `/giga/di-manager/` | — | `/gigalogs/di-manager/` |
| DI Flink | `/giga/di-flink/` | — | `/gigalogs/di-flink/` |
| DI Processor | `/giga/di-processor/` | — | `/gigalogs/di-processor/` |
| DI Transformations | `/giga/di-transformations/` | — | `/gigalogs/di-transformations/` |
| DI Subscription Mgr | `/giga/di-subscription-manager/` | — | `/gigalogs/di-subscription-manager/` |
| IIDR Access Server | `/giga/iidr/as/` | — | — |
| IIDR Kafka Agent | `/giga/iidr/kafka/` | — | — |
| IIDR Oracle Agent | `/giga/iidr/oracle/` | — | — |

Spring Boot `.properties` files are generated at `/giga/di-*.properties` (e.g., `di-mdm.properties`) during DI install, containing ZooKeeper connection URLs and Spring profiles.

DI Flink uses `latest-flink` symlink pointing to the actual version directory (e.g., `flink-1.18.1`). The `stop-cluster.sh` script is Apache Flink's built-in cluster shutdown script — it stops all TaskManager workers then the JobManager.

#### DI Remove Flow (`servers_di_remove.sh`)
1. Sources `setenv.sh` to discover Kafka/ZK paths
2. Stops all DI systemd services (Kafka, ZK, Flink, MDM, Manager, etc.)
3. Stops Flink cluster via `stop-cluster.sh`
4. Removes binaries, data, logs, symlinks, `.properties` files, and service files
5. Runs `systemctl daemon-reload`
6. Does **not** remove IIDR components (Access Server, Kafka Agent, Oracle Agent)

#### DI Install Status Check (`utils/ods_list.py`)
The DI list screen determines install status by checking for files on the remote host via SSH. Known issues:
- **DI Flink**: Checks for `/giga/di-flink/latest-flink/bin/start-cluster.sh`. If the `latest-flink` symlink is broken or points to an empty directory, shows "NO" even if the Flink binary exists.
- **IIDR components**: The install check path (`/data/gs_software/iidr/`) may differ from the actual install path (`/giga/iidr/`) depending on the environment. If the paths don't match, shows "No" even when installed.

### Space Deployment
- Tiered Storage: Data is stored on the disks
- In-Memory: Data is stored in Memory (RAM) for quick access

### Monitoring Stack
- **Telegraf**: Metrics collection agent
- **InfluxDB**: Metrics storage - Time Series DB
- **Kapacitor**: Alerting
- **Grafana**: Dashboards - catalogue service, main dashboard, data freshness, datavalidator etc...
- **Prometheus (17.3.0+)**: GigaSpaces pushes OTLP straight to Prometheus' native OTLP receiver
  (`--web.enable-otlp-receiver`, `POST /api/v1/otlp/v1/metrics`) - no Telegraf hop. Configured by
  `config/metrics/metrics.properties` (template: `config/metrics.properties.template`), propagated
  per host by `configureMetricsProperties()`. There is no `prometheus` metrics registry; the registry
  name is `otlp`.

#### Per-cluster identity for a shared Prometheus (`configureOtelIdentity()`)
Writes a managed block into `<giga>/gigaspaces-smart-ods/bin/setenv-overrides.sh` on every manager
and space host, via `scripts/configure_otel_identity.sh`:

```bash
export OTEL_SERVICE_NAME=gigaspaces
export OTEL_RESOURCE_ATTRIBUTES="service.namespace=<lookup group>"
```

- **Why environment variables and not a property**: the 17.3.0 OTLP registry's `OtlpConfig.get()`
  returns `null` for every key, so OTel *resource* attributes can only arrive through the standard
  `OTEL_*` variables. There is no `metrics.otlp.resourceAttributes`, and `-D` flags are ignored.
  (`metrics.otlp.headers` *is* honoured - that is the hook for Mimir/Cortex `X-Scope-OrgID`.)
- **Effect**: Prometheus' OTLP receiver always derives `job="<service.namespace>/<service.name>"`
  and `instance="<service.instance.id>"`, regardless of `otlp.promote_resource_attributes`. So each
  cluster's series become separable with **no configuration change on the receiving Prometheus**.
  Without this, every cluster stores as `job="unknown_service"`.
- **`service.namespace` is the cluster's lookup group** (`-Dcom.gs.jini_lus.groups`): it already
  uniquely names the grid and defines membership, so it cannot drift from the cluster it labels.
- Called immediately after `configureMetricsProperties()` in all four install flows, i.e. **before**
  the servers are started, so the JVMs export it on their first start. GSCs inherit the GSA's
  environment, so only the GSA needs it.
- Idempotent - rewrites its own marked block rather than appending, so repeated installs cannot
  stack up duplicate exports.
- Goes through `executeRemoteShCommandAndGetOutput` (script piped to remote bash), **not**
  `executeRemoteCommandAndGetOutput*Python36` - see the pitfall on space-splitting below.

### AirGap Support
Two installation modes:
- `AirGap=true`: All installers pre-staged on shared filesystem, no internet needed
- `AirGap=false`: Downloads from GigaSpaces S3 releases

## Script Naming Convention
All scripts follow a strict naming pattern:
- `odsx_<category>_<subcategory>_<action>.py` (non-security)
- `odsx_security_<category>_<subcategory>_<action>.py` (security)
- Corresponding `.sh` files for remote execution on target hosts

## Automation Scripts (Expect-based)
The user creates automation scripts using Linux `expect` to drive the `odsx.py` interactive menu programmatically. These scripts live on each pivot machine at `/giga/utils/auto_odsx/` (outside this repo). They work by spawning `odsx.py` with CLI path arguments (e.g., `./odsx.py servers space remove`) and then using `expect`/`send` pairs to navigate prompts and confirmations automatically. Examples include `auto_spaceremove`, `auto_managerinstall`, `auto_gridreinstall`, `auto_tsdeploy`, and many more (~80 scripts). Simple operations that require no interactive input (e.g., `auto_spacelist`) are plain bash scripts instead of expect. These scripts are tightly coupled to the exact prompt text in ODSX — any changes to menu text, prompt wording, or confirmation messages will break them.

### Common `expect` Issues
- **`PYTHONPATH` not set**: `expect` spawns a non-interactive shell that may not source `.bashrc`/`.bash_profile`. If `PYTHONPATH` is missing, add `set env(PYTHONPATH) /giga/gs-odsx` before the `spawn` line.
- **`python3` version**: The shebang `#!/usr/bin/env python3` uses whatever `python3` points to. Check `alternatives --display python3` — if it points to Python 3.6, `dataclasses` and other 3.7+ features will fail.
- **Special characters in `expect` patterns**: Square brackets `[]` are Tcl command substitution. Use curly braces for literal matching: `expect -exact {Press [Enter] to install all.}`. The `-exact` flag additionally disables glob wildcards (`*`, `?`).

## Non-Root Operation (gs-odsx-non-root branch)

### Root Guard (warning only)
`odsx.py` checks `os.geteuid() == 0` at startup and **prints a warning** recommending to run as the `gsods` user, but does **not** exit. Running as root is still permitted for edge cases (e.g., one-time recovery scenarios).

### Architecture Decisions
- **SSH user**: All SSH connections use `app.server.user` (default `gsods`) via `get_ssh_user()` helper in `utils/ods_ssh.py`. No more hardcoded `root`.
- **Systemd**: GS services (gsa, gsc, gs, kafka, zookeeper, etc.) use `systemctl --user` with service files in `~gsods/.config/systemd/user/`. Third-party services (Grafana, InfluxDB, Telegraf) keep `sudo` via sudoers whitelist.
- **Paths**: Start/stop scripts deploy to `/giga/bin/` instead of `/usr/local/bin/`. Service files deploy to `~/.config/systemd/user/` instead of `/etc/systemd/system/`.
- **Package management**: Moved to `setup.sh` / `setup_nonroot.sh` as one-time root prerequisites. Install scripts check for prerequisites instead of installing packages.

### Setup scripts (split by privilege level)

Setup is split into two scripts (`scripts/user-setup.sh` for the app user, `scripts/root-setup.sh` for one-time root prereqs). Both are idempotent. Typical workflow:

1. `user-setup.sh -d /gigashare -u gsods -tar /path/gigashare.tgz` — extract tgz, create dirs, local setup
2. `root-setup.sh -d /gigashare` — user creation, NFS, sudoers, parent-dir chown
3. `user-setup.sh -d /gigashare -u gsods` — re-run to deploy SSH keys and configure remote hosts

Step-by-step walkthroughs (all atomic operations of each script) are in `scripts/CLAUDE.md`.

### Standalone Control Scripts (root-only, outside ODSX menu)

Root-only scripts that install/remove third-party services directly on target hosts, bypassing the ODSX menu:
- `scripts/influxdbctl.sh` — InfluxDB install/remove on the local host (`-i|-r|-h [--purge]`)
- `scripts/telegrafctl.sh` — Telegraf install/remove across all manager/space/pivot hosts (`-i|-r|-h [--purge]`)

Both read paths from `$ENV_CONFIG/app.config` and are idempotent. gsods has `sudo` only for start/stop/enable/disable/restart on these services via the sudoers whitelist. Full operational details (atomic steps, role-to-config mappings, fixes over the original ODSX scripts) are in `scripts/CLAUDE.md`.

### NFS sharing of `/gigashare`
`root-setup.sh` configures the pivot to export `$GIGA_SHARE` to every non-pivot host listed in `host.yaml`. The fstab entry on each non-pivot host uses the `users` option, which allows **any** local user (including gsods) to `mount`/`umount` the share without sudo. No `/etc/sudoers.d/odsx-nfs` file is needed — fstab alone grants mount/umount rights.

`exec` is NOT added to the fstab options. ODSX never runs binaries directly out of `/gigashare`; scripts are either piped over SSH or invoked as `python3 script.py` / `bash script.sh`, neither of which is blocked by the `noexec` implied by `users`. Adding `exec` would be an unnecessary security relaxation.

### Directory needs per server role

`root-setup.sh` unconditionally creates all 6 base directories on every host, but each role only actually reads/writes a subset. This matters when sizing filesystems or pruning config for minimal deployments.

| Role | /giga | /gigashare | /gigalogs | /gigadata | /gigawork | /gigainfluxdata |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| pivot | Y | Y | Y | - | Y | - |
| manager | Y | Y | Y | - | - | Y |
| space | Y | Y | Y | Y | Y | - |
| DI | Y | Y | Y | Y | Y | - |
| grafana | Y | Y | - | - | - | - |
| influxdb | Y | Y | - | - | - | Y |
| northbound | Y | Y | Y | - | - | - |
| data_validator | Y | Y | Y | - | - | - |
| CDC/IIDR | Y | Y | - | - | - | - |

`data_validator` also installs to a separate path configured via `app.dv.server.install.target` / `app.dv.agent.install.target` — that target is not one of the 6 standard dirs.

### Known Pitfalls

#### `systemctl --user` over SSH requires environment variables
SSH non-login shells don't set `XDG_RUNTIME_DIR` or `DBUS_SESSION_BUS_ADDRESS`. Without these, `systemctl --user` fails with "This command has to be run with superuser privileges". **Two-layer fix required:**
1. Set in gsods's `.bashrc` on every server (for interactive SSH sessions)
2. Set at the top of every `.sh` script that uses `systemctl --user` (for `bash -s < script.sh` piped execution, which doesn't source `.bashrc`)

```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus
```

#### `User=` / `Group=` lines in user-level systemd service files
User-level systemd services **must not** have `User=` or `Group=` directives. If present, the service fails with `status=216/GROUP`. These lines are only valid for system-level services in `/etc/systemd/system/`.

#### ODSX logs to `${app.gigalog.path}/odsx.log`, not the repo's `logs/odsx.log`
`config/logging.conf` points its only file handler at
`("${app.gigalog.path}/odsx.log", "a", 1024*1024*5, 10)`, with the placeholder resolved at runtime by
`_expand_logging_conf()` in `scripts/logManager.py`. Resolve the real path per environment with
`grep ^app.gigalog.path $ENV_CONFIG/app.config` — on env4 it is
`/v/campus/vi/cs/eqrisk/josroden/gigalogs/odsx.log`.

The tracked `logs/odsx.log` inside the repo is a **0-byte placeholder that the current config never
writes to**. Grepping it during a diagnosis returns zero matches, which is indistinguishable from
"the code never ran" — a false negative that has already cost real time. Always resolve the handler's
path before concluding anything from an empty log.

#### `unzip` prompts consume the piped script — always pass `-o`
Install scripts reach the remote host as `cat lib_app_config.sh script.sh | ssh ... bash -s`, so
**stdin is the script body**. When `unzip` finds existing files it prompts on stdin, eats the rest of
the script, and every function defined below that point silently never gets defined — a partial
install that reports no error. `-qq` suppresses the file *listing*, **not** the prompts. Every
`unzip` in an install script must pass `-o`.

Fixed Aug 2026 across all 11 call sites: `installAirGapGS` in `servers_{manager,space}_install.sh`,
`security_{manager,space}_install.sh` and `security_dev_{manager,space}_install.sh`; the legacy 16.4
extraction in `security_manager_install.sh`; and the `unzipGS` equivalents in the four security
installers. Before that only the two non-security `unzipGS` functions had `-o`.

Why it stayed hidden: the **space** install is wrapped in `if installStatus == 'No'`
(`isInstalledAndGetVersion()`), so it never re-extracts over an existing tree — the guard was
accidentally masking the bug. The **manager** install has no such guard (detection exists only in
`odsx_servers_manager_list.py`, for the `Installed` column) and re-runs unconditionally, so
`auto_managerinstall` against an already-installed manager was the exposed path. Any
remove-then-install sequence, such as `auto_spacereinstall`, never hit it.

#### `readValuefromAppConfig()` truncates any value containing `=`
`setConfigProperties()` builds its dict with `line.split("=")[0]` / `line.split("=")[1]`, so it keeps
only the **first** `=`-delimited field of the value. Every `app.*.gsOptionExt` value therefore reads
back as just `"-Dcom.gs.work` - silently, with no error. Parse `app.config` as text for those (see
`getClusterLookupGroup()` in `utils/ods_list.py`), and never use `readValuefromAppConfig()` on a key
whose value can contain `=`.

#### `executeRemoteCommandAndGetOutput*Python36()` cannot carry an argument containing a space
They build one command string and then `cmd.split(" ")` it into an argv list, so any quoted argument
with a space is torn apart (quotes are not stripped either - the remote shell consumes them). This is
why every `sed` expression passed through them is deliberately space-free. For anything with spaces,
pipe a script to remote bash instead: `executeRemoteShCommandAndGetOutput()` /
`build_remote_bash_cmd()`, which also prepends `lib_app_config.sh` for `read_property()`.

#### `install/install.tar` stale artifact
Install scripts must delete `install/install.tar` before rebuilding (`os.remove('install/install.tar')`); a stale tar carries outdated service files to remote hosts. Don't reintroduce builds that skip the delete.

#### Prerequisite-check cleanup (Java/unzip RPM)
Java and unzip are installed by `root-setup.sh` as root prerequisites — `validateRPM()`/`validateRPMS()` no longer checks for `$ODSXARTIFACTS/jdk/*.rpm` or `$ODSXARTIFACTS/unzip/*.rpm`. Don't reintroduce those checks in `utils/ods_list.py` or any install script. `validateRPMS()` only checks `$ODSXARTIFACTS/gs/*.zip` for the manager install flow.

#### `read_property` over SSH: the lib_app_config.sh prepend trick
Bash scripts call `read_property "app.foo.bar"` (defined in `scripts/lib_app_config.sh`) to read app.config values with `${app.*.path}` resolution. Locally on the pivot, scripts source the file via:
```bash
[ -r "$(dirname "$0")/lib_app_config.sh" ] && source "$(dirname "$0")/lib_app_config.sh"
```
Over SSH-pipe execution (`ssh host bash -s args < script.sh`), `$0` is `bash` and the conditional source silently no-ops. **All stdin-pipe SSH helpers in `utils/ods_ssh.py` (`connectExecuteSSH`, `connectExecuteSSHWithLoginProxy`, `executeRemoteShCommandAndGetOutput`) go through the private `build_remote_bash_cmd()` helper, which unconditionally prepends `lib_app_config.sh` to the stdin stream:
```python
return "cat {helper} {script} | ssh{pem} {user}@{host} {bash_part}".format(...)
```
The remote bash receives `lib_app_config.sh` content first (function defs only, no side effects), then the script body. The helper path is resolved relative to `ods_ssh.py` (not cwd), and `build_remote_bash_cmd` raises `FileNotFoundError` if the helper is missing — silent degradation here previously caused a `rm -rf /*` event in production.

**Invariant**: any new SSH helper in `ods_ssh.py` that pipes a shell script to the remote via stdin MUST go through `build_remote_bash_cmd` so the prepend is always in place. Don't reintroduce inline `cmd = "ssh ... bash -s ... < script.sh"` constructions.

**Don't add side-effect code to lib_app_config.sh** — it must remain pure function definitions, since it runs unconditionally on every remote bash invocation.

#### App user must be able to traverse path-root parents on remote hosts
`root-setup.sh` mkdirs and `chown -R`'s the **parent** of each of the 6 path roots on every remote (e.g. `/v/campus/vi/cs/eqrisk/josroden/`). The parent dirs ABOVE that (e.g. `/v/`, `/v/campus/`) are created by `mkdir -p` running as root and end up `root:root` mode 755. The app user only needs `+x` (traverse) on those — which mode 755 provides — to read/write under its owned leaf parent. If any pre-existing intermediate dir has restrictive perms (e.g. mode 700 owned by another user with no group/other `+x`), the app user can't traverse and `user-setup.sh`'s mkdir will fail with `Permission denied`.

## `${app.*.path}` Placeholder System

### Single source of truth
The 6 path-root keys at the bottom of `app.config` are the single source of truth for filesystem layout:

```
app.giga.path=/giga
app.gigashare.path=/gigashare
app.gigalog.path=/gigalogs
app.gigadata.path=/gigadata
app.gigawork.path=/gigawork
app.gigainfluxdata.path=/gigainfluxdata
```

Every other path-bearing value in `app.config`, every `install/*.service` file, `config/logging.conf`, `install/mq-connector/config/application.yml`, and `env_config/security/security.properties` use `${app.<root>.path}` placeholders that resolve against these 6 keys. Edit one root key, and everything dependent on it follows.

### Resolution layers
| Layer | Resolved by | Notes |
|---|---|---|
| Python | `expand_path_placeholders(value)` in `utils/ods_app_config.py` | Called automatically by `readValuefromAppConfig()` and `readValueByConfigObj()`. Public — install scripts can also call it on arbitrary strings. |
| Bash | `read_property KEY` in `scripts/lib_app_config.sh` | Sourced from each script. The default config-path resolution order is: explicit 2nd arg → `$APP_CONFIG` → `$ENV_CONFIG_PATH` → `$ENV_CONFIG/app.config`. |
| Install templates (`.service`, `.yml`, `.yaml`) | `render_install_templates()` in `utils/ods_app_config.py` | Called by every install script that builds `install.tar`, just before the tar step. Substitutes placeholders in-place in the staged `install/` tree. |
| `config/logging.conf` | `_expand_logging_conf()` in `scripts/logManager.py` | Inline mini-parser (avoids importing `ods_app_config`, which would create a cycle since `ods_app_config` imports `logManager`). Writes a tempfile with substituted placeholders before passing to `logging.config.fileConfig()`. |

### Path-root keys themselves stay literal
The 6 root keys (`app.giga.path=/giga`, etc.) contain no `${...}` so the regex sub is a no-op on them. There's no risk of self-recursion by construction. The same regex is used in Python and bash so resolution is identical across both.

### Legacy `/dbagiga*` literals
The previous `/dbagiga/...` → `<gigaPath>/...` translation chain has been removed; configs must use `${app.*.path}` form. A few `/dbagiga*` literals remain intentionally as **search patterns** (not hardcoded paths) in the 3 adabas install scripts and `scripts/setup.sh`/`quickSetup.sh` sed lines — leave those alone. Backup `app.config` snapshots in `env_config/` also contain the literal but aren't loaded.

### Bash scripts: shared helper
`scripts/lib_app_config.sh` is the canonical definition of `read_property()`. See [Known Pitfalls — `read_property` over SSH](#read_property-over-ssh-the-lib_app_configsh-prepend-trick) for the source-vs-prepend mechanism. Don't redefine `read_property` inline in any script.

### `app.yaml` is unaffected
`app.yaml` maps artifact logical keys to filenames inside `$ODSXARTIFACTS`. It plays no role in directory naming and contains no `${app.*.path}` placeholders.

## Python Dependencies
Key packages (from `scripts/requirements.txt`): `colorama`, `pyfiglet`, `schedule`, `configobj`, `pandas`, `tabulate`, `requests`, `pyyaml`, `argparse`, `argcomplete`.
