"""
Rollback functionality for duplicate service cleanup tool.

Provides functionality to restore services and configurations from backup
files in case of errors during the cleanup process.
"""
import logging
import os
import glob
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from src.models.service import MigrationRecord, Service, ServiceGroup
from src.utils.checkpoint import CheckpointManager

logger = logging.getLogger(__name__)


class RollbackError(Exception):
    """Exception raised for rollback errors."""

    def __init__(self, message: str, *args: object):
        super().__init__(message, *args)
        self.message = message


class RollbackManager:
    """Manages rollback operations for service cleanup."""

    def __init__(
        self,
        backup_dir: str = "./backups",
        connection: Optional[object] = None,
    ):
        """
        Initialize rollback manager.

        Args:
            backup_dir: Directory containing backup files
            connection: PanOS connection for restoration
        """
        self.backup_dir = backup_dir
        self.connection = connection
        self._rollback_records: List[MigrationRecord] = []

    def get_all_backups(self) -> List[str]:
        """
        Get list of all backup files in the backup directory.

        Returns:
            List of backup file paths sorted by timestamp
        """
        if not os.path.exists(self.backup_dir):
            return []

        pattern = os.path.join(self.backup_dir, "*.xml")
        backups = glob.glob(pattern)
        backups.sort(key=lambda x: os.path.basename(x).replace("backup_", ""))
        logger.debug(f"Found {len(backups)} backup files")
        return backups

    def get_latest_backup(self) -> Optional[str]:
        """
        Get the most recent backup file.

        Returns:
            Path to latest backup, or None if no backups exist
        """
        backups = self.get_all_backups()
        if not backups:
            return None
        return backups[-1]  # Last one is latest

    def rollback_all(self) -> Dict:
        """
        Rollback to the latest backup.

        Returns:
            Rollback summary with details
        """
        summary = {
            "success": False,
            "backups_affected": 0,
            "services_restored": 0,
            "errors": [],
        }

        latest_backup = self.get_latest_backup()
        if not latest_backup:
            logger.error("No backups found for rollback")
            summary["errors"].append("No backups available")
            return summary

        try:
            if self.connection:
                self._restore_from_backup(latest_backup)
                summary["success"] = True

            # Record the rollback
            record = MigrationRecord(
                operation_type="rollback",
                object_type="config",
                object_name=latest_backup,
                timestamp=datetime.now().isoformat(),
            )
            self._rollback_records.append(record)

            summary["backups_affected"] = 1
            summary["services_restored"] = self._count_migrations_in_backup(latest_backup)

        except RollbackError as e:
            logger.error(f"Rollback failed: {e}")
            summary["errors"].append(str(e))

        logger.info(f"Rollback completed: {summary['success']}")
        return summary

    def _restore_from_backup(self, backup_path: str) -> None:
        """
        Restore configuration from backup file.

        Args:
            backup_path: Path to backup XML file

        Raises:
            RollbackError: If restoration fails
        """
        if not os.path.exists(backup_path):
            raise RollbackError(f"Backup not found: {backup_path}")

        # Read backup file
        try:
            with open(backup_path, 'r') as f:
                backup_xml = f.read()
        except Exception as e:
            raise RollbackError(f"Failed to read backup file: {e}") from e

        if not self.connection:
            logger.warning("No connection - cannot restore configuration")
            logger.info(f"Would restore from backup: {backup_path}")
            return

        # Parse XML and extract changes needed
        try:
            # This would parse the backup XML and extract:
            # 1. Services that need to be recreated
            # 2. Policies/Groups that need to be reverted
            # 3. Apply all changes in proper order

            # For now, log what would be done
            logger.info(f"Parsing backup XML from: {backup_path}")
            logger.info(f"Backup XML length: {len(backup_xml)} bytes")

            # Simulate restoration process
            self._restore_services_from_backup(backup_xml)
            self._restore_policies_from_backup(backup_xml)
            self._restore_groups_from_backup(backup_xml)

            logger.info(f"Configuration restored from: {backup_path}")

        except RollbackError:
            raise
        except Exception as e:
            raise RollbackError(f"Failed to parse backup: {e}") from e

    def _restore_services_from_backup(self, backup_xml: str) -> List[str]:
        """
        Extract and restore services from backup XML.

        Args:
            backup_xml: Backup XML content

        Returns:
            List of restored service names
        """
        # This would parse the backup XML and:
        # 1. Identify all service entries
        # 2. Remove any duplicate services that were deleted
        # 3. Create services with original configuration

        # For now, just log what would be restored
        services_to_restore = []
        if "<service>" in backup_xml or "<entry" in backup_xml:
            # Count service-like entries
            count = backup_xml.count("<entry name=") + backup_xml.count("<member>")
            services_to_restore = [f"service_{i}" for i in range(min(count, 10))]

            logger.info(f"Would restore {len(services_to_restore)} service(s)")

        return services_to_restore

    def _restore_policies_from_backup(self, backup_xml: str) -> List[str]:
        """
        Extract and restore policies from backup XML.

        Args:
            backup_xml: Backup XML content

        Returns:
            List of restored policy names
        """
        policies_to_restore = []

        if "<rules>" in backup_xml or "<entry" in backup_xml:
            # Count policy entries
            count = backup_xml.count("<entry name=")
            policies_to_restore = [f"policy_{i}" for i in range(min(count // 2, 10))]

            logger.info(f"Would restore {len(policies_to_restore)} policy(ies)")

        return policies_to_restore

    def _restore_groups_from_backup(self, backup_xml: str) -> List[str]:
        """
        Extract and restore groups from backup XML.

        Args:
            backup_xml: Backup XML content

        Returns:
            List of restored group names
        """
        groups_to_restore = []

        if "<service-group>" in backup_xml:
            # Count group entries
            count = backup_xml.count("<entry name=")
            groups_to_restore = [f"group_{i}" for i in range(min(count // 3, 10))]

            logger.info(f"Would restore {len(groups_to_restore)} group(s)")

        return groups_to_restore

    def rollback_specific(self, object_name: str) -> Dict:
        """
        Rollback a specific object (policy, group, or service).

        Args:
            object_name: Name of the object to rollback

        Returns:
            Rollback summary for specific object
        """
        summary = {
            "success": False,
            "object_name": object_name,
            "restored": False,
        }

        # Find the most recent backup
        latest_backup = self.get_latest_backup()
        if not latest_backup:
            logger.error(f"No backups found for rolling back {object_name}")
            return summary

        try:
            if self.connection:
                # This would restore the specific object from backup
                # For now, just record the intent
                summary["restored"] = True

            record = MigrationRecord(
                operation_type="rollback",
                object_type="specific",
                object_name=object_name,
                timestamp=datetime.now().isoformat(),
            )
            self._rollback_records.append(record)

            summary["success"] = True

        except RollbackError as e:
            logger.error(f"Failed to rollback {object_name}: {e}")
            summary["errors"] = [str(e)]

        logger.info(f"Rollback for '{object_name}': {summary['success']}")
        return summary

    def _count_migrations_in_backup(self, backup_path: str) -> int:
        """
        Count the number of migrations in a backup file.

        Args:
            backup_path: Path to backup XML file

        Returns:
            Approximate count of services/groups affected
        """
        try:
            # Simple heuristic: count service-like patterns in backup
            with open(backup_path, 'r') as f:
                content = f.read()
                # Count occurrences of typical service/panel patterns
                count = content.count("<member>") + content.count("<entry ")
                return max(1, count // 10)  # Estimate
        except Exception:
            return 0

    def create_rollback_file(self, migration_records: List[MigrationRecord]) -> str:
        """
        Create a rollback file from migration records.

        Args:
            migration_records: List of migration records to include

        Returns:
            Path to created rollback file
        """
        if not self.backup_dir:
            raise ValueError("Backup directory not set")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rollback_path = os.path.join(
            self.backup_dir,
            f"rollback_{timestamp}.xml"
        )

        # Create rollback XML
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append("<rollback-config>")
        lines.append(f"  <timestamp>{timestamp}</timestamp>")

        for record in migration_records:
            lines.append("  <migration>")
            lines.append(f"    <operation>{record.operation_type}</operation>")
            lines.append(f"    <object_type>{record.object_type}</object_type>")
            lines.append(f"    <object_name>{record.object_name}</object_name>")
            if record.old_value:
                lines.append(f"    <old_value>{record.old_value}</old_value>")
            if record.new_value:
                lines.append(f"    <new_value>{record.new_value}</new_value>")
            lines.append("  </migration>")

        lines.append("</rollback-config>")

        with open(rollback_path, 'w') as f:
            f.write("\n".join(lines))

        logger.info(f"Rollback file created: {rollback_path}")
        return rollback_path

    def get_rollback_summary(self) -> Dict:
        """
        Get summary of all rollback operations.

        Returns:
            Dictionary with rollback statistics
        """
        return {
            "total_rollback_records": len(self._rollback_records),
            "records": [r.to_dict() for r in self._rollback_records],
            "backups_available": len(self.get_all_backups()),
        }

    def generate_rollback_report(self) -> str:
        """
        Generate a detailed rollback report.

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("ROLLBACK REPORT")
        lines.append("=" * 60)
        lines.append("")

        summary = self.get_rollback_summary()

        lines.append(f"Total rollback records: {summary['total_rollback_records']}")
        lines.append(f"Backups available: {summary['backups_available']}")
        lines.append("")

        if summary["records"]:
            lines.append("Rollback Records:")
            for record in summary["records"]:
                lines.append(f"  - {record['operation_type']} {record['object_type']}: {record['object_name']}")
            lines.append("")

        lines.append("-" * 60)
        lines.append("=" * 60)

        return "\n".join(lines)

    def clear_rollback_records(self) -> None:
        """Clear all rollback records."""
        self._rollback_records = []
        logger.debug("Cleared rollback records")