#!/bin/bash
################################################################################
# GigaSpaces Partition Rebalancer
#
# Detects and fixes unbalanced partition distribution in a GigaSpaces cluster.
# Ensures optimal distribution with no primary/backup colocation violations.
#
# Usage: ./gs_partition_rebalancer.sh [OPTIONS]
#   -s, --service <name>    Service name (default: dih-tau-service)
#   -d, --dry-run           Dry run mode (default: true)
#   -e, --execute           Execute the plan (disables dry-run)
#   -v, --verbose           Verbose output
#   -h, --help              Show help
#
# Required Files:
#
# 1. gs-partition-rebalancer.sh - The main script (in current directory)
# 2. optimal_rebalancer.py - Python script for optimal rebalancing calculations (should be in same directory as the main script)
# 3. Configuration files (on target system):
#   - /gigashare/env_config/host.yaml - Contains server/host configuration (pivot, space servers, manager IPs)
#   - /gigashare/env_config/app.config - Contains application config (service name)
# 4. GigaSpaces installation:
#   - <app.giga.path>/gigaspaces-smart-ods/bin/gs.sh - GigaSpaces CLI tool (path from app.config)
#
# Required External Tools:
#
# - yq - YAML parser (required)
# - jq - JSON parser (required)
# - curl - HTTP client (required)
# - python3 - Python interpreter (required for optimal_rebalancer.py)
# - Standard Unix tools: hostname, awk, grep, cut, tr, mktemp
#
# Summary:
#
# The two main files you need to copy together are:
# - gs-partition-rebalancer.sh
# - optimal_rebalancer.py
################################################################################

set -euo pipefail

if [ -z "${ENV_CONFIG:-}" ]; then
  echo "Error: ENV_CONFIG is not set. Please set it before running this script."
  exit 1
fi

# Configuration — paths driven by app.config, not hardcoded
readonly CONFIG_DIR="${ENV_CONFIG}"
readonly HOST_YAML="${CONFIG_DIR}/host.yaml"
readonly APP_CONFIG="${CONFIG_DIR}/app.config"

read_property() {
  local prop_name="$1"
  grep "^$prop_name=" "$APP_CONFIG" | awk -F'=' '{print $2}'
}

readonly GS_HOME="$(read_property app.giga.path)/gigaspaces-smart-ods"
readonly GIGA_WORK="$(read_property app.gigawork.path)"
readonly GIGA_SHARE="$(read_property app.gigashare.path)"

# Get user/pass creds
_USER=$(awk -F= '/app.manager.security.username=/ {print $2}' ${APP_CONFIG})
if grep '^app.vault.use=true' ${APP_CONFIG} > /dev/null ; then
  _VAULT_PASS=$(awk -F= '/app.manager.security.password.vault=/ {print $2}' ${APP_CONFIG})
  _PASS=$(java -Dapp.db.path=${GIGA_WORK}/sqlite/ -jar ${GIGA_SHARE}/current/gs/jars/gs-vault-1.0-SNAPSHOT-jar-with-dependencies.jar --get ${_VAULT_PASS})
else
  _PASS=$(awk -F= '/app.manager.security.password=/ {print $2}' ${APP_CONFIG})
fi

readonly GS_CLI="${GS_HOME}/bin/gs.sh --username=$_USER --password=$_PASS "

# Read service name from config file
SERVICE_NAME=$(grep '^app.newspace.pu.name=' "$APP_CONFIG" 2>/dev/null | cut -d'=' -f2 | tr -d ' ')
if [[ -z "$SERVICE_NAME" ]]; then
    echo "ERROR: Could not read app.newspace.pu.name from $APP_CONFIG"
    exit 1
fi

# Derive space name from service name (replace -service with -space)
SPACE_NAME="${SERVICE_NAME%-service}-space"

DRY_RUN=true
VERBOSE=false
AUTO_CONFIRM=false
CREATE_BLOCKED=false
VERIFICATION_TIMEOUT=90
STEP_DELAY=5

# Manager failover configuration
declare -a MANAGER_IPS=()
ACTIVE_MANAGER=""
readonly MANAGER_CONNECT_TIMEOUT=5
readonly MANAGER_REQUEST_TIMEOUT=30
readonly MANAGER_RETRY_COUNT=3

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Temp files for state storage
STATE_FILE=$(mktemp -t gs_rebalancer_state.XXXXXX)
PLAN_FILE=$(mktemp -t gs_rebalancer_plan.XXXXXX)

cleanup() {
    rm -f "$STATE_FILE" "$PLAN_FILE"
}
trap cleanup EXIT ERR INT TERM

################################################################################
# Utility Functions
################################################################################

log() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $*" >&2
    fi
}

abort() {
    log_error "$1"
    exit 1
}

print_header() {
    local text="$1"
    echo ""
    echo "================================================================================"
    echo "$text"
    echo "================================================================================"
}

print_section() {
    local text="$1"
    echo ""
    echo "--- $text ---"
}

################################################################################
# Environment Discovery
################################################################################

get_pivot_ip() {
    if ! command -v yq &> /dev/null; then
        abort "yq command not found. Please install yq."
    fi

    local pivot_ip
    pivot_ip=$(yq '.servers.pivot.host1' "$HOST_YAML" 2>/dev/null) || abort "Failed to read pivot IP from $HOST_YAML"

    if [[ -z "$pivot_ip" || "$pivot_ip" == "null" ]]; then
        abort "Could not determine pivot IP from $HOST_YAML"
    fi
    echo "$pivot_ip"
}

get_space_servers() {
    local servers
    servers=$(yq '.servers.space[]' "$HOST_YAML" 2>/dev/null | tr '\n' ' ') || abort "Failed to read space servers from $HOST_YAML"

    if [[ -z "$servers" ]]; then
        abort "Could not determine space servers from $HOST_YAML"
    fi
    echo "$servers"
}

verify_running_on_pivot() {
    local pivot_ip
    local current_ip

    pivot_ip=$(get_pivot_ip)
    current_ip=$(hostname -I | awk '{print $1}')

    debug "Pivot IP: $pivot_ip, Current IP: $current_ip"

    # Check if we can access the GS CLI
    if [[ ! -x "${GS_HOME}/bin/gs.sh" ]]; then
        abort "GigaSpaces CLI not found or not executable: ${GS_HOME}/bin/gs.sh. Are you running on the pivot machine?"
    fi
}

################################################################################
# GigaSpaces API Functions
################################################################################

gs_service_list() {
    $GS_CLI --server="$ACTIVE_MANAGER" service list 2>&1 | grep -v "JAVA_HOME" || true
}

gs_service_info() {
    local service="$1"
    $GS_CLI --server="$ACTIVE_MANAGER" service info "$service" 2>&1 | grep -v "JAVA_HOME" || true
}

gs_service_list_instances() {
    local service="$1"
    $GS_CLI --server="$ACTIVE_MANAGER" service list-instances "$service" 2>&1 | grep -v "JAVA_HOME" || true
}

gs_service_info_instance() {
    local instance="$1"
    $GS_CLI --server="$ACTIVE_MANAGER" service info-instance "$instance" 2>&1 | grep -v "JAVA_HOME" || true
}

################################################################################
# Manager Connection and Failover Functions
################################################################################

discover_managers() {
    debug "Discovering managers from configuration..."
    local manager_list
    manager_list=$(yq '.servers.manager[]' "$HOST_YAML" 2>/dev/null)

    if [[ -z "$manager_list" ]]; then
        abort "No managers found in $HOST_YAML (key: servers.manager[])"
    fi

    MANAGER_IPS=()
    while IFS= read -r ip; do
        [[ -n "$ip" && "$ip" != "null" ]] && MANAGER_IPS+=("$ip")
    done <<< "$manager_list"

    if [[ ${#MANAGER_IPS[@]} -eq 0 ]]; then
        abort "No valid manager IPs found in configuration"
    fi

    log "Discovered ${#MANAGER_IPS[@]} managers: ${MANAGER_IPS[*]}"
}

check_manager_health() {
    local manager_ip="$1"
    local url="http://${manager_ip}:8090/v2/info"

    debug "Health check: $url"
    local http_code
    http_code=$(curl -sk -u $_USER:$_PASS -o /dev/null -w "%{http_code}" \
        --connect-timeout "$MANAGER_CONNECT_TIMEOUT" \
        --max-time "$MANAGER_REQUEST_TIMEOUT" \
        "$url" 2>/dev/null)

    if [[ "$http_code" == "200" ]]; then
        debug "Manager $manager_ip is healthy (HTTP $http_code)"
        return 0
    else
        debug "Manager $manager_ip unhealthy or unreachable (HTTP $http_code)"
        return 1
    fi
}

get_active_manager() {
    # If we have a cached active manager, verify it's still healthy
    if [[ -n "$ACTIVE_MANAGER" ]]; then
        if check_manager_health "$ACTIVE_MANAGER"; then
            debug "Using cached manager: $ACTIVE_MANAGER"
            return 0
        else
            log_warn "Cached manager $ACTIVE_MANAGER is no longer responding, searching for alternative..."
            ACTIVE_MANAGER=""
        fi
    fi

    # Try each manager in round-robin order
    local tried=0
    for manager_ip in "${MANAGER_IPS[@]}"; do
        ((tried++)) || true
        debug "Trying manager $tried/${#MANAGER_IPS[@]}: $manager_ip"

        if check_manager_health "$manager_ip"; then
            ACTIVE_MANAGER="$manager_ip"
            log_success "Connected to manager: $ACTIVE_MANAGER"
            return 0
        fi

        log_warn "Manager $manager_ip unavailable, trying next..."
    done

    # All managers failed
    log_error "All ${#MANAGER_IPS[@]} managers are unavailable:"
    for manager_ip in "${MANAGER_IPS[@]}"; do
        log_error "  - $manager_ip"
    done
    return 1
}

setup_cli_manager() {
    # CLI commands now use --server parameter to directly specify ACTIVE_MANAGER
    # This overrides the hardcoded GS_MANAGER_SERVERS in setenv-overrides.sh
    debug "CLI configured to use --server parameter with manager: $ACTIVE_MANAGER"
}

init_manager_connection() {
    print_section "Initializing Manager Connection"

    # Step 1: Discover all managers from configuration
    discover_managers

    # Step 2: Find and cache an active manager
    if ! get_active_manager; then
        abort "Failed to connect to any GigaSpaces manager"
    fi

    # Step 3: Setup CLI environment
    setup_cli_manager

    log_success "Manager connection initialized: $ACTIVE_MANAGER"
}

################################################################################
# REST API Functions
################################################################################

rest_get_containers() {
    local url="http://${ACTIVE_MANAGER}:8090/v2/containers"
    curl -sk -u $_USER:$_PASS "$url" 2>/dev/null || echo "[]"
}

rest_get_pu_instances() {
    local service="$1"
    local url="http://${ACTIVE_MANAGER}:8090/v2/pus/${service}/instances"
    curl -sk -u $_USER:$_PASS "$url" 2>/dev/null || echo "[]"
}

rest_get_space_instances() {
    local space="$1"
    local url="http://${ACTIVE_MANAGER}:8090/v2/spaces/${space}/instances"
    curl -sk -u $_USER:$_PASS "$url" 2>/dev/null || echo "[]"
}

rest_relocate_instance() {
    local service="$1"
    local instance_id="$2"
    local container_id="$3"

    local url="http://${ACTIVE_MANAGER}:8090/v2/pus/${service}/instances/${instance_id}/relocate?containerId=${container_id}"

    debug "REST API: Relocating $instance_id to $container_id"

    local response
    response=$(curl -sk -u $_USER:$_PASS -X POST \
        --header 'Content-Type: application/json' \
        --header 'Accept: text/plain' \
        "$url" 2>&1)

    echo "$response"
}

rest_demote_primary() {
    local space="$1"
    local instance_id="$2"
    local max_suspend="${3:-15s}"

    local url="http://${ACTIVE_MANAGER}:8090/v2/spaces/${space}/instances/${instance_id}/demote?maxSuspendTime=${max_suspend}"

    debug "REST API: Demoting $instance_id (maxSuspendTime=$max_suspend)"

    local response
    response=$(curl -sk -u $_USER:$_PASS -X POST \
        --header 'Content-Type: application/json' \
        --header 'Accept: text/plain' \
        "$url" 2>&1)

    echo "$response"
}

get_container_on_host() {
    local target_host="$1"

    debug "Searching for container on host $target_host"

    # Get containers from REST API
    local containers
    containers=$(rest_get_containers)

    if command -v jq &> /dev/null && [[ "$containers" != "[]" ]]; then
        # Extract container IDs and parse hostname from each
        local container_id
        while IFS= read -r container_id; do
            [[ -z "$container_id" ]] && continue

            # Extract hostname from container ID (before the ~)
            local hostname="${container_id%%~*}"

            # Extract IP from hostname using our existing generic function
            local container_ip
            container_ip=$(extract_ip_from_hostname "$hostname")

            # Compare IPs directly
            if [[ "$container_ip" == "$target_host" ]]; then
                debug "Found container: $container_id (IP: $container_ip)"
                echo "$container_id"
                return 0
            fi
        done < <(echo "$containers" | jq -r '.[].id' 2>/dev/null)
    fi

    # Fallback: Use CLI to get container list
    debug "Falling back to CLI for container lookup"
    local container_list
    container_list=$($GS_CLI container list 2>&1 | grep -v "JAVA_HOME" || true)

    # Parse container list line by line
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue

        local container_id
        local container_hostname
        container_id=$(echo "$line" | awk '{print $1}')
        container_hostname=$(echo "$line" | awk '{print $2}')

        # Extract IP from hostname
        local container_ip
        container_ip=$(extract_ip_from_hostname "$container_hostname")

        if [[ "$container_ip" == "$target_host" ]]; then
            debug "Found container via CLI: $container_id (IP: $container_ip)"
            echo "$container_id"
            return 0
        fi
    done < <(echo "$container_list")

    log_error "No container found on host $target_host"
    return 1
}

################################################################################
# Colocation Resolution Functions
################################################################################
#
# PARTITION ID INDEXING CONVENTION:
# ---------------------------------
# - STATE_FILE: stores 1-based partition numbers (1 to 40)
#   (extracted from instance ID names like dih-tau-service~11_2 -> partition 11)
# - Instance IDs in names: 1-based (dih-tau-service~11_2 = partition 11)
# - REST API partitionId field: 0-based (partition 11 has partitionId=10)
#
# Variable naming:
#   - partition = 1-based (for STATE_FILE queries, user messages, instance IDs)
#   - partition_idx = 0-based (only for REST API queries)
#
# When querying REST API, convert: partition_idx = partition - 1
#
################################################################################

get_free_containers_by_host() {
    # Returns free (empty) containers grouped by host IP
    # Output format: host_ip|container_id per line

    local containers
    containers=$(rest_get_containers)

    if ! command -v jq &> /dev/null || [[ -z "$containers" ]] || [[ "$containers" == "[]" ]]; then
        log_error "Cannot query containers - jq not available or REST API failed"
        return 1
    fi

    # jq to find containers with 0 instances and extract host IP
    echo "$containers" | jq -r '
        .[] |
        select((.instances | length) == 0) |
        .id
    ' 2>/dev/null | while read -r container_id; do
        [[ -z "$container_id" ]] && continue
        local hostname="${container_id%%~*}"
        local host_ip
        host_ip=$(extract_ip_from_hostname "$hostname")
        echo "${host_ip}|${container_id}"
    done
}

get_free_container_on_host() {
    # Get a specific free container on a target host
    local target_host="$1"

    local free_containers
    free_containers=$(get_free_containers_by_host)

    # Note: Using here-string instead of pipe to avoid subshell issue with return
    while IFS='|' read -r host_ip container_id; do
        if [[ "$host_ip" == "$target_host" ]]; then
            echo "$container_id"
            return 0
        fi
    done <<< "$free_containers"

    return 1
}

check_colocation_blocked_missing() {
    # Check if a missing backup cannot deploy due to colocation violation
    # @param partition: 1-based partition number (matches STATE_FILE)
    # Returns 0 if blocked (all free containers on same host as primary)
    # Returns 1 if NOT blocked (free container exists elsewhere)
    # Outputs the blocked host IP if blocked

    local partition="$1"

    # Get primary host for this partition (STATE_FILE uses 1-based)
    local primary_host
    primary_host=$(awk -F',' -v p="$partition" '$1 == p && $2 == "primary" {print $3; exit}' "$STATE_FILE")

    if [[ -z "$primary_host" ]]; then
        debug "Cannot find primary host for partition $partition"
        return 1
    fi

    # Get all free containers
    local free_containers
    free_containers=$(get_free_containers_by_host)

    if [[ -z "$free_containers" ]]; then
        debug "No free containers found anywhere"
        return 1
    fi

    # Check if ALL free containers are on the primary host
    local has_free_elsewhere=false
    local blocked_host=""

    while IFS='|' read -r host_ip container_id; do
        [[ -z "$host_ip" ]] && continue
        if [[ "$host_ip" == "$primary_host" ]]; then
            blocked_host="$primary_host"
        else
            has_free_elsewhere=true
            break
        fi
    done <<< "$free_containers"

    if [[ "$has_free_elsewhere" == "false" && -n "$blocked_host" ]]; then
        # All free containers are on primary host - blocked by colocation
        echo "$blocked_host"
        return 0
    fi

    return 1
}

find_relocatable_backup_to_host() {
    # Find a backup that can be safely relocated TO a specific target host
    # Returns: partition|instance_id|current_host

    local target_host="$1"

    # Query space instances via REST API
    local space_instances
    space_instances=$(rest_get_space_instances "$SPACE_NAME")

    if ! command -v jq &> /dev/null || [[ -z "$space_instances" ]] || [[ "$space_instances" == "[]" ]]; then
        log_error "Cannot query space instances"
        return 1
    fi

    # Find all BACKUP instances and check if they can be moved to target_host
    # Criteria: Primary must NOT be on target_host (to avoid colocation)

    # Build a map of partition -> primary_host
    local partition_primary_map
    partition_primary_map=$(echo "$space_instances" | jq -r '
        .[] | select(.mode == "PRIMARY") |
        "\(.partitionId)|\(.hostId)"
    ' 2>/dev/null)

    # Find a suitable backup
    # Note: Using here-string instead of pipe to avoid subshell issue with return
    local backups
    backups=$(echo "$space_instances" | jq -r '
        .[] | select(.mode == "BACKUP") |
        "\(.partitionId)|\(.id)|\(.hostId)"
    ' 2>/dev/null)

    while IFS='|' read -r partition_id instance_id backup_host; do
        [[ -z "$partition_id" ]] && continue

        # Extract backup host IP
        local backup_host_ip
        backup_host_ip=$(extract_ip_from_hostname "${backup_host%%~*}")

        # Skip if backup is already on target host
        [[ "$backup_host_ip" == "$target_host" ]] && continue

        # Get primary host for this partition
        local primary_host_full
        primary_host_full=$(echo "$partition_primary_map" | grep "^${partition_id}|" | cut -d'|' -f2)
        local primary_host_ip
        primary_host_ip=$(extract_ip_from_hostname "${primary_host_full%%~*}")

        # Check if primary is NOT on target host (safe to relocate backup there)
        if [[ "$primary_host_ip" != "$target_host" ]]; then
            # Found a suitable backup
            local display_partition=$((partition_id + 1))
            echo "${display_partition}|${instance_id}|${backup_host_ip}"
            return 0
        fi
    done <<< "$backups"

    return 1
}

wait_for_auto_deploy() {
    # Wait for GigaSpaces to auto-deploy a missing instance
    local partition="$1"
    local instance_type="$2"  # "primary" or "backup"
    local timeout="${3:-30}"

    log "Waiting up to ${timeout}s for partition $partition $instance_type to auto-deploy..."

    local elapsed=0
    local partition_id=$((partition - 1))  # Convert to 0-based
    local mode="PRIMARY"
    [[ "$instance_type" == "backup" ]] && mode="BACKUP"

    while [[ $elapsed -lt $timeout ]]; do
        # Query space instances via REST API
        local space_instances
        space_instances=$(rest_get_space_instances "$SPACE_NAME")

        # Check if the missing instance now exists
        local found
        found=$(echo "$space_instances" | jq -r \
            --argjson pid "$partition_id" \
            --arg mode "$mode" \
            '.[] | select(.partitionId == $pid and .mode == $mode) | .id' \
            2>/dev/null | head -1)

        if [[ -n "$found" ]]; then
            log_success "Partition $partition $instance_type auto-deployed: $found"
            return 0
        fi

        sleep 2
        elapsed=$((elapsed + 2))
        debug "Waiting... ${elapsed}s elapsed"
    done

    log_warn "Partition $partition $instance_type did not auto-deploy within ${timeout}s"
    return 1
}

resolve_colocation_blocked_missing() {
    # Main orchestration function to resolve missing instances blocked by colocation
    print_section "Resolving Colocation-Blocked Missing Instances"

    local space_servers
    space_servers=($(get_space_servers))
    local total_partitions
    total_partitions=$(cut -d',' -f1 "$STATE_FILE" | sort -u | wc -l | tr -d ' ')

    local resolved=0
    local failed=0

    # Step 1: Identify all missing backup instances
    # STATE_FILE uses 1-based partition numbers (1 to total_partitions)
    local missing_partitions=()
    for partition in $(seq 1 "$total_partitions"); do
        local backup_exists
        backup_exists=$(awk -F',' -v p="$partition" \
            'BEGIN{c=0} $1 == p && $2 == "backup" {c++} END{print c}' "$STATE_FILE")
        backup_exists=${backup_exists:-0}

        if [[ "$backup_exists" -eq 0 ]]; then
            missing_partitions+=("$partition")
        fi
    done

    if [[ ${#missing_partitions[@]} -eq 0 ]]; then
        log "No missing backup instances to resolve"
        return 0
    fi

    log "Found ${#missing_partitions[@]} missing partition backup(s): ${missing_partitions[*]}"

    # Step 2: For each missing instance, check if blocked by colocation
    for partition in "${missing_partitions[@]}"; do
        log "Analyzing partition $partition..."

        local blocked_host
        if blocked_host=$(check_colocation_blocked_missing "$partition"); then
            log "Partition $partition backup blocked - only free container(s) on $blocked_host (same as primary)"

            # Step 3: Find a backup that can be relocated TO blocked_host
            local relocate_info
            if relocate_info=$(find_relocatable_backup_to_host "$blocked_host"); then
                local rel_partition
                local rel_instance
                local rel_current_host
                rel_partition=$(echo "$relocate_info" | cut -d'|' -f1)
                rel_instance=$(echo "$relocate_info" | cut -d'|' -f2)
                rel_current_host=$(echo "$relocate_info" | cut -d'|' -f3)

                log "Found candidate: Relocate partition $rel_partition backup from $rel_current_host to $blocked_host"

                if [[ "$DRY_RUN" == "false" ]]; then
                    # Step 4: Get free container on blocked_host and relocate
                    local target_container
                    target_container=$(get_free_container_on_host "$blocked_host")

                    if [[ -n "$target_container" ]]; then
                        # Extract the actual suffix from rel_instance (space-level ID from REST API)
                        # rel_instance is like "dih-tau-space~11_1" or "dih-tau-space~11_2"
                        local instance_suffix="${rel_instance##*~}"  # e.g., "11_1" or "11_2"
                        # PU instance IDs use the same partition~suffix format with SERVICE_NAME
                        local pu_instance_id="${SERVICE_NAME}~${instance_suffix}"
                        log "Relocating $pu_instance_id to $target_container..."

                        local response
                        response=$(rest_relocate_instance "$SERVICE_NAME" "$pu_instance_id" "$target_container")

                        if echo "$response" | grep -qi "error"; then
                            log_error "Relocation failed: $response"
                            ((failed++)) || true
                            continue
                        fi

                        log "Relocation initiated. Waiting 10s for completion..."
                        sleep 10

                        # Verify relocation completed (use PU instance ID for verification)
                        if verify_instance_on_host "$pu_instance_id" "$blocked_host"; then
                            log_success "Relocation verified"

                            # Step 5: Wait for auto-deploy of missing instance
                            # wait_for_auto_deploy expects 1-based partition number
                            if wait_for_auto_deploy "$partition" "backup" 30; then
                                ((resolved++)) || true

                                # Refresh STATE_FILE after successful resolution
                                log "Refreshing cluster state..."
                                discover_cluster_state
                            else
                                log_warn "Auto-deploy timed out - GigaSpaces may still deploy later"
                                ((failed++)) || true
                            fi
                        else
                            log_error "Relocation verification failed"
                            ((failed++)) || true
                        fi
                    else
                        log_error "No free container found on $blocked_host"
                        ((failed++)) || true
                    fi
                else
                    log_warn "[DRY RUN] Would relocate partition $rel_partition backup to $blocked_host"
                fi
            else
                log_warn "No suitable backup found to relocate to $blocked_host"
                ((failed++)) || true
            fi
        else
            log "Partition $partition backup is NOT blocked by colocation"
            log "Free containers exist on other hosts - GigaSpaces should auto-deploy"
        fi
    done

    echo ""
    if [[ $resolved -gt 0 ]]; then
        log_success "Resolved $resolved missing instance(s)"
    fi
    if [[ $failed -gt 0 ]]; then
        log_warn "$failed missing instance(s) could not be resolved automatically"
    fi

    return $failed
}

create_colocation_blocked_scenario() {
    # Creates a colocation-blocked scenario for testing the resolution logic
    # WARNING: This is a DESTRUCTIVE operation that kills a container!
    #
    # Strategy (v5 - correct approach):
    # 1. Find partition X: PRIMARY on host P, BACKUP on host B
    # 2. Find partition Y: BACKUP on host P (primary NOT on B)
    # 3. Kill partition X's BACKUP on host B
    # 4. Relocate partition Y's BACKUP from P to B (filling the freed container)
    # 5. Result: X's backup can't recover - only free container is on P (same as primary)
    #
    # The key insight: relocate FROM the primary's host TO the backup's host,
    # so the free container ends up on the primary's host.

    print_section "Creating Colocation-Blocked Scenario (FOR TESTING)"

    log_warn "WARNING: This operation will KILL a container and may leave the cluster in a compromised state!"
    log_warn "Only use this for testing the colocation resolution feature."
    echo ""

    log "Strategy:"
    log "  1. Find partition X: PRIMARY on host P, BACKUP on host B"
    log "  2. Find partition Y: BACKUP on host P (primary NOT on B)"
    log "  3. Kill partition X's BACKUP on host B"
    log "  4. Relocate partition Y's BACKUP from P to B"
    log "  5. Result: X's backup can't recover - only free container is on P (same as primary)"
    echo ""

    if [[ "$AUTO_CONFIRM" != "true" ]]; then
        read -r -p "Are you sure you want to create a blocked scenario? (yes/NO): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log "Aborted by user"
            return 1
        fi
    fi

    # Get current cluster state
    local space_instances
    space_instances=$(rest_get_space_instances "$SPACE_NAME")

    if [[ -z "$space_instances" ]] || [[ "$space_instances" == "[]" ]]; then
        log_error "Cannot query space instances"
        return 1
    fi

    # Build partition map: partition_id -> {PRIMARY: {ip, container, pid}, BACKUP: {ip, container, pid}}
    log "Step 1: Analyzing cluster state..."

    local partition_data
    partition_data=$(echo "$space_instances" | jq -r '
        .[] |
        "\(.partitionId)|\(.mode)|\(.containerId)"
    ' 2>/dev/null)

    # Find partition X and Y using the correct strategy
    local x_partition="" x_primary_host="" x_backup_host="" x_backup_pid=""
    local y_partition="" y_instance="" y_backup_host=""

    # First pass: build a map of all partitions
    declare -A partition_primary_host partition_primary_container
    declare -A partition_backup_host partition_backup_container partition_backup_pid

    while IFS='|' read -r pid mode container; do
        [[ -z "$pid" ]] && continue
        local hostname="${container%%~*}"
        local ip
        ip=$(extract_ip_from_hostname "$hostname")
        local process_pid="${container##*~}"

        if [[ "$mode" == "PRIMARY" ]]; then
            partition_primary_host[$pid]="$ip"
            partition_primary_container[$pid]="$container"
        elif [[ "$mode" == "BACKUP" ]]; then
            partition_backup_host[$pid]="$ip"
            partition_backup_container[$pid]="$container"
            partition_backup_pid[$pid]="$process_pid"
        fi
    done <<< "$partition_data"

    # Find partition X: has both PRIMARY and BACKUP on different hosts
    for pid in "${!partition_primary_host[@]}"; do
        local p_host="${partition_primary_host[$pid]}"
        local b_host="${partition_backup_host[$pid]}"

        [[ -z "$p_host" || -z "$b_host" ]] && continue
        [[ "$p_host" == "$b_host" ]] && continue

        # Found a candidate for X, now find Y
        # Y needs: BACKUP on X's primary host (p_host), PRIMARY not on X's backup host (b_host)
        for y_pid in "${!partition_primary_host[@]}"; do
            [[ "$y_pid" == "$pid" ]] && continue

            local y_p_host="${partition_primary_host[$y_pid]}"
            local y_b_host="${partition_backup_host[$y_pid]}"

            [[ -z "$y_p_host" || -z "$y_b_host" ]] && continue

            # Y's backup must be on X's primary host
            # Y's primary must NOT be on X's backup host (to allow relocation there)
            if [[ "$y_b_host" == "$p_host" && "$y_p_host" != "$b_host" ]]; then
                x_partition=$((pid + 1))
                x_primary_host="$p_host"
                x_backup_host="$b_host"
                x_backup_pid="${partition_backup_pid[$pid]}"

                y_partition=$((y_pid + 1))

                # Query REST API to find the actual BACKUP instance for partition Y
                local y_backup_space_id
                y_backup_space_id=$(echo "$space_instances" | jq -r \
                    --argjson ypid "$y_pid" \
                    '.[] | select(.partitionId == $ypid and .mode == "BACKUP") | .id' \
                    2>/dev/null | head -1)

                # Extract suffix from space ID and construct service instance ID
                local y_suffix="${y_backup_space_id##*~}"  # e.g., "3_1" or "3_2"
                y_instance="${SERVICE_NAME}~${y_suffix}"
                y_backup_host="$y_b_host"

                debug "Found pair: X=P${x_partition}, Y=P${y_partition}"
                break 2
            fi
        done
    done

    if [[ -z "$x_partition" || -z "$y_partition" ]]; then
        log_error "Could not find suitable partition pair for blocked scenario"
        return 1
    fi

    log ""
    log "Partition X: $x_partition"
    log "  PRIMARY on: $x_primary_host"
    log "  BACKUP on: $x_backup_host (will be killed, PID: $x_backup_pid)"
    log ""
    log "Partition Y: $y_partition"
    log "  BACKUP on: $y_backup_host (= X's primary host)"
    log "  Will relocate TO: $x_backup_host"
    log ""
    log "After relocation, free container will be on $x_primary_host"
    log "X's backup can't recover there (same as X's primary) = BLOCKED!"
    echo ""

    # Step 2: Kill X's backup and race to relocate Y's backup
    log "Step 2: Killing partition $x_partition backup and racing to relocate..."

    # Kill in background
    ssh "$x_backup_host" "kill -9 $x_backup_pid" 2>/dev/null &
    local kill_pid=$!

    # Tight polling loop (0.1s interval, 100 attempts = 10 seconds max)
    local max_attempts=100
    local attempt=0
    local success=false
    local host_pattern
    host_pattern=$(echo "$x_backup_host" | sed 's/\./-/g')

    while [[ $attempt -lt $max_attempts ]]; do
        sleep 0.1
        ((attempt++)) || true

        # Look for free container on x_backup_host
        local free_container
        free_container=$(curl -sk -u $_USER:$_PASS "http://${ACTIVE_MANAGER}:8090/v2/containers" 2>/dev/null | \
            jq -r ".[] | select(.instances | length == 0) | .id" 2>/dev/null | \
            grep -i "$host_pattern" | head -1 || true)

        if [[ -n "$free_container" ]]; then
            log "  Attempt $attempt: Found free container on $x_backup_host"
            log "  Relocating partition $y_partition backup..."

            local response
            response=$(curl -sk -u $_USER:$_PASS -X POST "http://${ACTIVE_MANAGER}:8090/v2/pus/${SERVICE_NAME}/instances/${y_instance}/relocate?containerId=${free_container}" 2>&1)

            if echo "$response" | grep -qi "error"; then
                log_warn "  Relocate response: $response"
            else
                log_success "  Relocation initiated: $response"
                success=true
            fi
            break
        fi

        [[ $((attempt % 20)) -eq 0 ]] && debug "  Attempt $attempt: waiting for free container on $x_backup_host..."
    done

    # Wait for background kill to complete
    wait $kill_pid 2>/dev/null || true

    if [[ "$success" != "true" ]]; then
        log_warn "Could not find free container in time - scenario may not be fully created"
    fi

    # Step 3: Verify immediately (before GigaSpaces can spin up new containers)
    log ""
    log "Step 3: Verifying scenario (checking immediately)..."
    sleep 1  # Brief pause for relocation to complete

    # Global variable to store check result
    CHECK_RESULT=""

    # Function to check and report state (sets CHECK_RESULT)
    check_blocked_state() {
        local check_label="$1"
        local instances free_ctrs total_inst

        instances=$(rest_get_space_instances "$SPACE_NAME")
        total_inst=$(echo "$instances" | jq 'length' 2>/dev/null)
        free_ctrs=$(curl -sk -u $_USER:$_PASS "http://${ACTIVE_MANAGER}:8090/v2/containers" 2>/dev/null | jq -r '.[] | select(.instances | length == 0) | .id' 2>/dev/null)

        log ""
        log "=== $check_label ==="
        log "Total instances: $total_inst"

        # Count instances per host (extract hosts from data)
        log ""
        log "Instance distribution:"
        local host_counts
        host_counts=$(echo "$instances" | jq -r '.[].containerId' 2>/dev/null | while read -r cid; do
            [[ -z "$cid" ]] && continue
            local h="${cid%%~*}"
            if [[ "$h" == *"91"* ]]; then echo "10.0.1.91"
            elif [[ "$h" == *"57"* ]]; then echo "10.0.1.57"
            elif [[ "$h" == *"203"* ]]; then echo "10.0.1.203"
            elif [[ "$h" == *"179"* ]]; then echo "10.0.1.179"
            fi
        done | sort | uniq -c | sort -rn)

        if [[ -n "$host_counts" ]]; then
            while read -r cnt hst; do
                [[ -z "$hst" ]] && continue
                log "  $hst: $cnt instances"
            done <<< "$host_counts"
        fi

        # Check free containers
        log ""
        log "Free containers:"
        local free_host=""
        if [[ -z "$free_ctrs" ]]; then
            log "  (none)"
        else
            while read -r cid; do
                [[ -z "$cid" ]] && continue
                local ch="${cid%%~*}"
                ch=$(extract_ip_from_hostname "$ch")
                log "  $ch: $cid"
                free_host="$ch"
            done <<< "$free_ctrs"
        fi

        # Check for missing backups
        local expected_parts missing_backups=()
        expected_parts=$(echo "$instances" | jq '[.[].partitionId] | max + 1' 2>/dev/null)

        for ((p=0; p<expected_parts; p++)); do
            local has_backup
            has_backup=$(echo "$instances" | jq -r ".[] | select(.partitionId == $p and .mode == \"BACKUP\") | .id" 2>/dev/null | head -1)
            if [[ -z "$has_backup" ]]; then
                missing_backups+=($((p + 1)))
            fi
        done

        if [[ ${#missing_backups[@]} -gt 0 ]]; then
            log ""
            log_warn "Missing backups: ${missing_backups[*]}"

            # Check if any missing backup is blocked by colocation
            for mp in "${missing_backups[@]}"; do
                local mp_idx=$((mp - 1))
                local mp_primary_container mp_primary_host
                mp_primary_container=$(echo "$instances" | jq -r ".[] | select(.partitionId == $mp_idx and .mode == \"PRIMARY\") | .containerId" 2>/dev/null | head -1)
                if [[ -n "$mp_primary_container" ]]; then
                    mp_primary_host="${mp_primary_container%%~*}"
                    mp_primary_host=$(extract_ip_from_hostname "$mp_primary_host")
                    if [[ "$mp_primary_host" == "$free_host" ]]; then
                        log_success "BLOCKED: Partition $mp backup cannot recover - primary is on $free_host (same as free container)"
                        CHECK_RESULT="BLOCKED:$mp:$free_host"
                        return 0
                    fi
                fi
            done
            CHECK_RESULT="MISSING:${missing_backups[*]}"
            return 0
        fi

        CHECK_RESULT="OK:$total_inst"
        return 0
    }

    # Immediate check
    check_blocked_state "Immediate Check (t+1s)"
    local result1="$CHECK_RESULT"

    # If we found a blocked partition immediately, success!
    if [[ "$result1" == BLOCKED:* ]]; then
        local blocked_info="${result1#BLOCKED:}"
        local blocked_part="${blocked_info%%:*}"
        local blocked_host="${blocked_info#*:}"
        echo ""
        log_success "SUCCESS! Colocation-blocked scenario created:"
        log "  Partition $blocked_part backup is MISSING"
        log "  Free container is on $blocked_host (same as partition's primary)"
        log "  Backup cannot recover due to colocation constraint"
        log ""
        log "Run the rebalancer to test resolution:"
        log "  $0 -v --execute"
        return 0
    fi

    # Check again after 5 seconds to see if situation persists
    log ""
    log "Waiting 5 more seconds to check if scenario persists..."
    sleep 5

    check_blocked_state "Delayed Check (t+6s)"
    local result2="$CHECK_RESULT"

    if [[ "$result2" == BLOCKED:* ]]; then
        local blocked_info="${result2#BLOCKED:}"
        local blocked_part="${blocked_info%%:*}"
        local blocked_host="${blocked_info#*:}"
        echo ""
        log_success "SUCCESS! Colocation-blocked scenario persists:"
        log "  Partition $blocked_part backup is MISSING"
        log "  Free container is on $blocked_host (same as partition's primary)"
        log ""
        log "Run the rebalancer to test resolution:"
        log "  $0 -v --execute"
        return 0
    fi

    # Check if we at least created an imbalance (free container on target host)
    local final_free
    final_free=$(curl -sk -u $_USER:$_PASS "http://${ACTIVE_MANAGER}:8090/v2/containers" 2>/dev/null | jq -r '.[] | select(.instances | length == 0) | .id' 2>/dev/null | head -1)

    if [[ -n "$final_free" ]]; then
        local final_free_host="${final_free%%~*}"
        final_free_host=$(extract_ip_from_hostname "$final_free_host")

        if [[ "$final_free_host" == "$x_primary_host" ]]; then
            echo ""
            log_success "PARTIAL SUCCESS: Created imbalance with free container on $x_primary_host"
            log "  All backups recovered, but instance distribution is uneven"
            log "  This can still be used to test the rebalancer"
            log ""
            log "Run the rebalancer:"
            log "  $0 -v --execute"
            return 0
        fi
    fi

    # If we got here with missing backups, still partial success
    if [[ "$result2" == MISSING:* ]]; then
        local missing="${result2#MISSING:}"
        echo ""
        log_warn "PARTIAL: Missing backups ($missing) but not blocked by colocation"
        log "GigaSpaces may recover them to a different host"
        return 0
    fi

    echo ""
    log_warn "Scenario not created - GigaSpaces auto-recovery was too fast"
    log "All backups recovered and no useful imbalance was created"
    log "Try running again - timing varies"
    return 1
}

################################################################################
# Intelligent Rebalancing Functions
################################################################################

find_relocatable_backup() {
    local source_host="$1"
    local target_host="$2"

    debug "Finding relocatable backup: $source_host -> $target_host"

    # Query space instances via REST API to get actual PRIMARY/BACKUP modes
    local space_instances
    space_instances=$(rest_get_space_instances "$SPACE_NAME")

    if ! command -v jq &> /dev/null || [[ "$space_instances" == "[]" ]]; then
        log_error "Cannot query space instances - jq not available or REST API failed"
        return 1
    fi

    # Find all BACKUP instances on source_host
    while IFS='|' read -r partition instance_id container_id; do
        [[ -z "$partition" ]] && continue

        # Extract host from container ID
        local hostname="${container_id%%~*}"
        local backup_host
        backup_host=$(extract_ip_from_hostname "$hostname")

        if [[ "$backup_host" == "$source_host" ]]; then
            debug "Checking backup partition $partition on $source_host"

            # Find PRIMARY for this partition
            local primary_container primary_host
            primary_container=$(echo "$space_instances" | jq -r ".[] | select(.partitionId == $partition and .mode == \"PRIMARY\") | .containerId" 2>/dev/null | head -1)

            if [[ -n "$primary_container" ]]; then
                local primary_hostname="${primary_container%%~*}"
                primary_host=$(extract_ip_from_hostname "$primary_hostname")

                # Check if primary is NOT on target host (to avoid colocation)
                if [[ "$primary_host" != "$target_host" ]]; then
                    # partition is 0-based (from REST API partitionId)
                    local partition_display=$((partition + 1))
                    debug "Found candidate: Partition $partition_display (primary on $primary_host, backup on $source_host)"
                    # Service instance IDs use 1-based partition in the name
                    local service_instance_id="${SERVICE_NAME}~${partition_display}_${instance_id##*_}"
                    # Return: partition_idx (0-based) | service_instance_id | primary_host
                    echo "${partition}|${service_instance_id}|${primary_host}"
                    return 0
                else
                    debug "Skipping partition $((partition + 1)) - primary is on target host $target_host"
                fi
            fi
        fi
    done < <(echo "$space_instances" | jq -r '.[] | select(.mode == "BACKUP") | "\(.partitionId)|\(.id)|\(.containerId)"' 2>/dev/null)

    log_warn "No relocatable backup found from $source_host to $target_host"
    return 1
}

find_demote_candidate() {
    local over_primary_host="$1"
    local under_primary_host="$2"

    debug "Finding demote candidate: primary on $over_primary_host, backup on $under_primary_host"

    # Query space instances via REST API to get actual PRIMARY/BACKUP modes
    local space_instances
    space_instances=$(rest_get_space_instances "$SPACE_NAME")

    if ! command -v jq &> /dev/null || [[ "$space_instances" == "[]" ]]; then
        log_error "Cannot query space instances - jq not available or REST API failed"
        return 1
    fi

    # Find all PRIMARY instances on over_primary_host
    while IFS='|' read -r partition instance_id container_id; do
        [[ -z "$partition" ]] && continue

        # Extract host from container ID
        local hostname="${container_id%%~*}"
        local primary_host
        primary_host=$(extract_ip_from_hostname "$hostname")

        if [[ "$primary_host" == "$over_primary_host" ]]; then
            debug "Checking primary partition $partition on $over_primary_host"

            # Find BACKUP for this partition
            local backup_container backup_host
            backup_container=$(echo "$space_instances" | jq -r ".[] | select(.partitionId == $partition and .mode == \"BACKUP\") | .containerId" 2>/dev/null | head -1)

            if [[ -n "$backup_container" ]]; then
                local backup_hostname="${backup_container%%~*}"
                backup_host=$(extract_ip_from_hostname "$backup_hostname")

                # Check if backup is on under_primary_host
                if [[ "$backup_host" == "$under_primary_host" ]]; then
                    # partition is 0-based (from REST API partitionId)
                    local partition_display=$((partition + 1))
                    debug "Found candidate: Partition $partition_display (primary on $over_primary_host, backup on $under_primary_host)"
                    # Service instance IDs use 1-based partition in the name
                    local service_instance_id="${SERVICE_NAME}~${partition_display}_${instance_id##*_}"
                    # Return: partition_idx (0-based) | service_instance_id | backup_host
                    echo "${partition}|${service_instance_id}|${backup_host}"
                    return 0
                else
                    debug "Skipping partition $partition - backup is on $backup_host, not $under_primary_host"
                fi
            fi
        fi
    done < <(echo "$space_instances" | jq -r '.[] | select(.mode == "PRIMARY") | "\(.partitionId)|\(.id)|\(.containerId)"' 2>/dev/null)

    log_warn "No demote candidate found on $over_primary_host with backup on $under_primary_host"
    return 1
}

################################################################################
# Phase 1: Discovery and State Collection
################################################################################

extract_ip_from_hostname() {
    local hostname="$1"

    # Handle empty input
    if [[ -z "$hostname" ]]; then
        debug "extract_ip_from_hostname: empty hostname provided"
        echo ""
        return 1
    fi

    # Method 1: Already an IP address - return as-is
    # Matches IPv4 pattern: X.X.X.X where X is 1-3 digits
    if [[ "$hostname" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        debug "extract_ip_from_hostname: '$hostname' is already an IP"
        echo "$hostname"
        return 0
    fi

    # Method 2: DNS resolution using 'host' command
    if command -v host &>/dev/null; then
        local host_output
        host_output=$(host "$hostname" 2>/dev/null)

        if [[ $? -eq 0 ]]; then
            # Parse output: "hostname has address X.X.X.X"
            local resolved_ip
            resolved_ip=$(echo "$host_output" | grep -oE 'has address [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -1 | awk '{print $3}')

            if [[ -n "$resolved_ip" ]]; then
                debug "extract_ip_from_hostname: resolved '$hostname' to '$resolved_ip' via DNS"
                echo "$resolved_ip"
                return 0
            fi
        fi
        debug "extract_ip_from_hostname: DNS resolution failed for '$hostname'"
    else
        debug "extract_ip_from_hostname: 'host' command not available"
    fi

    # Method 3: Fallback to /etc/hosts lookup
    if [[ -r /etc/hosts ]]; then
        local hosts_ip
        # Match hostname as a word boundary to avoid partial matches
        # Format: IP_ADDRESS hostname [aliases...]
        hosts_ip=$(grep -E "^[^#]*[[:space:]]$hostname([[:space:]]|$)" /etc/hosts 2>/dev/null | head -1 | awk '{print $1}')

        if [[ -n "$hosts_ip" && "$hosts_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            debug "extract_ip_from_hostname: resolved '$hostname' to '$hosts_ip' via /etc/hosts"
            echo "$hosts_ip"
            return 0
        fi
        debug "extract_ip_from_hostname: '$hostname' not found in /etc/hosts"
    fi

    # Resolution failed - log warning and return empty string
    log_warn "extract_ip_from_hostname: unable to resolve '$hostname' to IP address"
    echo ""
    return 1
}

discover_cluster_state() {
    print_section "Phase 1: Discovering Cluster State"

    # Clear state file to avoid double-counting on re-discovery
    > "$STATE_FILE"

    # Get service status
    log "Checking service: $SERVICE_NAME"
    local service_info
    service_info=$(gs_service_info "$SERVICE_NAME")

    if [[ -z "$service_info" ]]; then
        abort "Service '$SERVICE_NAME' not found. Check service name."
    fi

    if ! echo "$service_info" | grep -q "^Status"; then
        abort "Unexpected service info format. GigaSpaces CLI compatibility issue?"
    fi

    local status
    local planned
    local actual

    status=$(echo "$service_info" | grep "^Status" | awk '{print $2}' || echo "unknown")
    planned=$(echo "$service_info" | grep "^Planned Instances" | awk '{print $3}' || echo "0")
    actual=$(echo "$service_info" | grep "^Actual Instances" | awk '{print $3}' || echo "0")

    log "Service Status: $status"
    log "Planned Instances: $planned"
    log "Actual Instances: $actual"

    # Validate service status - only run if compromised or intact
    if [[ "$status" != "compromised" && "$status" != "intact" ]]; then
        log_error "Service status is '$status' - script only runs when status is 'compromised' or 'intact'"
        abort "Aborting due to invalid service status. Current status: $status"
    fi

    if [[ "$status" == "compromised" ]]; then
        log_warn "Service is in COMPROMISED state - rebalancing needed"
    elif [[ "$status" == "intact" ]]; then
        log_success "Service is in INTACT state"
    fi

    # Get all instances
    log "Retrieving instance distribution..."
    local instances
    instances=$(gs_service_list_instances "$SERVICE_NAME")

    if [[ -z "$instances" ]]; then
        abort "No instances found for service $SERVICE_NAME"
    fi

    # Get actual PRIMARY/BACKUP status from REST API
    debug "Querying actual PRIMARY/BACKUP modes from REST API"
    local space_instances
    space_instances=$(rest_get_space_instances "$SPACE_NAME")

    # Parse instances and build state
    # Use process substitution to avoid subshell issues
    while read -r line; do
        # Skip header and empty lines
        if [[ "$line" =~ ^INSTANCE || -z "$line" ]]; then
            continue
        fi

        local instance_id
        local hostname
        local host

        instance_id=$(echo "$line" | awk '{print $1}')
        hostname=$(echo "$line" | awk '{print $2}')
        host=$(extract_ip_from_hostname "$hostname")

        # Extract partition number from instance_id
        if [[ "$instance_id" =~ ~([0-9]+)_([12])$ ]]; then
            local partition="${BASH_REMATCH[1]}"
            local instance_suffix="${BASH_REMATCH[2]}"

            # Determine actual mode from REST API space instances
            local space_instance_id="${SPACE_NAME}~${partition}_${instance_suffix}"
            local actual_mode=""

            if command -v jq &> /dev/null && [[ "$space_instances" != "[]" ]]; then
                actual_mode=$(echo "$space_instances" | jq -r ".[] | select(.id == \"$space_instance_id\") | .mode" 2>/dev/null)
            fi

            # Convert mode to lowercase (PRIMARY -> primary, BACKUP -> backup)
            if [[ "$actual_mode" == "PRIMARY" ]]; then
                echo "${partition},primary,$host,$instance_id" >> "$STATE_FILE"
            elif [[ "$actual_mode" == "BACKUP" ]]; then
                echo "${partition},backup,$host,$instance_id" >> "$STATE_FILE"
            else
                debug "Could not determine mode for $instance_id, skipping"
            fi
        else
            debug "Skipping instance with unexpected format: $instance_id"
        fi
    done < <(echo "$instances" | grep -E "^${SERVICE_NAME}")

    if [[ ! -s "$STATE_FILE" ]]; then
        abort "No instances discovered. Is the service running and deployed?"
    fi

    local total_instances
    total_instances=$(wc -l < "$STATE_FILE" | tr -d ' ')
    log_success "Discovered $total_instances instances"
}

get_instance_host() {
    local instance_id="$1"
    grep "$instance_id" "$STATE_FILE" | cut -d',' -f3 || echo ""
}

get_instance_count_on_host() {
    local host="$1"
    local count
    count=$(grep -c ",$host," "$STATE_FILE" 2>/dev/null) || count=0
    echo "$count"
}

get_primary_count_on_host() {
    local host="$1"
    local count
    count=$(grep -c ",primary,$host," "$STATE_FILE" 2>/dev/null) || count=0
    echo "$count"
}

get_backup_count_on_host() {
    local host="$1"
    local count
    count=$(grep -c ",backup,$host," "$STATE_FILE" 2>/dev/null) || count=0
    echo "$count"
}

################################################################################
# Phase 2: Problem Detection
################################################################################

detect_problems() {
    print_section "Phase 2: Detecting Problems"

    local space_servers
    local num_servers
    local total_partitions

    space_servers=($(get_space_servers))
    num_servers=${#space_servers[@]}

    if [[ $num_servers -eq 0 ]]; then
        abort "No space servers found in configuration"
    fi

    total_partitions=$(cut -d',' -f1 "$STATE_FILE" | sort -u | wc -l | tr -d ' ')

    if [[ $total_partitions -eq 0 ]]; then
        abort "No partitions found in state data"
    fi

    log "Total partitions: $total_partitions"
    log "Space servers: $num_servers"

    # Calculate expected distribution
    local expected_instances=$((total_partitions * 2 / num_servers))
    local expected_primaries=$((total_partitions / num_servers))

    log "Expected per host: $expected_instances instances ($expected_primaries P + $expected_primaries B)"

    # Track problems
    local problems=0

    # 1. Detect missing instances
    # STATE_FILE uses 1-based partition numbers (1 to total_partitions)
    echo ""
    log "Checking for missing instances..."
    local partition
    for partition in $(seq 1 "$total_partitions"); do
        local primary_exists
        local backup_exists

        # Use awk for exact field matching (STATE_FILE uses 1-based)
        primary_exists=$(awk -F',' -v p="$partition" 'BEGIN{c=0} $1 == p && $2 == "primary" {c++} END{print c}' "$STATE_FILE")
        backup_exists=$(awk -F',' -v p="$partition" 'BEGIN{c=0} $1 == p && $2 == "backup" {c++} END{print c}' "$STATE_FILE")

        # Ensure we have valid numbers
        primary_exists=${primary_exists:-0}
        backup_exists=${backup_exists:-0}

        if [[ "$primary_exists" -eq 0 ]]; then
            log_warn "MISSING: Partition $partition primary not found"
            ((problems++)) || true
        fi

        if [[ "$backup_exists" -eq 0 ]]; then
            log_warn "MISSING: Partition $partition backup not found"
            ((problems++)) || true
        fi
    done

    # 2. Detect colocation violations
    echo ""
    log "Checking for primary/backup colocation violations..."
    for partition in $(seq 1 "$total_partitions"); do
        local primary_host
        local backup_host

        # Use awk for exact field matching (STATE_FILE uses 1-based)
        primary_host=$(awk -F',' -v p="$partition" '$1 == p && $2 == "primary" {print $3; exit}' "$STATE_FILE")
        backup_host=$(awk -F',' -v p="$partition" '$1 == p && $2 == "backup" {print $3; exit}' "$STATE_FILE")

        if [[ -n "$primary_host" && -n "$backup_host" && "$primary_host" == "$backup_host" ]]; then
            log_warn "VIOLATION: Partition $partition has primary and backup on same host ($primary_host)"
            ((problems++)) || true
        fi
    done

    # 3. Detect uneven distribution
    echo ""
    log "Checking distribution across hosts..."
    local host
    for host in "${space_servers[@]}"; do
        local total
        local primaries
        local backups

        total=$(get_instance_count_on_host "$host")
        primaries=$(get_primary_count_on_host "$host")
        backups=$(get_backup_count_on_host "$host")

        printf "  %-15s: %2d instances (%2d P, %2d B)" "$host" "$total" "$primaries" "$backups"

        if [[ "$total" -lt "$expected_instances" ]]; then
            echo -e " ${YELLOW}[UNDER-CAPACITY]${NC}"
            ((problems++)) || true
        elif [[ "$total" -gt "$expected_instances" ]]; then
            echo -e " ${YELLOW}[OVER-CAPACITY]${NC}"
            ((problems++)) || true
        elif [[ "$primaries" -ne "$expected_primaries" ]]; then
            echo -e " ${YELLOW}[IMBALANCED P/B]${NC}"
            ((problems++)) || true
        else
            echo -e " ${GREEN}[OK]${NC}"
        fi
    done

    echo ""
    if [[ "$problems" -eq 0 ]]; then
        log_success "No problems detected. Cluster is balanced."
        return 0
    else
        log_warn "Detected $problems problem(s) that need fixing"
        return 1
    fi
}

################################################################################
# Phase 3: Target State Calculation
################################################################################

calculate_target_state() {
    print_section "Phase 3: Calculating Target State"

    local space_servers
    local num_servers
    local total_partitions

    space_servers=($(get_space_servers))
    num_servers=${#space_servers[@]}
    total_partitions=$(cut -d',' -f1 "$STATE_FILE" | sort -u | wc -l | tr -d ' ')

    log "Calculating optimal distribution for $total_partitions partitions across $num_servers servers"

    # Round-robin distribution algorithm:
    # Primary of partition P goes to server (P-1) % num_servers
    # Backup of partition P goes to server P % num_servers (offset by 1)

    echo ""
    log "Target Distribution Algorithm:"
    log "  Primaries: Round-robin starting at server 0"
    log "  Backups:   Round-robin offset by 1 (ensures no colocation)"

    # Calculate expected counts per host
    local expected_per_host=$((total_partitions / num_servers))
    echo ""
    log "Expected per host: $expected_per_host primaries + $expected_per_host backups = $((expected_per_host * 2)) total"

    log_success "Target state calculated"
}

################################################################################
# Phase 4: Migration Plan Generation
################################################################################

generate_migration_plan() {
    print_section "Phase 4: Generating Migration Plan"

    local space_servers
    local num_servers
    local total_partitions

    space_servers=($(get_space_servers))
    num_servers=${#space_servers[@]}
    total_partitions=$(cut -d',' -f1 "$STATE_FILE" | sort -u | wc -l | tr -d ' ')

    > "$PLAN_FILE"  # Clear plan file

    # Step 1: Deploy missing instances
    # STATE_FILE uses 1-based partition numbers (1 to total_partitions)
    log "Analyzing missing instances..."
    local partition
    for partition in $(seq 1 "$total_partitions"); do
        local primary_exists
        local backup_exists

        # Use awk for exact field matching (STATE_FILE uses 1-based)
        primary_exists=$(awk -F',' -v p="$partition" 'BEGIN{c=0} $1 == p && $2 == "primary" {c++} END{print c}' "$STATE_FILE")
        backup_exists=$(awk -F',' -v p="$partition" 'BEGIN{c=0} $1 == p && $2 == "backup" {c++} END{print c}' "$STATE_FILE")

        # Ensure we have valid numbers
        primary_exists=${primary_exists:-0}
        backup_exists=${backup_exists:-0}

        # Calculate target host using round-robin (convert 1-based to 0-based for array index)
        local server_idx=$(((partition - 1) % num_servers))

        # Validate index is within bounds
        if [[ $server_idx -ge $num_servers ]]; then
            log_error "Internal error: server index $server_idx out of bounds for $num_servers servers"
            continue
        fi

        local target_host="${space_servers[$server_idx]}"

        if [[ "$backup_exists" -eq 0 ]]; then
            # Instance IDs use 1-based partition in the name
            local instance_id="${SERVICE_NAME}~${partition}_2"
            echo "DEPLOY_MISSING|$instance_id|$target_host||$partition|Deploy missing backup" >> "$PLAN_FILE"
            debug "Plan: Deploy $instance_id to $target_host"
        fi
    done

    # Step 2: Fix colocation violations (relocate backups)
    log "Analyzing colocation violations..."
    for partition in $(seq 1 "$total_partitions"); do
        local primary_host
        local backup_host

        # Use awk for exact field matching (STATE_FILE uses 1-based)
        primary_host=$(awk -F',' -v p="$partition" '$1 == p && $2 == "primary" {print $3; exit}' "$STATE_FILE")
        backup_host=$(awk -F',' -v p="$partition" '$1 == p && $2 == "backup" {print $3; exit}' "$STATE_FILE")

        if [[ -n "$primary_host" && -n "$backup_host" && "$primary_host" == "$backup_host" ]]; then
            # Instance IDs use 1-based partition in the name
            local instance_id="${SERVICE_NAME}~${partition}_2"
            local server_idx=$(((partition - 1) % num_servers))

            if [[ $server_idx -ge $num_servers ]]; then
                log_error "Internal error: server index out of bounds"
                continue
            fi

            local target_host="${space_servers[$server_idx]}"

            echo "RELOCATE_BACKUP|$instance_id|$backup_host|$target_host|$partition|Fix colocation violation" >> "$PLAN_FILE"
            debug "Plan: Relocate $instance_id from $backup_host to $target_host"
        fi
    done

    # Step 3: Rebalance primaries across hosts
    log "Analyzing primary distribution..."
    local expected_primaries=$((total_partitions / num_servers))

    local host
    for host in "${space_servers[@]}"; do
        local current_primaries
        current_primaries=$(get_primary_count_on_host "$host")

        if [[ "$current_primaries" -gt "$expected_primaries" ]]; then
            local excess=$((current_primaries - expected_primaries))
            debug "Host $host has $excess excess primaries"

            # Find partitions to demote
            # Collect to array first to avoid subshell issue
            local demote_count=0
            while read -r line; do
                if [[ $demote_count -ge $excess ]]; then
                    break
                fi

                local partition
                local instance_id

                partition=$(echo "$line" | cut -d',' -f1)
                instance_id=$(echo "$line" | cut -d',' -f4)

                echo "DEMOTE_PRIMARY|$instance_id|$host||$partition|Rebalance primaries" >> "$PLAN_FILE"
                debug "Plan: Demote $instance_id on $host"

                demote_count=$((demote_count + 1))
            done < <(grep ",primary,$host," "$STATE_FILE")
        fi
    done

    # Step 4: Rebalance backups across hosts
    log "Analyzing backup distribution..."
    local expected_backups=$((total_partitions / num_servers))

    # Find over-capacity and under-capacity hosts for backups
    local over_capacity_hosts=()
    local under_capacity_hosts=()

    for host in "${space_servers[@]}"; do
        local current_backups
        current_backups=$(get_backup_count_on_host "$host")

        if [[ "$current_backups" -gt "$expected_backups" ]]; then
            over_capacity_hosts+=("$host:$((current_backups - expected_backups))")
            debug "Host $host has $((current_backups - expected_backups)) excess backups"
        elif [[ "$current_backups" -lt "$expected_backups" ]]; then
            under_capacity_hosts+=("$host:$((expected_backups - current_backups))")
            debug "Host $host needs $((expected_backups - current_backups)) more backups"
        fi
    done

    # Relocate backups from over-capacity to under-capacity hosts
    for over_entry in "${over_capacity_hosts[@]}"; do
        local over_host="${over_entry%%:*}"
        local over_excess="${over_entry##*:}"

        for under_entry in "${under_capacity_hosts[@]}"; do
            [[ "$over_excess" -le 0 ]] && break

            local under_host="${under_entry%%:*}"
            local under_need="${under_entry##*:}"

            [[ "$under_need" -le 0 ]] && continue

            # Find backups on over_host that can be moved to under_host
            # (their primary must NOT be on under_host)
            while read -r line; do
                [[ "$over_excess" -le 0 ]] && break
                [[ "$under_need" -le 0 ]] && break

                local partition primary_host instance_id
                partition=$(echo "$line" | cut -d',' -f1)
                instance_id=$(echo "$line" | cut -d',' -f4)

                # Get primary host for this partition
                primary_host=$(awk -F',' -v p="$partition" '$1 == p && $2 == "primary" {print $3; exit}' "$STATE_FILE")

                # Can only move if primary is NOT on the target host
                if [[ "$primary_host" != "$under_host" ]]; then
                    echo "RELOCATE_BACKUP|$instance_id|$over_host|$under_host|$partition|Rebalance backups" >> "$PLAN_FILE"
                    debug "Plan: Relocate backup $instance_id from $over_host to $under_host"
                    over_excess=$((over_excess - 1))
                    under_need=$((under_need - 1))
                fi
            done < <(grep ",backup,$over_host," "$STATE_FILE")

            # Update under_entry with new need value
            under_capacity_hosts=("${under_capacity_hosts[@]/$under_entry/$under_host:$under_need}")
        done
    done

    # Number the steps after generating all entries
    if [[ -s "$PLAN_FILE" ]]; then
        # Add step numbers as first field
        local step_num=0
        local temp_plan
        temp_plan=$(mktemp)

        while IFS='|' read -r operation rest; do
            step_num=$((step_num + 1))
            echo "$step_num|$operation|$rest" >> "$temp_plan"
        done < "$PLAN_FILE"

        mv "$temp_plan" "$PLAN_FILE"
    fi

    local total_steps
    total_steps=$(wc -l < "$PLAN_FILE" | tr -d ' ')
    log_success "Generated migration plan with $total_steps steps"
}

display_plan() {
    print_section "Migration Plan"

    if [[ ! -s "$PLAN_FILE" ]]; then
        log_success "No migration needed - cluster is already balanced!"
        return 0
    fi

    echo ""
    printf "%-6s %-20s %-12s %-20s %-40s\n" "STEP" "OPERATION" "PARTITION" "TARGET/HOST" "REASON"
    printf "%-6s %-20s %-12s %-20s %-40s\n" "----" "---------" "---------" "-----------" "------"

    while IFS='|' read -r step_id operation instance from_host to_host partition reason; do
        case "$operation" in
            DEPLOY_MISSING)
                printf "%-6s %-20s %-12s %-20s %-40s\n" "$step_id" "Deploy Missing" "$partition" "$from_host" "$reason"
                ;;
            RELOCATE_BACKUP)
                printf "%-6s %-20s %-12s %-20s %-40s\n" "$step_id" "Relocate Backup" "$partition" "$from_host -> $to_host" "$reason"
                ;;
            DEMOTE_PRIMARY)
                printf "%-6s %-20s %-12s %-20s %-40s\n" "$step_id" "Demote Primary" "$partition" "$from_host" "$reason"
                ;;
        esac
    done < "$PLAN_FILE"

    echo ""
    return 1  # Indicate there are steps to execute
}

################################################################################
# Phase 5: Execution Engine
################################################################################
#
# Verification Strategy:
# - All operations are verified before proceeding to next step
# - Verification uses 2-attempt retry logic with 30-second wait between attempts
# - Each attempt polls for up to 90 seconds (VERIFICATION_TIMEOUT)
# - If verification fails after 2 attempts, execution stops with error
#
# Operation Timeouts:
# - Relocation: 10s initial wait + up to 150s verification = max 160s
# - Demote: 15s initial wait + up to 150s verification = max 165s
#
################################################################################

verify_instance_on_host() {
    local instance_id="$1"
    local expected_host="$2"
    local timeout="$VERIFICATION_TIMEOUT"

    debug "Verifying $instance_id is on $expected_host (timeout: ${timeout}s)"

    # Retry logic: 2 attempts with 30-second wait between attempts
    # - Attempt 1: Poll for up to 90 seconds (VERIFICATION_TIMEOUT)
    # - If fails: Wait 30 seconds
    # - Attempt 2: Poll for up to 90 seconds again
    # - Total max time: 90 + 30 + 90 = 210 seconds
    local attempt=1
    local max_attempts=2

    while [[ $attempt -le $max_attempts ]]; do
        if [[ $attempt -eq 2 ]]; then
            log_warn "First verification attempt failed, waiting 30 seconds before retry..."
            sleep 30
            debug "Retrying verification (attempt $attempt/$max_attempts)..."
        fi

        local elapsed=0
        while [[ $elapsed -lt $timeout ]]; do
            local info
            info=$(gs_service_info_instance "$instance_id" 2>/dev/null || echo "")

            if [[ -n "$info" ]]; then
                local actual_host
                actual_host=$(echo "$info" | grep "^Host ID" | awk '{print $3}' | head -1 || echo "")
                actual_host=$(extract_ip_from_hostname "$actual_host")

                if [[ "$actual_host" == "$expected_host" ]]; then
                    debug "Verification passed: $instance_id is on $expected_host"
                    return 0
                fi

                debug "Instance on $actual_host (expected $expected_host), waiting..."
            fi

            sleep 2
            elapsed=$((elapsed + 2))
        done

        attempt=$((attempt + 1))
    done

    log_error "Verification failed: $instance_id not on $expected_host after $max_attempts attempts"
    return 1
}

verify_demote_completed() {
    # @param partition_idx: 0-based partition index (for REST API queries)
    # @param expected_primary_host: IP address expected to host the new primary
    local partition_idx="$1"
    local expected_primary_host="$2"
    local timeout="$VERIFICATION_TIMEOUT"

    debug "Verifying partition $((partition_idx + 1)) primary is now on $expected_primary_host (timeout: ${timeout}s)"

    # Retry logic: 2 attempts with 30-second wait between attempts
    # - Attempt 1: Poll for up to 90 seconds (VERIFICATION_TIMEOUT)
    # - If fails: Wait 30 seconds
    # - Attempt 2: Poll for up to 90 seconds again
    # - Total max time: 90 + 30 + 90 = 210 seconds
    # Note: Uses REST API to check if partition's PRIMARY is on expected host
    local attempt=1
    local max_attempts=2

    while [[ $attempt -le $max_attempts ]]; do
        if [[ $attempt -eq 2 ]]; then
            log_warn "First verification attempt failed, waiting 30 seconds before retry..."
            sleep 30
            debug "Retrying verification (attempt $attempt/$max_attempts)..."
        fi

        local elapsed=0
        while [[ $elapsed -lt $timeout ]]; do
            # Query space instances via REST API
            local space_instances
            space_instances=$(rest_get_space_instances "$SPACE_NAME")

            if command -v jq &> /dev/null && [[ "$space_instances" != "[]" ]]; then
                # Find the PRIMARY instance for this partition (REST API uses 0-based partitionId)
                local primary_instance_id primary_container
                local partition_display=$((partition_idx + 1))
                primary_instance_id=$(echo "$space_instances" | jq -r ".[] | select(.partitionId == $partition_idx and .mode == \"PRIMARY\") | .id" 2>/dev/null | head -1)
                primary_container=$(echo "$space_instances" | jq -r ".[] | select(.partitionId == $partition_idx and .mode == \"PRIMARY\") | .containerId" 2>/dev/null | head -1)

                if [[ -n "$primary_container" ]]; then
                    # Extract hostname from container ID
                    local hostname="${primary_container%%~*}"
                    local actual_host
                    actual_host=$(extract_ip_from_hostname "$hostname")

                    if [[ "$actual_host" == "$expected_primary_host" ]]; then
                        debug "Verification passed: Partition $partition_display primary is now on $expected_primary_host"
                        return 0
                    fi

                    debug "Partition $partition_display primary on $actual_host (expected $expected_primary_host), waiting..."
                else
                    debug "Could not find PRIMARY for partition $partition_display, waiting..."
                fi
            fi

            sleep 2
            elapsed=$((elapsed + 2))
        done

        attempt=$((attempt + 1))
    done

    log_error "Verification failed: Partition $((partition_idx + 1)) primary not on $expected_primary_host after $max_attempts attempts"
    return 1
}

verify_primary_on_host() {
    # Alias for verify_demote_completed
    verify_demote_completed "$@"
}

################################################################################
# Optimal Rebalancing Functions
################################################################################

generate_state_json() {
    # Generate JSON representation of current state for optimal_rebalancer.py
    local space_servers
    space_servers=($(get_space_servers))

    # Start JSON structure
    echo "{"

    # Add hosts array
    echo "  \"hosts\": ["
    local first=true
    for host in "${space_servers[@]}"; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            echo ","
        fi
        echo -n "    \"$host\""
    done
    echo ""
    echo "  ],"

    # Add partitions object
    echo "  \"partitions\": {"

    # Parse STATE_FILE and build partition map
    local partition_ids
    partition_ids=($(cut -d',' -f1 "$STATE_FILE" | sort -u))

    first=true
    for partition in "${partition_ids[@]}"; do
        # Get primary and backup hosts for this partition
        local primary_host backup_host
        primary_host=$(awk -F',' -v p="$partition" '$1 == p && $2 == "primary" {print $3; exit}' "$STATE_FILE")
        backup_host=$(awk -F',' -v p="$partition" '$1 == p && $2 == "backup" {print $3; exit}' "$STATE_FILE")

        if [[ -n "$primary_host" && -n "$backup_host" ]]; then
            if [[ "$first" == "true" ]]; then
                first=false
            else
                echo ","
            fi
            echo "    \"$partition\": {"
            echo "      \"primary\": \"$primary_host\","
            echo "      \"backup\": \"$backup_host\""
            echo -n "    }"
        fi
    done
    echo ""
    echo "  }"
    echo "}"
}

call_optimal_rebalancer() {
    # Call the Python optimal rebalancer and return the operations
    local json_state="$1"
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local rebalancer_script="${script_dir}/optimal_rebalancer.py"

    debug "Calling optimal rebalancer: $rebalancer_script"

    if [[ ! -f "$rebalancer_script" ]]; then
        log_error "Optimal rebalancer script not found: $rebalancer_script"
        return 1
    fi

    # Create temp file for JSON state
    local temp_json
    temp_json=$(mktemp -t rebalancer_state.XXXXXX.json)
    echo "$json_state" > "$temp_json"

    # Build command with optional verbose flag
    local cmd="python3 \"$rebalancer_script\" --json \"$temp_json\""
    if [[ "$VERBOSE" == "true" ]]; then
        cmd="$cmd --verbose"
    fi

    # Call Python script and capture output
    local output
    output=$(eval "$cmd" 2>&1)
    local exit_code=$?

    rm -f "$temp_json"

    if [[ $exit_code -ne 0 ]]; then
        log_error "Optimal rebalancer failed:"
        echo "$output" >&2
        return 1
    fi

    echo "$output"
    return 0
}

parse_operations_from_output() {
    # Parse operations from optimal rebalancer output
    # Format: "Step N: DEMOTE partition X" or "Step N: RELOCATE partition X from Y to Z"
    local output="$1"
    local temp_ops
    temp_ops=$(mktemp -t operations.XXXXXX)

    # Extract operation lines
    echo "$output" | grep -E "^Step [0-9]+:" | while IFS= read -r line; do
        # Extract operation type and partition
        if echo "$line" | grep -q "DEMOTE"; then
            local partition
            partition=$(echo "$line" | grep -oE "partition [0-9]+" | awk '{print $2}')
            if [[ -n "$partition" ]]; then
                echo "DEMOTE|$partition"
            fi
        elif echo "$line" | grep -q "RELOCATE"; then
            local partition from_host to_host
            partition=$(echo "$line" | grep -oE "partition [0-9]+" | awk '{print $2}')
            # This is more complex, would need to parse "from X to Y"
            # For now, just support DEMOTE which is most common
        fi
    done > "$temp_ops"

    cat "$temp_ops"
    rm -f "$temp_ops"
}

execute_optimal_rebalance() {
    print_section "Phase 5: Optimal Rebalancing Execution"

    # Check if Python3 is available
    if ! command -v python3 &> /dev/null; then
        log_warn "Python3 not found - falling back to greedy rebalancing"
        execute_intelligent_rebalance
        return $?
    fi

    # Check for missing instances - optimal rebalancer requires all partitions to be complete
    # Count unique partition IDs and verify each has both primary and backup
    local total_partitions
    total_partitions=$(cut -d',' -f1 "$STATE_FILE" | sort -u | wc -l | tr -d ' ')

    # STATE_FILE uses 1-based partition numbers (1 to total_partitions)
    local missing_count=0
    for partition in $(seq 1 "$total_partitions"); do
        local primary_exists backup_exists
        primary_exists=$(awk -F',' -v p="$partition" 'BEGIN{c=0} $1 == p && $2 == "primary" {c++} END{print c}' "$STATE_FILE")
        backup_exists=$(awk -F',' -v p="$partition" 'BEGIN{c=0} $1 == p && $2 == "backup" {c++} END{print c}' "$STATE_FILE")
        primary_exists=${primary_exists:-0}
        backup_exists=${backup_exists:-0}

        if [[ "$primary_exists" -eq 0 || "$backup_exists" -eq 0 ]]; then
            ((missing_count++)) || true
        fi
    done

    if [[ $missing_count -gt 0 ]]; then
        log_warn "Detected $missing_count missing partition instance(s)"

        # Try to resolve colocation-blocked missing instances
        if [[ "$DRY_RUN" == "false" ]]; then
            log "Attempting to resolve missing instances blocked by colocation..."
            resolve_colocation_blocked_missing

            # Re-discover state after resolution attempt
            log "Re-discovering cluster state after resolution attempt..."
            discover_cluster_state

            # Re-count missing instances
            missing_count=0
            for partition in $(seq 1 "$total_partitions"); do
                local primary_exists backup_exists
                primary_exists=$(awk -F',' -v p="$partition" 'BEGIN{c=0} $1 == p && $2 == "primary" {c++} END{print c}' "$STATE_FILE")
                backup_exists=$(awk -F',' -v p="$partition" 'BEGIN{c=0} $1 == p && $2 == "backup" {c++} END{print c}' "$STATE_FILE")
                primary_exists=${primary_exists:-0}
                backup_exists=${backup_exists:-0}
                if [[ "$primary_exists" -eq 0 || "$backup_exists" -eq 0 ]]; then
                    ((missing_count++)) || true
                fi
            done

            if [[ $missing_count -eq 0 ]]; then
                log_success "All missing instances resolved - continuing with optimal rebalancing"
            else
                log_warn "Still have $missing_count missing instance(s) after resolution attempt"
                log_warn "Optimal rebalancer requires all partitions to be complete - falling back to greedy approach"
                execute_intelligent_rebalance
                return $?
            fi
        else
            log_warn "[DRY RUN] Would attempt to resolve colocation-blocked missing instances"
            log_warn "Falling back to greedy approach for analysis"
            execute_intelligent_rebalance
            return $?
        fi
    fi

    # Manager connection already initialized - verify it's still healthy
    if ! check_manager_health "$ACTIVE_MANAGER"; then
        log_warn "Active manager unavailable, searching for alternative..."
        if ! get_active_manager; then
            abort "Failed to connect to any GigaSpaces manager"
        fi
    fi

    log "Generating current state representation..."
    local json_state
    json_state=$(generate_state_json)

    if [[ -z "$json_state" ]]; then
        log_error "Failed to generate state JSON"
        return 1
    fi

    debug "State JSON generated (${#json_state} bytes)"

    log "Calling optimal rebalancer (A* search algorithm)..."
    local rebalancer_output
    if ! rebalancer_output=$(call_optimal_rebalancer "$json_state"); then
        log_error "Optimal rebalancer failed - falling back to greedy approach"
        execute_intelligent_rebalance
        return $?
    fi

    # Display the solution found (show all steps, not just first 20 lines)
    echo "$rebalancer_output" | sed -n '/EXECUTION PLAN/,$p' || true

    # Parse operations from output
    local operations_file
    operations_file=$(mktemp -t operations.XXXXXX)

    # Extract operations in format: OPERATION|PARTITION|PRIMARY_HOST|BACKUP_HOST
    echo "$rebalancer_output" | awk '
        /^Step [0-9]+:/ { in_step=1; step=$2; gsub(/:/, "", step); next }
        in_step && /Operation:/ { op=$2; next }
        in_step && /Partition:/ { partition=$2; next }
        in_step && /Effect:/ && op == "DEMOTE" {
            # Current line: "Effect: Primary on X becomes backup"
            # Extract X from current line
            for (i=1; i<=NF; i++) {
                if ($i == "on" && $(i+1) != "") {
                    primary_host = $(i+1)
                    break
                }
            }
            # Next line: "        Backup on Y becomes primary"
            getline
            for (i=1; i<=NF; i++) {
                if ($i == "on" && $(i+1) != "") {
                    backup_host = $(i+1)
                    break
                }
            }
            print op "|" partition "|" primary_host "|" backup_host
            in_step=0
        }
    ' > "$operations_file"

    debug "Parsing operations from file: $operations_file"

    local num_operations
    num_operations=$(wc -l < "$operations_file" 2>/dev/null | tr -d ' ' || echo "0")

    debug "Number of operations parsed: $num_operations"
    debug "Operations file content:"
    if [[ "$VERBOSE" == "true" && -f "$operations_file" ]]; then
        cat "$operations_file" >&2
    fi

    if [[ -z "$num_operations" || $num_operations -eq 0 ]]; then
        log "No operations needed - cluster is balanced"
        rm -f "$operations_file"
        return 0
    fi

    log "Optimal solution found: $num_operations operations"

    debug "DRY_RUN mode: $DRY_RUN"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "[DRY RUN] No actual changes made - run with --execute to apply changes"
        rm -f "$operations_file"
        return 0
    fi

    # Execute each operation
    log "Starting execution of $num_operations operations..."

    debug "Operations file exists: $(test -f "$operations_file" && echo 'yes' || echo 'no')"
    debug "Operations file size: $(wc -c < "$operations_file" 2>/dev/null || echo '0')"

    local step=0
    local operations_performed=0

    debug "About to enter while loop..."
    while IFS='|' read -r operation partition primary_host backup_host || [[ -n "$operation" ]]; do
        [[ -z "$operation" ]] && continue
        ((step++)) || true
        debug "Read operation: op=$operation, partition=$partition, primary=$primary_host, backup=$backup_host"
        log "Executing step $step/$num_operations: $operation partition $partition"

        if [[ "$operation" == "DEMOTE" ]]; then
            # Query REST API to find the actual PRIMARY instance for this partition
            # NOTE: Python optimal_rebalancer.py outputs 1-based partition IDs
            # Instance IDs use 1-based partition numbers in the name:
            # dih-tau-space~11_1 = partition 11 (display) = partitionId 10 (REST API)
            local partition_idx=$((partition - 1))

            local space_instances
            space_instances=$(rest_get_space_instances "$SPACE_NAME")

            local space_instance_id
            space_instance_id=$(echo "$space_instances" | jq -r \
                --argjson pid "$partition_idx" \
                '.[] | select(.partitionId == $pid and .mode == "PRIMARY") | .id' \
                2>/dev/null | head -1)

            if [[ -z "$space_instance_id" ]]; then
                log_error "  Cannot find PRIMARY instance for partition $partition"
                rm -f "$operations_file"
                return 1
            fi

            log "  Demoting primary: $space_instance_id (partition $partition)"
            debug "  Current: Primary on $primary_host, Backup on $backup_host"

            local response
            response=$(rest_demote_primary "$SPACE_NAME" "$space_instance_id" "15s")

            if echo "$response" | grep -qi "error"; then
                log_error "  Demote failed: $response"
                rm -f "$operations_file"
                return 1
            fi

            log_success "  Demote initiated - waiting 15 seconds for failover..."
            sleep 15

            # Verify the swap occurred
            # verify_primary_on_host expects 0-based partition ID (for REST API query)
            # partition_idx already calculated above
            log "  Verifying primary swap..."
            if verify_primary_on_host "$partition_idx" "$backup_host"; then
                log_success "  Verification passed: Partition $partition primary now on $backup_host"
                ((operations_performed++)) || true
            else
                log_error "  Verification failed: Primary not on expected host"
                rm -f "$operations_file"
                return 1
            fi
        fi

    done < "$operations_file" || true

    debug "Finished executing operations loop"

    rm -f "$operations_file"

    log_success "Completed $operations_performed operations"
    return 0
}

execute_intelligent_rebalance() {
    print_section "Phase 5: Intelligent Rebalancing Execution"

    # Manager connection already initialized - verify it's still healthy
    if ! check_manager_health "$ACTIVE_MANAGER"; then
        log_warn "Active manager unavailable, searching for alternative..."
        if ! get_active_manager; then
            abort "Failed to connect to any GigaSpaces manager"
        fi
    fi

    local space_servers num_servers total_partitions expected_per_host
    space_servers=($(get_space_servers))
    num_servers=${#space_servers[@]}
    total_partitions=$(cut -d',' -f1 "$STATE_FILE" | sort -u | wc -l | tr -d ' ')
    expected_per_host=$((total_partitions / num_servers))

    log "Analyzing current distribution to determine optimal rebalancing strategy"

    # Analyze current state per host
    declare -A host_totals host_primaries host_backups

    for host in "${space_servers[@]}"; do
        host_totals[$host]=$(get_instance_count_on_host "$host")
        host_primaries[$host]=$(get_primary_count_on_host "$host")
        host_backups[$host]=$(get_backup_count_on_host "$host")

        debug "Host $host: ${host_totals[$host]} total (${host_primaries[$host]}P, ${host_backups[$host]}B)"
    done

    # Identify hosts with issues
    local under_capacity_host="" over_backup_host="" over_primary_host="" under_primary_host=""

    for host in "${space_servers[@]}"; do
        local total=${host_totals[$host]}
        local primaries=${host_primaries[$host]}
        local backups=${host_backups[$host]}

        if [[ $total -lt $((expected_per_host * 2)) ]]; then
            under_capacity_host="$host"
            log "Identified under-capacity host: $host ($total instances, expected $((expected_per_host * 2)))"
        fi

        if [[ $backups -gt $expected_per_host ]]; then
            over_backup_host="$host"
            log "Identified host with excess backups: $host ($backups backups, expected $expected_per_host)"
        fi

        if [[ $primaries -gt $expected_per_host ]]; then
            over_primary_host="$host"
            log "Identified host with excess primaries: $host ($primaries primaries, expected $expected_per_host)"
        fi

        if [[ $primaries -lt $expected_per_host ]]; then
            under_primary_host="$host"
            log "Identified host with deficit primaries: $host ($primaries primaries, expected $expected_per_host)"
        fi
    done

    local operations_performed=0

    # Step 1: Fix backup deficit by relocating from over-backup host to under-capacity host
    if [[ -n "$under_capacity_host" && -n "$over_backup_host" ]]; then
        echo ""
        log "Step 1: Relocating backup from $over_backup_host to $under_capacity_host"

        local relocate_info
        if relocate_info=$(find_relocatable_backup "$over_backup_host" "$under_capacity_host"); then
            local partition instance_id primary_host
            partition=$(echo "$relocate_info" | cut -d'|' -f1)
            instance_id=$(echo "$relocate_info" | cut -d'|' -f2)
            primary_host=$(echo "$relocate_info" | cut -d'|' -f3)

            log "Selected partition $partition for relocation"
            log "  Instance: $instance_id"
            log "  From: $over_backup_host"
            log "  To: $under_capacity_host"
            log "  Primary location: $primary_host (safe - not on target)"

            if [[ "$DRY_RUN" == "false" ]]; then
                local target_container
                if target_container=$(get_container_on_host "$under_capacity_host"); then
                    log "Target container: $target_container"
                    log "Executing relocation..."

                    local response
                    response=$(rest_relocate_instance "$SERVICE_NAME" "$instance_id" "$target_container")

                    if [[ -n "$response" ]]; then
                        debug "Relocation response: $response"
                    fi

                    log "Waiting 10 seconds for relocation to complete..."
                    sleep 10

                    # Verify relocation succeeded with retry logic:
                    # - Up to 2 attempts (60s each) with 30s wait between attempts
                    # - Total max time: 10s initial + 60s + 30s + 60s = 160s
                    if verify_instance_on_host "$instance_id" "$under_capacity_host"; then
                        log_success "Relocation verified: $instance_id is now on $under_capacity_host"
                        operations_performed=$((operations_performed + 1))

                        # Update state tracking
                        host_totals[$under_capacity_host]=$((${host_totals[$under_capacity_host]} + 1))
                        host_backups[$under_capacity_host]=$((${host_backups[$under_capacity_host]} + 1))
                        host_totals[$over_backup_host]=$((${host_totals[$over_backup_host]} - 1))
                        host_backups[$over_backup_host]=$((${host_backups[$over_backup_host]} - 1))
                    else
                        log_error "Relocation verification failed"
                        return 1
                    fi
                else
                    log_error "Could not find container on $under_capacity_host"
                    return 1
                fi
            else
                log_warn "[DRY RUN] Would relocate $instance_id to $under_capacity_host"
            fi
        else
            log_warn "No suitable backup found for relocation - may need manual intervention"
        fi
    fi

    # Step 2: Fix primary imbalance via demote (causes automatic failover)
    if [[ -n "$over_primary_host" && -n "$under_primary_host" ]]; then
        echo ""
        log "Step 2: Demoting primary on $over_primary_host to rebalance with $under_primary_host"

        local demote_info
        if demote_info=$(find_demote_candidate "$over_primary_host" "$under_primary_host"); then
            local partition_idx instance_id backup_host
            # partition_idx is 0-based (from REST API partitionId)
            partition_idx=$(echo "$demote_info" | cut -d'|' -f1)
            instance_id=$(echo "$demote_info" | cut -d'|' -f2)
            backup_host=$(echo "$demote_info" | cut -d'|' -f3)

            # Convert to 1-based for display and instance ID construction
            local partition_display=$((partition_idx + 1))
            # Extract the actual suffix (_1 or _2) from the service instance ID
            # instance_id is like "dih-tau-service~3_2", we need the "2" part
            local actual_suffix="${instance_id##*_}"
            # Space instance IDs use 1-based partition in the name with actual suffix
            local space_instance_id="${SPACE_NAME}~${partition_display}_${actual_suffix}"

            log "Selected partition $partition_display for demote"
            log "  Space instance: $space_instance_id"
            log "  Current primary on: $over_primary_host"
            log "  Backup on: $backup_host (will become primary after demote)"

            if [[ "$DRY_RUN" == "false" ]]; then
                log "Executing demote (will cause automatic failover)..."

                local response
                response=$(rest_demote_primary "$SPACE_NAME" "$space_instance_id" "15s")

                if [[ -n "$response" ]]; then
                    debug "Demote response: $response"
                fi

                log "Waiting for failover to complete..."
                sleep 15

                # Verify demote succeeded by checking if backup is now primary
                # Retry logic: Up to 2 attempts (60s each) with 30s wait between attempts
                # Total max time: 15s initial + 60s + 30s + 60s = 165s
                # verify_demote_completed expects 0-based partition_idx (for REST API query)
                if verify_demote_completed "$partition_idx" "$backup_host"; then
                    log_success "Demote verified: Partition $partition_display primary is now on $backup_host"
                    operations_performed=$((operations_performed + 1))
                else
                    log_error "Demote verification failed"
                    return 1
                fi
            else
                log_warn "[DRY RUN] Would demote $space_instance_id"
            fi
        else
            log_warn "No suitable demote candidate found - cluster may already be balanced"
        fi
    fi

    echo ""
    if [[ "$DRY_RUN" == "false" ]]; then
        if [[ $operations_performed -gt 0 ]]; then
            log_success "Intelligent rebalancing completed: $operations_performed operations performed"
        else
            log_warn "No rebalancing operations were needed or could be performed"
        fi
    else
        log_warn "[DRY RUN] No actual changes made - run with --execute to apply changes"
    fi

    # Return number of operations performed (for reporting)
    return $operations_performed
}

execute_plan() {
    print_section "Phase 5: Executing Migration Plan"

    if [[ ! -s "$PLAN_FILE" ]]; then
        log_success "No steps to execute"
        return 0
    fi

    local total_steps
    total_steps=$(wc -l < "$PLAN_FILE" | tr -d ' ')
    local current_step=0

    log "Executing $total_steps migration steps..."
    echo ""

    while IFS='|' read -r step_id operation instance from_host to_host partition reason; do
        ((current_step++)) || true

        log "Step $current_step/$total_steps: $operation - $reason"

        case "$operation" in
            DEPLOY_MISSING)
                log_warn "Manual action required: Deploy backup $instance to $from_host"
                log_warn "Command: $GS_CLI pu deploy-instance $instance --host=$from_host"
                ;;

            RELOCATE_BACKUP)
                log "Relocating $instance from $from_host to $to_host"

                # Get container on target host
                # Note: In real implementation, need to query available containers
                log_warn "Manual relocation required for $instance"
                log_warn "Command: $GS_CLI pu relocate $instance --target-host=$to_host"

                # Verification would happen here
                # verify_instance_on_host "$instance" "$to_host" || abort "Relocation verification failed"
                ;;

            DEMOTE_PRIMARY)
                log "Demoting primary $instance on $from_host"
                log_warn "Manual demote required for $instance"
                log_warn "This will cause automatic failover to the backup instance"
                ;;
        esac

        if [[ "$DRY_RUN" == "false" ]]; then
            log "Waiting $STEP_DELAY seconds before next step..."
            sleep "$STEP_DELAY"
        fi

        echo ""
    done < "$PLAN_FILE"

    log_success "Plan execution completed"
}

################################################################################
# Main Report
################################################################################

generate_report() {
    local operations_count="${1:-0}"

    print_header "GigaSpaces Partition Rebalancer - Final Report"

    local space_servers
    local total_partitions
    local total_instances

    space_servers=($(get_space_servers))
    total_partitions=$(cut -d',' -f1 "$STATE_FILE" | sort -u | wc -l | tr -d ' ')
    total_instances=$(wc -l < "$STATE_FILE" | tr -d ' ')

    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Service: $SERVICE_NAME"
    echo "Partitions: $total_partitions ($total_instances total instances)"
    echo "Hosts: ${#space_servers[@]}"
    echo ""

    print_section "Current State"
    local host
    for host in "${space_servers[@]}"; do
        local total
        local primaries
        local backups

        total=$(get_instance_count_on_host "$host")
        primaries=$(get_primary_count_on_host "$host")
        backups=$(get_backup_count_on_host "$host")

        printf "  %-15s: %2d instances (%2d primaries, %2d backups)\n" "$host" "$total" "$primaries" "$backups"
    done

    echo ""
    if [[ -s "$PLAN_FILE" ]]; then
        local total_steps
        total_steps=$(wc -l < "$PLAN_FILE" | tr -d ' ')
        echo "Migration Plan: $total_steps steps generated"
    else
        echo "Migration Plan: No steps needed - cluster is balanced"
    fi

    echo ""
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "Execution Status: DRY RUN - No changes made"
        echo ""
        echo "To execute the plan, run with: --execute"
    else
        if [[ $operations_count -gt 0 ]]; then
            echo "Execution Status: COMPLETED ($operations_count operations performed)"
        else
            echo "Execution Status: NO OPERATIONS PERFORMED"
        fi
    fi

    print_header ""
}

################################################################################
# Argument Parsing
################################################################################

usage() {
    cat << EOF
GigaSpaces Partition Rebalancer

Usage: $0 [OPTIONS]

Options:
  -s, --service <name>    Service name (default: from config)
  -d, --dry-run           Dry run mode - don't execute (default)
  -e, --execute           Execute the migration plan
  -y, --yes               Auto-confirm execution (skip prompt)
  -v, --verbose           Enable verbose debug output
  --create-blocked        Create a colocation-blocked scenario (FOR TESTING ONLY)
  -h, --help              Show this help message

Examples:
  $0                      # Analyze only (dry-run)
  $0 --execute            # Analyze and execute (prompts for confirmation)
  $0 --execute --yes      # Analyze and execute (auto-confirm, no prompt)
  $0 -e -y -v             # Execute with auto-confirm and verbose output
  $0 --create-blocked -v  # Create blocked scenario for testing resolution logic

EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--service)
                SERVICE_NAME="$2"
                shift 2
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -e|--execute)
                DRY_RUN=false
                shift
                ;;
            -y|--yes)
                AUTO_CONFIRM=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            --create-blocked)
                CREATE_BLOCKED=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

################################################################################
# Main Entry Point
################################################################################

main() {
    print_header "GigaSpaces Partition Rebalancer"

    echo "Service: $SERVICE_NAME"
    if [[ "$CREATE_BLOCKED" == "true" ]]; then
        echo "Mode: CREATE BLOCKED SCENARIO (TESTING)"
    else
        echo "Mode: $([ "$DRY_RUN" == "true" ] && echo "DRY RUN" || echo "EXECUTE")"
    fi
    echo ""

    # Verify environment
    log "Verifying environment..."
    verify_running_on_pivot

    local pivot_ip
    local space_servers

    pivot_ip=$(get_pivot_ip)
    space_servers=($(get_space_servers))

    log "Pivot IP: $pivot_ip"
    log "Space servers: ${space_servers[*]}"

    # Initialize manager connection with automatic failover
    init_manager_connection

    # If creating blocked scenario, do that and exit
    if [[ "$CREATE_BLOCKED" == "true" ]]; then
        create_colocation_blocked_scenario
        exit $?
    fi

    # Execute phases
    discover_cluster_state

    if detect_problems; then
        # No problems detected
        generate_report
        exit 0
    fi

    calculate_target_state
    generate_migration_plan

    if display_plan; then
        # No plan needed
        generate_report
        exit 0
    fi

    # Plan exists - now use intelligent rebalancing
    if [[ "$DRY_RUN" == "false" ]] && [[ "$AUTO_CONFIRM" == "false" ]]; then
        echo ""
        read -r -p "Execute intelligent rebalancing? (y/N): " confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            log "Execution cancelled by user"
            exit 0
        fi
    fi

    # Always call optimal rebalancing (respects DRY_RUN flag)
    local operations_performed=0
    execute_optimal_rebalance
    operations_performed=$?

    # Regenerate report after execution
    echo ""
    log "Re-discovering cluster state after rebalancing..."
    discover_cluster_state
    detect_problems || true  # Show final state even if balanced

    generate_report "$operations_performed"
}

# Parse arguments and run
parse_args "$@"
main
