"""
Checkpoint utility for atomic migration operations.

Provides checkpointing functionality to enable resume capability
and atomic migrations in case of failures during execution.
"""
import os
import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

from src.models.service import MigrationRecord


@dataclass
class MigrationCheckpoint:
    """Represents a checkpoint for migration operations."""
    checkpoint_id: str
    timestamp: str
    stage: str  # discovery, migration, deletion, completed
    services_in_scope: List[str] = field(default_factory=list)
    duplicate_groups: Dict[str, List[str]] = field(default_factory=dict)
    winner_selections: Dict[str, str] = field(default_factory=dict)
    migrated_policies: Dict[str, Dict[str, str]] = field(default_factory=dict)
    migrated_groups: Dict[str, Dict[str, str]] = field(default_factory=dict)
    deletions_prepared: List[str] = field(default_factory=list)
    error_state: Optional[str] = None
    last_operation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MigrationCheckpoint":
        """Create checkpoint from dictionary."""
        return cls(**data)


class CheckpointManager:
    """Manages migration checkpoints for atomic operations."""

    def __init__(self, backup_dir: str = "./backups"):
        """
        Initialize checkpoint manager.

        Args:
            backup_dir: Directory to store checkpoint files
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._checkpoints: List[MigrationCheckpoint] = []
        self._current_checkpoint: Optional[MigrationCheckpoint] = None

    def create_checkpoint(
        self,
        stage: str,
        checkpoint_id: Optional[str] = None,
        **kwargs
    ) -> MigrationCheckpoint:
        """
        Create a new checkpoint.

        Args:
            stage: Current stage of migration (discovery, migration, deletion, completed)
            checkpoint_id: Unique ID for this checkpoint (auto-generated if not provided)
            **kwargs: Additional checkpoint data

        Returns:
            MigrationCheckpoint object
        """
        if checkpoint_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            checkpoint_id = f"checkpoint_{timestamp}"

        checkpoint = MigrationCheckpoint(
            checkpoint_id=checkpoint_id,
            timestamp=datetime.now().isoformat(),
            stage=stage,
            **kwargs
        )

        self._current_checkpoint = checkpoint
        self._checkpoints.append(checkpoint)

        # Save to file
        self._save_checkpoint(checkpoint)

        return checkpoint

    def _save_checkpoint(self, checkpoint: MigrationCheckpoint) -> str:
        """Save checkpoint to file."""
        filepath = self.backup_dir / f"{checkpoint.checkpoint_id}.json"

        with open(filepath, "w") as f:
            json.dump(checkpoint.to_dict(), f, indent=2)

        return str(filepath)

    def load_latest_checkpoint(self) -> Optional[MigrationCheckpoint]:
        """Load the most recent checkpoint."""
        checkpoint_files = list(self.backup_dir.glob("checkpoint_*.json"))

        if not checkpoint_files:
            return None

        # Sort by filename (which includes timestamp) and get latest
        latest = sorted(checkpoint_files)[-1]

        with open(latest, "r") as f:
            data = json.load(f)

        self._current_checkpoint = MigrationCheckpoint.from_dict(data)
        self._checkpoints.append(self._current_checkpoint)

        return self._current_checkpoint

    def get_stage(self) -> str:
        """Get current checkpoint stage."""
        if self._current_checkpoint:
            return self._current_checkpoint.stage
        return "none"

    def update_stage(self, stage: str, **kwargs) -> None:
        """Update checkpoint with new stage data."""
        if self._current_checkpoint is None:
            raise ValueError("No active checkpoint to update")

        for key, value in kwargs.items():
            if hasattr(self._current_checkpoint, key):
                setattr(self._current_checkpoint, key, value)

        self._current_checkpoint.stage = stage
        self._current_checkpoint.timestamp = datetime.now().isoformat()
        self._save_checkpoint(self._current_checkpoint)

    def clear_checkpoints(self) -> List[str]:
        """Clear all checkpoint files."""
        removed = []
        for checkpoint in self._checkpoints:
            filepath = self.backup_dir / f"{checkpoint.checkpoint_id}.json"
            if filepath.exists():
                filepath.unlink()
                removed.append(str(filepath))

        self._checkpoints = []
        self._current_checkpoint = None
        return removed

    def resume_from_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Resume migration from checkpoint.

        Returns:
            Dictionary with checkpoint data for resuming, or None if no checkpoint
        """
        checkpoint = self.load_latest_checkpoint()

        if checkpoint is None:
            return None

        return {
            "checkpoint_id": checkpoint.checkpoint_id,
            "stage": checkpoint.stage,
            "services_in_scope": checkpoint.services_in_scope,
            "duplicate_groups": checkpoint.duplicate_groups,
            "winner_selections": checkpoint.winner_selections,
            "migrated_policies": checkpoint.migrated_policies,
            "migrated_groups": checkpoint.migrated_groups,
            "deletions_prepared": checkpoint.deletions_prepared,
            "error_state": checkpoint.error_state,
        }


class AtomicMigrator:
    """Performs atomic migrations with checkpoint support."""

    def __init__(
        self,
        connection: Optional[object],
        dry_run: bool = True,
        checkpoint_manager: Optional[CheckpointManager] = None
    ):
        """
        Initialize atomic migrator.

        Args:
            connection: PanOS connection object
            dry_run: If True, only simulate without making changes
            checkpoint_manager: Optional checkpoint manager for resume capability
        """
        self.connection = connection
        self.dry_run = dry_run
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
        self._migration_records: List[MigrationRecord] = []

    def migrate_with_checkpoint(
        self,
        policies: List[Dict],
        groups: List[Any],
        duplicate_groups: Dict[str, List[str]],
    ) -> Dict:
        """
        Migrate references with checkpoint support.

        Args:
            policies: List of policy dictionaries to migrate
            groups: List of service groups to migrate
            duplicate_groups: Dict mapping group keys to service names

        Returns:
            Migration summary with checkpoint info
        """
        summary = {
            "policies_migrated": 0,
            "groups_migrated": 0,
            "policies_failed": [],
            "groups_failed": [],
            "checkpoint_id": None,
        }

        # Create initial checkpoint
        checkpoint = self.checkpoint_manager.create_checkpoint(
            stage="migration_started",
            services_in_scope=list(duplicate_groups.keys()),
            duplicate_groups=duplicate_groups,
        )
        summary["checkpoint_id"] = checkpoint.checkpoint_id

        # Migrate policies
        for policy in policies:
            policy_name = policy.get("name", "unknown")
            try:
                self._migrate_policy(policy, duplicate_groups)
                summary["policies_migrated"] += 1
                # Update checkpoint after each successful migration
                checkpoint.migrated_policies[policy_name] = {
                    str(k): str(v) for k, v in policy.get("service", []).items()
                }
                self.checkpoint_manager.update_stage("policy_migrated", checkpoint=checkpoint)
            except Exception as e:
                summary["policies_failed"].append({
                    "policy": policy_name,
                    "error": str(e),
                })
                # Log error but continue with other policies
                # In production, you might want to rollback here

        # Migrate groups
        for group in groups:
            group_name = group.name
            try:
                self._migrate_group(group, duplicate_groups)
                summary["groups_migrated"] += 1
                # Update checkpoint
                checkpoint.migrated_groups[group_name] = {
                    str(k): str(v) for k, v in group.members.items()
                }
                self.checkpoint_manager.update_stage("group_migrated", checkpoint=checkpoint)
            except Exception as e:
                summary["groups_failed"].append({
                    "group": group_name,
                    "error": str(e),
                })

        # Mark completion
        self.checkpoint_manager.update_stage(
            "migration_completed",
            checkpoint=checkpoint,
        )

        return summary

    def _migrate_policy(
        self,
        policy: Dict,
        duplicate_groups: Dict[str, List[str]]
    ) -> Dict[str, str]:
        """
        Migrate a single policy.

        Args:
            policy: Policy dictionary
            duplicate_groups: Duplicate group mappings

        Returns:
            Migration changes for this policy
        """
        service_field = policy.get("service", [])
        if not isinstance(service_field, list):
            service_field = [service_field]

        changes = {}
        new_services = []

        for svc in service_field:
            winner = self._get_winner_for_service(svc, duplicate_groups)
            if winner and winner != svc:
                new_services.append(winner)
                changes[svc] = winner
            else:
                new_services.append(svc)

        if changes:
            # Apply migration
            policy["service"] = new_services
            record = MigrationRecord(
                operation_type="update",
                object_type="policy",
                object_name=policy.get("name", "unknown"),
                old_value=str(service_field),
                new_value=str(new_services),
            )
            self._migration_records.append(record)

        return changes

    def _migrate_group(
        self,
        group: Any,
        duplicate_groups: Dict[str, List[str]]
    ) -> Dict[str, str]:
        """
        Migrate a single group.

        Args:
            group: Service group object
            duplicate_groups: Duplicate group mappings

        Returns:
            Migration changes for this group
        """
        members = group.members or []
        changes = {}
        new_members = []

        for member in members:
            winner = self._get_winner_for_service(member, duplicate_groups)
            if winner and winner != member:
                new_members.append(winner)
                changes[member] = winner
            else:
                new_members.append(member)

        if changes:
            group.members = new_members
            record = MigrationRecord(
                operation_type="update",
                object_type="group",
                object_name=group.name,
                old_value=str(members),
                new_value=str(new_members),
            )
            self._migration_records.append(record)

        return changes

    def _get_winner_for_service(
        self,
        service_name: str,
        duplicate_groups: Dict[str, List[str]]
    ) -> Optional[str]:
        """
        Get winner for a service from duplicate groups.

        Args:
            service_name: Name of service to look up
            duplicate_groups: Duplicate group mappings

        Returns:
            Winner service name or None
        """
        for group_key, services in duplicate_groups.items():
            if service_name in services:
                # Return alphabetically first
                return sorted(services)[0]
        return None

    def get_migration_summary(self) -> Dict:
        """Get migration summary."""
        return {
            "total_records": len(self._migration_records),
            "records": [r.to_dict() for r in self._migration_records],
        }


# Convenience functions for common operations

def atomic_migrate_services(
    policies: List[Dict],
    groups: List[Any],
    duplicate_groups: Dict[str, List[str]],
    connection: Optional[object] = None,
    dry_run: bool = True,
    backup_dir: str = "./backups"
) -> Dict:
    """
    Perform atomic service migration.

    Args:
        policies: List of policy dictionaries
        groups: List of service groups
        duplicate_groups: Duplicate group mappings
        connection: PanOS connection (optional)
        dry_run: If True, only simulate
        backup_dir: Directory for checkpoints

    Returns:
        Migration summary
    """
    checkpoint_manager = CheckpointManager(backup_dir)
    migrator = AtomicMigrator(connection, dry_run, checkpoint_manager)

    return migrator.migrate_with_checkpoint(
        policies, groups, duplicate_groups
    )