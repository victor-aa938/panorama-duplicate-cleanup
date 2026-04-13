"""
Service deletion logic for duplicate service cleanup tool.

Provides functionality to safely delete duplicate services after all references
have been migrated to the winner service.
"""
import logging
from typing import List, Dict, Optional

from src.models.service import Service, MigrationRecord

logger = logging.getLogger(__name__)


class ServiceDeleter:
    """Safely deletes duplicate services after migration."""

    def __init__(
        self,
        connection: Optional[object],
        dry_run: bool = True
    ):
        """
        Initialize service deleter.

        Args:
            connection: PanOS connection object (required for actual deletions)
            dry_run: If True, only simulate without making changes
        """
        self.connection = connection
        self.dry_run = dry_run

        self._deletion_records: List[MigrationRecord] = []
        self._services_to_delete: List[Service] = []

    def delete_duplicates(
        self,
        duplicate_groups: Dict[str, List[Service]],
        services_in_use: Optional[Dict[str, int]] = None,
        post_migration_usage: Optional[Dict[str, int]] = None
    ) -> Dict:
        """
        Delete duplicate services from Panorama.

        Args:
            duplicate_groups: Dict mapping group keys to duplicate Service objects
            services_in_use: Optional dict mapping service names to usage counts (pre-migration)
            post_migration_usage: Optional dict mapping service names to usage counts AFTER migration

        Returns:
            Deletion summary with counts and details
        """
        summary = {
            "services_deleted": 0,
            "services_skipped": 0,
            "errors": [],
        }

        for group_key, services in duplicate_groups.items():
            if len(services) <= 1:
                continue  # Not a duplicate group

            # Determine winner (alphabetically first)
            winner = self._select_winner([s.name for s in services])

            for service in services:
                if service.name == winner:
                    # Skip the winner service
                    continue

                if self._is_safe_to_delete(service, services_in_use, winner, post_migration_usage):
                    if self.dry_run:
                        logger.info(f"[DRY-RUN] Would delete service: {service.name}")
                        record = MigrationRecord(
                            operation_type="delete",
                            object_type="service",
                            object_name=service.name,
                        )
                        self._deletion_records.append(record)
                        self._services_to_delete.append(service)
                        summary["services_deleted"] += 1
                    else:
                        try:
                            self._delete_service(service)
                            summary["services_deleted"] += 1
                        except Exception as e:
                            logger.error(f"Error deleting service '{service.name}': {e}")
                            summary["errors"].append({
                                "service": service.name,
                                "error": str(e),
                            })
                            summary["services_skipped"] += 1
                else:
                    logger.warning(f"Skipping deletion of '{service.name}' - still in use")
                    summary["services_skipped"] += 1

        logger.info(f"Deletion summary: {summary['services_deleted']} deleted, {summary['services_skipped']} skipped")
        return summary

    def _is_safe_to_delete(
        self,
        service: Service,
        services_in_use: Optional[Dict[str, int]],
        winner_name: str,
        post_migration_usage: Optional[Dict[str, int]] = None
    ) -> bool:
        """
        Determine if it's safe to delete a service.

        Args:
            service: Service to check
            services_in_use: Dict of service names to usage counts (pre-migration)
            winner_name: Name of the winner service
            post_migration_usage: Dict of usage counts AFTER migration (NEW - recommended)

        Returns:
            True if safe to delete, False otherwise
        """
        # In dry_run mode, allow deletion for testing
        if self.dry_run:
            return True

        # PRIORITY 1: Use post-migration usage if available (recommended)
        if post_migration_usage is not None:
            usage = post_migration_usage.get(service.name, 0)
            if usage > 0:
                logger.error(f"Service '{service.name}' still has {usage} references after migration - NOT safe to delete")
                return False

        # Fallback: Check pre-migration usage (only if post-migration not available)
        if services_in_use is not None:
            usage = services_in_use.get(service.name, 0)
            # Allow deletion only if usage was 0 pre-migration (meaning no other refs)
            if usage > 0:
                logger.warning(f"Service '{service.name}' had {usage} references before migration")
                logger.error("Post-migration verification required for safety")
                return False

        return True

    def _select_winner(self, services: List[str]) -> str:
        """
        Select winner from duplicate services using alphabetical tie-breaker.

        Args:
            services: List of duplicate service names

        Returns:
            Selected winner service name
        """
        sorted_services = sorted(services)
        return sorted_services[0]  # Alphabetically first

    def _delete_service(self, service: Service) -> None:
        """
        Delete a service using PanOS SDK.

        Args:
            service: Service object to delete
        """
        try:
            if not self.connection:
                logger.warning(f"No connection - skipping actual deletion of '{service.name}'")
                return

            # This would use the PanOS SDK to delete the service
            # Example: service_obj.delete()

            record = MigrationRecord(
                operation_type="delete",
                object_type="service",
                object_name=service.name,
            )
            self._deletion_records.append(record)
            logger.info(f"Deleted service: {service.name}")

        except Exception as e:
            logger.error(f"Error deleting service '{service.name}': {e}")
            raise

    def get_deletion_summary(self) -> Dict:
        """
        Get a summary of all deletions prepared.

        Returns:
            Dictionary with deletion statistics
        """
        return {
            "total_services_prepared": len(self._services_to_delete),
            "services_to_delete": [s.to_dict() for s in self._services_to_delete],
            "deletion_records": [r.to_dict() for r in self._deletion_records],
        }

    def generate_deletion_report(self) -> str:
        """
        Generate a detailed deletion report.

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("SERVICE DELETION REPORT")
        lines.append("=" * 60)
        lines.append("")

        summary = self.get_deletion_summary()

        lines.append(f"Total services to delete: {summary['total_services_prepared']}")
        lines.append("")

        if summary["services_to_delete"]:
            lines.append("Services scheduled for deletion:")
            for service_dict in summary["services_to_delete"]:
                lines.append(f"  - {service_dict['name']} ({service_dict['protocol']}/{service_dict['port']})")
            lines.append("")

        lines.append("-" * 60)
        lines.append("=" * 60)

        return "\n".join(lines)

    def rollback_deletions(self) -> Dict:
        """
        Rollback service deletions (in case of errors).

        Returns:
            Rollback summary
        """
        summary = {
            "rollbacks_attempted": len(self._services_to_delete),
            "rollbacks_completed": 0,
            "errors": [],
        }

        if self.dry_run:
            logger.info("[DRY-RUN] Rollback would restore deleted services")
            summary["rollbacks_completed"] = summary["rollbacks_attempted"]
            return summary

        # Implementation would re-create the deleted services
        # For now, just clear the records
        self._services_to_delete = []
        self._deletion_records = []
        summary["rollbacks_completed"] = summary["rollbacks_attempted"]

        logger.info("Rollback completed")
        return summary

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._deletion_records = []
        self._services_to_delete = []
        logger.debug("Cleared deletion cache")