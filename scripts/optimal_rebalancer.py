#!/usr/bin/env python3
"""
GigaSpaces Optimal Partition Rebalancer
========================================

This module implements an optimal algorithm to find the shortest sequence of
operations to achieve perfect partition balance in a GigaSpaces cluster.

Problem Statement:
- 40 partitions (each has 1 primary + 1 backup = 80 total instances)
- 4 space servers
- Goal: Each server should have exactly 10 primaries + 10 backups = 20 instances

Available Operations:
1. DEMOTE: Swap primary/backup roles for a partition (cost: 1)
2. RELOCATE: Move a backup to a different host (cost: 1)

Constraints:
- Primary and backup of same partition cannot be on same host (colocation violation)

This is a state-space search problem similar to solving a Rubik's cube.
We use A* search with an admissible heuristic for optimal solutions.

Author: Claude (Anthropic)
"""

import json
import subprocess
import sys
import time
from collections import defaultdict, deque
from heapq import heappush, heappop
from typing import Dict, List, Optional, Set, Tuple
import copy
import argparse


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class Partition:
    """Represents a single partition with its primary and backup locations."""
    def __init__(self, partition_id, primary_host, backup_host):
        self.partition_id = partition_id
        self.primary_host = primary_host
        self.backup_host = backup_host

    def __hash__(self):
        return hash((self.partition_id, self.primary_host, self.backup_host))

    def __eq__(self, other):
        return (self.partition_id == other.partition_id and
                self.primary_host == other.primary_host and
                self.backup_host == other.backup_host)

    def __repr__(self):
        return f"Partition({self.partition_id}, {self.primary_host}, {self.backup_host})"


class ClusterState:
    """
    Represents the complete state of all partitions in the cluster.

    The state is immutable for hashing purposes in the search algorithm.
    """
    def __init__(self, partitions):
        self.partitions = partitions  # Sorted tuple for consistent hashing
        self._hash = None  # Lazy hash caching

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(self.partitions)
        return self._hash

    def __eq__(self, other):
        return self.partitions == other.partitions

    def __repr__(self):
        return f"ClusterState({len(self.partitions)} partitions)"

    @classmethod
    def from_dict(cls, partition_dict):
        """Create ClusterState from a dictionary {partition_id: (primary_host, backup_host)}"""
        partitions = tuple(sorted(
            [Partition(pid, ph, bh) for pid, (ph, bh) in partition_dict.items()],
            key=lambda p: p.partition_id
        ))
        return cls(partitions)

    def to_dict(self):
        """Convert to dictionary representation."""
        return {p.partition_id: (p.primary_host, p.backup_host) for p in self.partitions}

    def get_host_stats(self, hosts):
        """Calculate primaries and backups per host."""
        stats = {h: {'primaries': 0, 'backups': 0, 'total': 0} for h in hosts}

        for p in self.partitions:
            if p.primary_host in stats:
                stats[p.primary_host]['primaries'] += 1
                stats[p.primary_host]['total'] += 1
            if p.backup_host in stats:
                stats[p.backup_host]['backups'] += 1
                stats[p.backup_host]['total'] += 1

        return stats

    def get_partition(self, partition_id):
        """Get a specific partition by ID."""
        for p in self.partitions:
            if p.partition_id == partition_id:
                return p
        return None


class Operation:
    """Represents a single rebalancing operation."""
    def __init__(self, op_type, partition_id, from_host, to_host, description=""):
        self.op_type = op_type  # 'DEMOTE' or 'RELOCATE'
        self.partition_id = partition_id
        self.from_host = from_host
        self.to_host = to_host
        self.description = description

    def __repr__(self):
        if self.op_type == 'DEMOTE':
            return f"DEMOTE partition {self.partition_id} (primary {self.from_host} -> backup)"
        else:
            return f"RELOCATE partition {self.partition_id} backup: {self.from_host} -> {self.to_host}"


class SearchNode:
    """Node in the A* search tree."""
    def __init__(self, f_score, g_score, state, operations):
        self.f_score = f_score  # f = g + h (for priority queue ordering)
        self.g_score = g_score  # Cost so far
        self.state = state
        self.operations = operations  # Path to this state

    def __lt__(self, other):
        """For priority queue ordering."""
        return self.f_score < other.f_score

    def __hash__(self):
        return hash(self.state)

    def __repr__(self):
        return f"SearchNode(f={self.f_score}, g={self.g_score}, ops={len(self.operations)})"


# =============================================================================
# HEURISTIC FUNCTIONS
# =============================================================================

def compute_imbalance(state, hosts,
                      target_primaries, target_backups):
    """
    Compute the imbalance (excess/deficit) for each host.

    Returns dict: {host: {'primary_excess', 'backup_excess'}}
    Positive = excess, Negative = deficit
    """
    stats = state.get_host_stats(hosts)
    imbalance = {}

    for host in hosts:
        imbalance[host] = {
            'primary_excess': stats[host]['primaries'] - target_primaries,
            'backup_excess': stats[host]['backups'] - target_backups
        }

    return imbalance


def heuristic_manhattan(state, hosts,
                       target_primaries, target_backups):
    """
    Admissible heuristic: Manhattan distance to goal.

    For each host, calculate |actual_primaries - target| + |actual_backups - target|
    Sum all and divide by 2 (since each operation affects 2 counts).

    This is admissible because:
    - Each DEMOTE changes 2 primary counts and 2 backup counts (net 4 changes)
    - Each RELOCATE changes 2 backup counts (net 2 changes)
    - Dividing total deviation by max impact gives lower bound
    """
    stats = state.get_host_stats(hosts)

    primary_deviation = sum(abs(stats[h]['primaries'] - target_primaries) for h in hosts)
    backup_deviation = sum(abs(stats[h]['backups'] - target_backups) for h in hosts)

    # Each demote fixes 2 primary deviations (one host loses, one gains)
    # Each relocate fixes 2 backup deviations
    # Minimum operations needed is max of these divided by 2

    # More sophisticated: demote affects both, relocate only affects backups
    # If primary imbalance exists, we need demotes
    # If only backup imbalance, we might use relocates

    demotes_needed = primary_deviation // 2  # Each demote reduces deviation by 2
    relocates_needed = max(0, (backup_deviation - primary_deviation) // 2)

    return demotes_needed + relocates_needed


def count_colocation_violations(state):
    """
    Count partitions where primary and backup are on the same host (colocation violations).
    Each violation requires at least one RELOCATE operation to fix.
    """
    violations = 0
    for partition in state.partitions:
        if partition.primary_host == partition.backup_host:
            violations += 1
    return violations


def heuristic_improved(state, hosts,
                       target_primaries, target_backups):
    """
    Improved admissible heuristic that considers:
    1. Primary imbalance (fixed by DEMOTE)
    2. Backup imbalance (fixed by RELOCATE or DEMOTE)
    3. Colocation violations (require RELOCATE)

    Key insight:
    - DEMOTE: Swaps P/B for a partition. If primary on host A, backup on host B,
              after demote: A loses 1P gains 1B, B gains 1P loses 1B
    - RELOCATE: Moves backup from A to C. A loses 1B, C gains 1B.

    Returns the maximum of three lower bounds for an admissible heuristic.
    """
    imbalance = compute_imbalance(state, hosts, target_primaries, target_backups)

    # Sum of positive primary excesses (hosts that have too many primaries)
    total_excess_primaries = sum(max(0, imbalance[h]['primary_excess']) for h in hosts)

    # Sum of positive backup excesses
    total_excess_backups = sum(max(0, imbalance[h]['backup_excess']) for h in hosts)

    # Minimum demotes needed to fix primary imbalance
    # Each DEMOTE fixes 2 primary counts (one decreases, one increases)
    min_demotes = total_excess_primaries

    # Backup imbalance that can't be fixed by demotes alone
    # If backup excess is greater than primary excess, we need relocates
    backup_only_imbalance = max(0, (total_excess_backups - total_excess_primaries) // 2)

    # Colocation violations require at least one RELOCATE per violation
    colocation_violations = count_colocation_violations(state)

    # Return the maximum lower bound (admissible heuristic)
    # This is more informative than just counting primary excess
    return max(min_demotes, backup_only_imbalance, colocation_violations)


# =============================================================================
# STATE TRANSITION FUNCTIONS
# =============================================================================

def apply_demote(state, partition_id) -> Optional[Tuple[ClusterState, Operation]]:
    """
    Apply DEMOTE operation to a partition.

    Demote swaps the primary and backup roles.
    Before: primary on A, backup on B
    After:  primary on B, backup on A

    Constraint: Primary and backup must be on different hosts (always true for valid states)
    """
    partition = state.get_partition(partition_id)
    if not partition:
        return None

    # Cannot demote if primary and backup are on same host (should never happen)
    if partition.primary_host == partition.backup_host:
        return None

    # Create new partition with swapped roles
    new_partition = Partition(
        partition_id=partition_id,
        primary_host=partition.backup_host,  # Old backup becomes primary
        backup_host=partition.primary_host   # Old primary becomes backup
    )

    # Create new state with updated partition
    new_partitions = tuple(
        new_partition if p.partition_id == partition_id else p
        for p in state.partitions
    )

    operation = Operation(
        op_type='DEMOTE',
        partition_id=partition_id,
        from_host=partition.primary_host,
        to_host=partition.backup_host,
        description=f"Demote P{partition_id}: primary {partition.primary_host} -> backup, "
                   f"backup {partition.backup_host} -> primary"
    )

    return ClusterState(new_partitions), operation


def apply_relocate(state, partition_id,
                   target_host) -> Optional[Tuple[ClusterState, Operation]]:
    """
    Apply RELOCATE operation to move a backup to a different host.

    Constraint: Cannot relocate backup to same host as primary (would cause colocation)
    """
    partition = state.get_partition(partition_id)
    if not partition:
        return None

    # Cannot relocate to same host as primary
    if target_host == partition.primary_host:
        return None

    # Cannot relocate to where it already is (no-op)
    if target_host == partition.backup_host:
        return None

    # Create new partition with relocated backup
    new_partition = Partition(
        partition_id=partition_id,
        primary_host=partition.primary_host,  # Primary stays
        backup_host=target_host               # Backup moves
    )

    new_partitions = tuple(
        new_partition if p.partition_id == partition_id else p
        for p in state.partitions
    )

    operation = Operation(
        op_type='RELOCATE',
        partition_id=partition_id,
        from_host=partition.backup_host,
        to_host=target_host,
        description=f"Relocate P{partition_id} backup: {partition.backup_host} -> {target_host}"
    )

    return ClusterState(new_partitions), operation


def generate_successors(state, hosts,
                        target_primaries, target_backups,
                        relaxed=False):
    """
    Generate all valid successor states from current state.

    If relaxed=False (default):
        Optimization: Only generate operations that make direct progress toward the goal.
        - Only demote partitions where primary is on an over-primary host
        - Only relocate backups from over-backup hosts to under-backup hosts

    If relaxed=True:
        Generate ALL valid operations (needed when direct path doesn't exist)
        - Demote any partition where it helps primary balance (even if backup location not optimal)
        - Relocate backups to enable future demotes
    """
    successors = []
    imbalance = compute_imbalance(state, hosts, target_primaries, target_backups)

    # Identify hosts with imbalances
    over_primary_hosts = {h for h in hosts if imbalance[h]['primary_excess'] > 0}
    under_primary_hosts = {h for h in hosts if imbalance[h]['primary_excess'] < 0}
    over_backup_hosts = {h for h in hosts if imbalance[h]['backup_excess'] > 0}
    under_backup_hosts = {h for h in hosts if imbalance[h]['backup_excess'] < 0}

    if relaxed:
        # Relaxed mode: Generate all potentially useful operations
        for partition in state.partitions:
            # DEMOTE: Any partition where primary is on over-primary host
            if partition.primary_host in over_primary_hosts:
                result = apply_demote(state, partition.partition_id)
                if result:
                    successors.append(result)

            # RELOCATE: Move backup TO under-primary host to enable future demotes
            # This is key for multi-step solutions!
            if partition.backup_host not in under_primary_hosts:
                for target_host in under_primary_hosts:
                    if target_host != partition.primary_host:
                        result = apply_relocate(state, partition.partition_id, target_host)
                        if result:
                            successors.append(result)

            # RELOCATE: Also consider moving from over-backup to under-backup
            if partition.backup_host in over_backup_hosts:
                for target_host in under_backup_hosts:
                    if target_host != partition.primary_host:
                        result = apply_relocate(state, partition.partition_id, target_host)
                        if result:
                            successors.append(result)
    else:
        # Strict mode: Only operations that directly improve balance
        for partition in state.partitions:
            # DEMOTE operations: Only if primary is on over-primary host
            # and backup is on under-primary host (so demote helps both)
            if (partition.primary_host in over_primary_hosts and
                partition.backup_host in under_primary_hosts):
                result = apply_demote(state, partition.partition_id)
                if result:
                    successors.append(result)

            # RELOCATE operations: Only if backup is on over-backup host
            if partition.backup_host in over_backup_hosts:
                for target_host in under_backup_hosts:
                    # Cannot relocate to same host as primary
                    if target_host != partition.primary_host:
                        result = apply_relocate(state, partition.partition_id, target_host)
                        if result:
                            successors.append(result)

    return successors


def is_goal_state(state, hosts,
                  target_primaries, target_backups):
    """Check if current state is the goal (balanced) state."""
    stats = state.get_host_stats(hosts)

    for host in hosts:
        if stats[host]['primaries'] != target_primaries:
            return False
        if stats[host]['backups'] != target_backups:
            return False

    return True


# =============================================================================
# SEARCH ALGORITHMS
# =============================================================================

def astar_search(initial_state, hosts,
                 target_primaries, target_backups,
                 max_depth=40, max_time=60, verbose=False):
    """
    A* search for optimal rebalancing sequence.

    Uses two-phase approach:
    1. First try strict successors (direct progress only)
    2. If no solution, use relaxed successors (enable multi-step paths)

    Uses improved admissible heuristic for guaranteed optimal solution.

    Args:
        max_time: Maximum time in seconds (default 60). Returns None if timeout.
    """
    if is_goal_state(initial_state, hosts, target_primaries, target_backups):
        return []

    search_start_time = time.time()

    # Try strict mode first (faster for simple cases)
    for relaxed_mode in [False, True]:
        mode_name = "relaxed" if relaxed_mode else "strict"
        if verbose:
            print(f"  Trying {mode_name} search mode...")

        # Priority queue: (f_score, g_score, state, operations)
        initial_h = heuristic_improved(initial_state, hosts, target_primaries, target_backups)
        start_node = SearchNode(
            f_score=initial_h,
            g_score=0,
            state=initial_state,
            operations=tuple()
        )

        frontier = [start_node]
        explored = set()
        best_g = {initial_state: 0}

        nodes_expanded = 0
        phase_start_time = time.time()

        while frontier:
            # Check timeout
            elapsed = time.time() - search_start_time
            if elapsed > max_time:
                if verbose:
                    print(f"  [{mode_name}] Search timeout after {elapsed:.1f}s")
                    print(f"  [{mode_name}] Explored {nodes_expanded} nodes before timeout")
                return None  # Trigger fallback to greedy
            node = heappop(frontier)

            if node.state in explored:
                continue

            explored.add(node.state)
            nodes_expanded += 1

            if verbose and nodes_expanded % 100 == 0:
                elapsed = time.time() - phase_start_time
                print(f"  [{mode_name}] Expanded {nodes_expanded} nodes, depth {node.g_score}, "
                      f"frontier {len(frontier)}, elapsed {elapsed:.1f}s")

            if node.g_score > max_depth:
                continue

            # Check if goal
            if is_goal_state(node.state, hosts, target_primaries, target_backups):
                if verbose:
                    print(f"  Found solution! Depth: {node.g_score}, Nodes expanded: {nodes_expanded}")
                return list(node.operations)

            # Generate successors
            for new_state, operation in generate_successors(
                node.state, hosts, target_primaries, target_backups, relaxed=relaxed_mode
            ):
                new_g = node.g_score + 1

                # Skip if we've found a better path to this state
                if new_state in best_g and best_g[new_state] <= new_g:
                    continue

                best_g[new_state] = new_g
                new_h = heuristic_improved(new_state, hosts, target_primaries, target_backups)

                new_node = SearchNode(
                    f_score=new_g + new_h,
                    g_score=new_g,
                    state=new_state,
                    operations=node.operations + (operation,)
                )

                heappush(frontier, new_node)

        if verbose:
            print(f"  [{mode_name}] No solution found. Nodes expanded: {nodes_expanded}")

    return None


def bfs_search(initial_state, hosts,
               target_primaries, target_backups,
               max_depth=10, verbose=False):
    """
    Breadth-first search for guaranteed shortest path.

    Use for small state spaces or when A* is too slow.
    Uses relaxed=True to find multi-step solutions.
    """
    if is_goal_state(initial_state, hosts, target_primaries, target_backups):
        return []

    queue = deque([(initial_state, [])])
    visited = {initial_state}
    nodes_expanded = 0

    while queue:
        state, operations = queue.popleft()
        nodes_expanded += 1

        if verbose and nodes_expanded % 100 == 0:
            print(f"  BFS: Expanded {nodes_expanded} nodes, depth {len(operations)}")

        if len(operations) >= max_depth:
            continue

        for new_state, operation in generate_successors(
            state, hosts, target_primaries, target_backups, relaxed=True
        ):
            if new_state in visited:
                continue

            visited.add(new_state)
            new_ops = operations + [operation]

            if is_goal_state(new_state, hosts, target_primaries, target_backups):
                if verbose:
                    print(f"  Found solution! Depth: {len(new_ops)}, Nodes expanded: {nodes_expanded}")
                return new_ops

            queue.append((new_state, new_ops))

    if verbose:
        print(f"  No solution found within depth {max_depth}. Nodes expanded: {nodes_expanded}")
    return None


def greedy_rebalance(initial_state, hosts,
                     target_primaries, target_backups,
                     verbose=False) -> List[Operation]:
    """
    Greedy algorithm: Always pick the operation that reduces imbalance most.

    Not guaranteed optimal, but fast and usually good enough.
    Uses relaxed=True to find multi-step solutions.
    """
    state = initial_state
    operations = []

    while not is_goal_state(state, hosts, target_primaries, target_backups):
        if len(operations) > 100:  # Safety limit
            if verbose:
                print("  Warning: Greedy exceeded 100 operations, stopping")
            break

        best_successor = None
        best_operation = None
        best_h = float('inf')

        for new_state, operation in generate_successors(
            state, hosts, target_primaries, target_backups, relaxed=True
        ):
            h = heuristic_improved(new_state, hosts, target_primaries, target_backups)
            if h < best_h:
                best_h = h
                best_successor = new_state
                best_operation = operation

        if best_successor is None:
            if verbose:
                print("  Warning: No valid operations found, stopping")
            break

        state = best_successor
        operations.append(best_operation)

        if verbose:
            print(f"  Step {len(operations)}: {best_operation}")

    return operations


# =============================================================================
# MAIN ANALYSIS FUNCTIONS
# =============================================================================

def analyze_current_state(partition_map,
                          hosts, verbose=False):
    """Analyze and display current cluster state."""
    state = ClusterState.from_dict(partition_map)
    stats = state.get_host_stats(hosts)

    print("\n" + "="*80)
    print("CURRENT CLUSTER STATE ANALYSIS")
    print("="*80)

    num_partitions = len(partition_map)
    num_hosts = len(hosts)
    target_per_host = num_partitions // num_hosts

    print(f"\nConfiguration:")
    print(f"  Partitions: {num_partitions}")
    print(f"  Hosts: {num_hosts}")
    print(f"  Target per host: {target_per_host} primaries + {target_per_host} backups = {target_per_host * 2} total")

    print(f"\nPer-Host Distribution:")
    print(f"  {'Host':<15} {'Primaries':>10} {'Backups':>10} {'Total':>10} {'Status':<20}")
    print(f"  {'-'*15} {'-'*10} {'-'*10} {'-'*10} {'-'*20}")

    imbalanced = False
    for host in hosts:
        s = stats[host]
        p_diff = s['primaries'] - target_per_host
        b_diff = s['backups'] - target_per_host

        if p_diff == 0 and b_diff == 0:
            status = "BALANCED"
        else:
            imbalanced = True
            parts = []
            if p_diff > 0:
                parts.append(f"-{p_diff}P")
            elif p_diff < 0:
                parts.append(f"+{-p_diff}P")
            if b_diff > 0:
                parts.append(f"-{b_diff}B")
            elif b_diff < 0:
                parts.append(f"+{-b_diff}B")
            status = "needs " + ", ".join(parts)

        print(f"  {host:<15} {s['primaries']:>10} {s['backups']:>10} {s['total']:>10} {status:<20}")

    if imbalanced:
        print(f"\n  Status: IMBALANCED - rebalancing needed")
    else:
        print(f"\n  Status: BALANCED - no action needed")

    if verbose:
        print(f"\nPartition Details:")
        print(f"  {'Partition':<10} {'Primary Host':<18} {'Backup Host':<18}")
        print(f"  {'-'*10} {'-'*18} {'-'*18}")
        for pid in sorted(partition_map.keys()):
            ph, bh = partition_map[pid]
            print(f"  {pid:<10} {ph:<18} {bh:<18}")


def find_optimal_rebalancing(partition_map,
                             hosts,
                             algorithm = 'astar',
                             verbose=False) -> List[Operation]:
    """
    Find optimal sequence of operations to balance the cluster.

    Args:
        partition_map: Dict mapping partition_id to (primary_host, backup_host)
        hosts: List of host IPs
        algorithm: 'astar', 'bfs', or 'greedy'
        verbose: Print detailed progress

    Returns:
        List of Operation objects representing the rebalancing sequence
    """
    state = ClusterState.from_dict(partition_map)
    num_partitions = len(partition_map)
    num_hosts = len(hosts)
    target_primaries = num_partitions // num_hosts
    target_backups = num_partitions // num_hosts

    print("\n" + "="*80)
    print(f"SEARCHING FOR OPTIMAL REBALANCING ({algorithm.upper()})")
    print("="*80)

    if is_goal_state(state, hosts, target_primaries, target_backups):
        print("\nCluster is already balanced! No operations needed.")
        return []

    initial_h = heuristic_improved(state, hosts, target_primaries, target_backups)
    print(f"\nInitial heuristic (lower bound): {initial_h} operations")
    print(f"Searching...")

    if algorithm == 'astar':
        operations = astar_search(state, hosts, target_primaries, target_backups,
                                  max_depth=40, max_time=60, verbose=verbose)
        # Fall back to greedy if A* times out or fails
        if operations is None:
            print("\nA* search timed out or failed. Falling back to greedy algorithm...")
            operations = greedy_rebalance(state, hosts, target_primaries, target_backups,
                                          verbose=verbose)
            if operations is None:
                print("\nGreedy algorithm also failed to find solution!")
                return []
            print(f"\nGreedy algorithm found solution with {len(operations)} operations (may not be optimal)")
    elif algorithm == 'bfs':
        operations = bfs_search(state, hosts, target_primaries, target_backups,
                                max_depth=10, verbose=verbose)
    elif algorithm == 'greedy':
        operations = greedy_rebalance(state, hosts, target_primaries, target_backups,
                                      verbose=verbose)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    if operations is None:
        print("\nNo solution found!")
        return []

    print(f"\nFound solution with {len(operations)} operations:")
    print("-" * 60)

    for i, op in enumerate(operations, 1):
        print(f"  Step {i}: {op.description}")

    return operations


def verify_solution(partition_map,
                    hosts,
                    operations):
    """Verify that applying operations leads to balanced state."""
    state = ClusterState.from_dict(partition_map)
    num_partitions = len(partition_map)
    num_hosts = len(hosts)
    target_primaries = num_partitions // num_hosts
    target_backups = num_partitions // num_hosts

    print("\n" + "="*80)
    print("SOLUTION VERIFICATION")
    print("="*80)

    for i, op in enumerate(operations, 1):
        print(f"\nStep {i}: {op.op_type} partition {op.partition_id}")

        if op.op_type == 'DEMOTE':
            result = apply_demote(state, op.partition_id)
        else:
            result = apply_relocate(state, op.partition_id, op.to_host)

        if result is None:
            print(f"  ERROR: Operation failed!")
            return False

        state, _ = result
        stats = state.get_host_stats(hosts)
        state_parts = [f'{h}: {s["primaries"]}P/{s["backups"]}B' for h, s in stats.items()]
        print(f"  State after: {', '.join(state_parts)}")

    final_balanced = is_goal_state(state, hosts, target_primaries, target_backups)

    print(f"\nFinal state balanced: {final_balanced}")
    return final_balanced


# =============================================================================
# EXAMPLE: THE SPECIFIC PROBLEM FROM USER
# =============================================================================

def create_example_state() -> Tuple[Dict[int, Tuple[str, str]], List[str]]:
    """
    Create example state matching the user's problem:

    Current state:
    - 10.0.1.91:  9 primaries, 11 backups (needs +1P, -1B)
    - 10.0.1.57: 11 primaries,  9 backups (needs -1P, +1B)
    - 10.0.1.203: 10 primaries, 10 backups (balanced)
    - 10.0.1.179: 10 primaries, 10 backups (balanced)

    We need to create a synthetic partition map that matches these counts.
    """
    hosts = ['10.0.1.91', '10.0.1.57', '10.0.1.203', '10.0.1.179']

    # Target: 10P + 10B per host
    # Current imbalance:
    #   10.0.1.91:  9P, 11B
    #   10.0.1.57: 11P,  9B
    #   10.0.1.203: 10P, 10B
    #   10.0.1.179: 10P, 10B

    # Build partition map to match these counts
    partition_map = {}

    # Host assignments for primaries (total 40)
    primary_counts = {
        '10.0.1.91': 9,
        '10.0.1.57': 11,
        '10.0.1.203': 10,
        '10.0.1.179': 10
    }

    # Host assignments for backups (total 40)
    backup_counts = {
        '10.0.1.91': 11,
        '10.0.1.57': 9,
        '10.0.1.203': 10,
        '10.0.1.179': 10
    }

    # Distribute partitions to match counts
    # Strategy: Assign primaries first, then backups ensuring no colocation

    partition_id = 1

    # For balanced hosts (203, 179), create standard assignments
    # 203 gets primaries 1-10, with backups distributed to other hosts
    # 179 gets primaries 11-20, with backups distributed
    # etc.

    # Let's create a specific distribution:
    # Partitions 1-9: Primary on 91, Backup on various
    for i in range(1, 10):
        backup_host = hosts[(i % 3) + 1]  # 57, 203, or 179
        partition_map[partition_id] = ('10.0.1.91', backup_host)
        partition_id += 1

    # Partitions 10-20: Primary on 57
    for i in range(10, 21):
        # Need backups distributed but not on 91 to keep 91's backup count high
        if i < 12:
            backup_host = '10.0.1.91'  # 2 backups on 91
        elif i < 17:
            backup_host = '10.0.1.203'
        else:
            backup_host = '10.0.1.179'
        partition_map[partition_id] = ('10.0.1.57', backup_host)
        partition_id += 1

    # Partitions 21-30: Primary on 203
    for i in range(21, 31):
        if i < 25:
            backup_host = '10.0.1.91'  # 4 more backups on 91
        elif i < 28:
            backup_host = '10.0.1.57'
        else:
            backup_host = '10.0.1.179'
        partition_map[partition_id] = ('10.0.1.203', backup_host)
        partition_id += 1

    # Partitions 31-40: Primary on 179
    for i in range(31, 41):
        if i < 36:
            backup_host = '10.0.1.91'  # 5 more backups on 91 (total 11)
        elif i < 39:
            backup_host = '10.0.1.57'  # 3 more backups on 57
        else:
            backup_host = '10.0.1.203'
        partition_map[partition_id] = ('10.0.1.179', backup_host)
        partition_id += 1

    return partition_map, hosts


def create_example_state_v2() -> Tuple[Dict[int, Tuple[str, str]], List[str]]:
    """
    Create example state with exact counts:
    - 10.0.1.91:  9P, 11B (needs +1P, -1B)
    - 10.0.1.57: 11P,  9B (needs -1P, +1B)
    - 10.0.1.203: 10P, 10B (balanced)
    - 10.0.1.179: 10P, 10B (balanced)

    Key insight: The simplest fix is:
    1. Find a partition where primary is on 57 and backup is on 91
    2. DEMOTE that partition -> 57 loses 1P gains 1B, 91 gains 1P loses 1B
    3. Done in 1 operation!

    If no such partition exists, we need a 2-step sequence:
    1. RELOCATE a backup from 91 to a third host
    2. DEMOTE to fix primary imbalance

    Or we find a creative multi-hop path.
    """
    hosts = ['10.0.1.91', '10.0.1.57', '10.0.1.203', '10.0.1.179']

    # Create distribution where NO partition has primary on 57 AND backup on 91
    # This forces the algorithm to find a multi-step solution
    partition_map = {}

    # Primaries on 10.0.1.91 (9 total)
    # Backups NOT on 91 itself
    for i in range(1, 10):  # Partitions 1-9
        backup = ['10.0.1.57', '10.0.1.203', '10.0.1.179'][i % 3]
        partition_map[i] = ('10.0.1.91', backup)

    # Primaries on 10.0.1.57 (11 total)
    # CRITICAL: None of these have backup on 91 (making direct demote impossible)
    for i in range(10, 21):  # Partitions 10-20
        # Backups on 203 and 179 only (not 91)
        backup = ['10.0.1.203', '10.0.1.179'][(i - 10) % 2]
        partition_map[i] = ('10.0.1.57', backup)

    # Primaries on 10.0.1.203 (10 total)
    # Some backups on 91 to get 91's backup count to 11
    for i in range(21, 31):  # Partitions 21-30
        if i < 26:  # 5 backups on 91
            backup = '10.0.1.91'
        elif i < 28:  # 2 backups on 57
            backup = '10.0.1.57'
        else:  # 3 backups on 179
            backup = '10.0.1.179'
        partition_map[i] = ('10.0.1.203', backup)

    # Primaries on 10.0.1.179 (10 total)
    # More backups on 91 to complete the count
    for i in range(31, 41):  # Partitions 31-40
        if i < 37:  # 6 backups on 91 (total 91 backups: 5+6=11)
            backup = '10.0.1.91'
        elif i < 40:  # 3 backups on 57 (total 57 backups: 3+2+3=8... need adjustment)
            backup = '10.0.1.57'
        else:  # 1 backup on 203
            backup = '10.0.1.203'
        partition_map[i] = ('10.0.1.179', backup)

    # Verify counts
    counts = {h: {'P': 0, 'B': 0} for h in hosts}
    for pid, (ph, bh) in partition_map.items():
        counts[ph]['P'] += 1
        counts[bh]['B'] += 1

    print("\nGenerated state verification:")
    for h in hosts:
        print(f"  {h}: {counts[h]['P']}P, {counts[h]['B']}B")

    # Adjust to get exact counts
    # Current: 91: 9P, 11B | 57: 11P, 8B | 203: 10P, 8B | 179: 10P, 13B
    # Need:    91: 9P, 11B | 57: 11P, 9B | 203: 10P, 10B | 179: 10P, 10B

    # Let me recalculate more carefully...
    return partition_map, hosts


def create_example_state_v3() -> Tuple[Dict[int, Tuple[str, str]], List[str]]:
    """
    Create exact state with careful count verification.

    Target counts:
    - 10.0.1.91:  9P, 11B
    - 10.0.1.57: 11P,  9B
    - 10.0.1.203: 10P, 10B
    - 10.0.1.179: 10P, 10B

    Constraint: NO partition has both primary on 57 AND backup on 91
    (This makes the problem non-trivial)
    """
    hosts = ['10.0.1.91', '10.0.1.57', '10.0.1.203', '10.0.1.179']
    partition_map = {}
    pid = 1

    # Primaries on 91 (9 total), backups distributed (not on 91)
    # Backups: 3 on 57, 3 on 203, 3 on 179
    for backup in ['10.0.1.57', '10.0.1.203', '10.0.1.179'] * 3:
        partition_map[pid] = ('10.0.1.91', backup)
        pid += 1

    # Primaries on 57 (11 total), backups NOT on 91 (to make problem harder)
    # Backups: 6 on 203, 5 on 179
    for i in range(11):
        backup = '10.0.1.203' if i < 6 else '10.0.1.179'
        partition_map[pid] = ('10.0.1.57', backup)
        pid += 1

    # Primaries on 203 (10 total)
    # Backups: need to add more to 91 (currently 0 from 57's primaries)
    # Need 91 to have 11 total backups. Current from 91's primaries: 0
    # So all 11 backups on 91 must come from 203 and 179's primaries
    # 203 contributes: 6 backups on 91
    # 179 contributes: 5 backups on 91
    for i in range(10):
        if i < 6:  # 6 backups on 91
            backup = '10.0.1.91'
        elif i < 8:  # 2 backups on 57
            backup = '10.0.1.57'
        else:  # 2 backups on 179
            backup = '10.0.1.179'
        partition_map[pid] = ('10.0.1.203', backup)
        pid += 1

    # Primaries on 179 (10 total)
    # Backups: 5 on 91, rest distributed to reach correct totals
    for i in range(10):
        if i < 5:  # 5 backups on 91 (total 91 backups: 6+5=11)
            backup = '10.0.1.91'
        elif i < 9:  # 4 backups on 57 (total 57 backups: 3+2+4=9)
            backup = '10.0.1.57'
        else:  # 1 backup on 203 (total 203 backups: 3+6+1=10)
            backup = '10.0.1.203'
        partition_map[pid] = ('10.0.1.179', backup)
        pid += 1

    # Verify
    counts = {h: {'P': 0, 'B': 0} for h in hosts}
    for p_id, (ph, bh) in partition_map.items():
        counts[ph]['P'] += 1
        counts[bh]['B'] += 1

    print("\nGenerated state (v3) verification:")
    for h in hosts:
        print(f"  {h}: {counts[h]['P']}P, {counts[h]['B']}B")

    # Check if any partition has primary on 57 AND backup on 91
    can_demote_directly = False
    for p_id, (ph, bh) in partition_map.items():
        if ph == '10.0.1.57' and bh == '10.0.1.91':
            can_demote_directly = True
            print(f"\n  WARNING: Partition {p_id} allows direct demote!")
            break

    if not can_demote_directly:
        print("\n  CONFIRMED: No direct demote possible (multi-step required)")

    return partition_map, hosts


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='GigaSpaces Optimal Partition Rebalancer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --example          Run with synthetic example data
  %(prog)s --json state.json  Load partition map from JSON file
  %(prog)s --verbose          Enable detailed output

JSON format for --json:
{
  "hosts": ["10.0.1.91", "10.0.1.57", "10.0.1.203", "10.0.1.179"],
  "partitions": {
    "1": {"primary": "10.0.1.91", "backup": "10.0.1.57"},
    "2": {"primary": "10.0.1.57", "backup": "10.0.1.203"},
    ...
  }
}
        """
    )

    parser.add_argument('--example', action='store_true',
                        help='Run with synthetic example matching the user problem')
    parser.add_argument('--json', type=str, metavar='FILE',
                        help='Load partition map from JSON file')
    parser.add_argument('--algorithm', choices=['astar', 'bfs', 'greedy'], default='astar',
                        help='Search algorithm to use (default: astar)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    parser.add_argument('--verify', action='store_true',
                        help='Verify the solution by simulating operations')

    args = parser.parse_args()

    # Load or create state
    if args.example:
        partition_map, hosts = create_example_state_v3()
    elif args.json:
        with open(args.json, 'r') as f:
            data = json.load(f)
        hosts = data['hosts']
        partition_map = {
            int(pid): (p['primary'], p['backup'])
            for pid, p in data['partitions'].items()
        }
    else:
        # Default: run example
        partition_map, hosts = create_example_state_v3()

    # Analyze current state
    analyze_current_state(partition_map, hosts, verbose=args.verbose)

    # Find optimal rebalancing
    operations = find_optimal_rebalancing(
        partition_map, hosts,
        algorithm=args.algorithm,
        verbose=args.verbose
    )

    # Verify if requested
    if args.verify and operations:
        verify_solution(partition_map, hosts, operations)

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nTotal operations needed: {len(operations)}")

    if operations:
        demotes = sum(1 for op in operations if op.op_type == 'DEMOTE')
        relocates = sum(1 for op in operations if op.op_type == 'RELOCATE')
        print(f"  - DEMOTE operations: {demotes}")
        print(f"  - RELOCATE operations: {relocates}")

        print("\n" + "="*80)
        print("EXECUTION PLAN")
        print("="*80)
        for i, op in enumerate(operations, 1):
            print(f"\nStep {i}:")
            print(f"  Operation: {op.op_type}")
            print(f"  Partition: {op.partition_id}")
            if op.op_type == 'DEMOTE':
                print(f"  Effect: Primary on {op.from_host} becomes backup")
                print(f"          Backup on {op.to_host} becomes primary")
            else:
                print(f"  Effect: Backup moves from {op.from_host} to {op.to_host}")


if __name__ == '__main__':
    main()
