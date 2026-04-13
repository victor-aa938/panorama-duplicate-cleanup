"""
Backup utility module.

Provides backup and rollback functionality for Panorama configurations.
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.utils.logger import get_logger

logger = get_logger(__name__)


class BackupError(Exception):
    """Exception raised for backup-related errors."""


class BackupManager:
    """Manages backup and rollback operations."""

    def __init__(self, backup_dir: Optional[str] = None):
        self.backup_dir = backup_dir or "./backups"
        self._ensure_backup_dir()
        self._backups: List[Dict[str, Any]] = []

    def _ensure_backup_dir(self) -> None:
        path = Path(self.backup_dir)
        path.mkdir(parents=True, exist_ok=True)

    def _generate_timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    def _generate_filename(self, prefix: str = "backup") -> str:
        timestamp = self._generate_timestamp()
        return f"{prefix}_{timestamp}"

    def create_backup(self, data: str, prefix: str = "backup") -> str:
        filename = self._generate_filename(prefix)
        filepath = Path(self.backup_dir) / f"{filename}.xml"

        with open(filepath, "w") as f:
            f.write(data)

        self._backups.append({
            "path": str(filepath),
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "type": "config",
        })

        logger.info(f"Backup created: {filepath}")
        return str(filepath)

    def create_backup_from_file(
        self, source_path: str, prefix: str = "backup"
    ) -> str:
        if not os.path.exists(source_path):
            raise BackupError(f"Source file not found: {source_path}")

        filename = self._generate_filename(prefix)
        dest_path = Path(self.backup_dir) / f"{filename}.xml"

        shutil.copy2(source_path, dest_path)

        self._backups.append({
            "path": str(dest_path),
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "type": "file_copy",
        })

        logger.info(f"Backup created from file: {dest_path}")
        return str(dest_path)

    def create_rollback_file(self, backup_path: str) -> str:
        if not os.path.exists(backup_path):
            raise BackupError(f"Backup file not found: {backup_path}")

        rollback_data = {
            "backup_path": backup_path,
            "created_at": datetime.now().isoformat(),
            "rollback_id": f"rollback_{self._generate_timestamp()}",
            "version": "1.0",
        }

        rollback_path = Path(self.backup_dir) / f"rollback_{self._generate_timestamp()}.json"

        with open(rollback_path, "w") as f:
            json.dump(rollback_data, f, indent=2)

        logger.info(f"Rollback file created: {rollback_path}")
        return str(rollback_path)

    def verify_backup(self, backup_path: str) -> bool:
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False

        if not os.path.isfile(backup_path):
            logger.error(f"Backup path is not a file: {backup_path}")
            return False

        try:
            with open(backup_path, "r") as f:
                content = f.read()
                if not content:
                    logger.error(f"Backup file is empty: {backup_path}")
                    return False
            logger.info(f"Backup verified: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to verify backup: {e}")
            return False

    def get_latest_backup(self, prefix: str = "backup") -> Optional[str]:
        backup_files = []
        for f in Path(self.backup_dir).glob(f"{prefix}_*.xml"):
            backup_files.append(f)

        if not backup_files:
            return None

        return str(sorted(backup_files)[-1])

    def get_all_backups(self) -> List[Dict[str, Any]]:
        backups = []
        for f in Path(self.backup_dir).glob("*.xml"):
            backups.append({
                "path": str(f),
                "name": f.name,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
        return sorted(backups, key=lambda x: x["modified"], reverse=True)

    def cleanup_old_backups(
        self, keep_count: int = 5, prefix: str = "backup"
    ) -> List[str]:
        backup_files = sorted(
            Path(self.backup_dir).glob(f"{prefix}_*.xml"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        removed = []
        for backup_file in backup_files[keep_count:]:
            backup_file.unlink()
            removed.append(str(backup_file))
            logger.info(f"Removed old backup: {backup_file}")

        return removed

    def rollback_from_file(self, backup_path: str, dest_path: str) -> bool:
        if not self.verify_backup(backup_path):
            raise BackupError(f"Invalid backup file: {backup_path}")

        try:
            shutil.copy2(backup_path, dest_path)
            logger.info(f"Rolled back to: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
    
    def save_duplicate_report(self, duplicate_groups: List[Any], policies: List[Any], service_groups: List[Any], winner_selections: Optional[Dict[str, str]] = None) -> str:
        """
        Save a backup report of duplicates and affected policies/groups.
        
        Args:
            duplicate_groups: List of DuplicateGroup objects
            policies: List of policy dictionaries
            service_groups: List of ServiceGroup objects
            winner_selections: Dict mapping duplicate keys to winner service names
            
        Returns:
            Path to saved report file
        """
        filename = self._generate_filename("duplicate_report")
        filepath = Path(self.backup_dir) / f"{filename}.json"
        
        # Build report data
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "duplicate_groups": [],
            "policies_using_winners": [],
            "policies_to_be_modified": [],
            "affected_service_groups": [],
            "summary": {
                "total_duplicate_groups": len(duplicate_groups),
                "total_services_in_duplicates": 0,
                "total_policies_using_winners": 0,
                "total_policies_to_be_modified": 0,
                "total_affected_service_groups": 0,
            }
        }
        
        # Collect all duplicate service names and winners
        all_duplicate_names = set()
        winner_services = set()
        loser_services = set()
        
        for group in duplicate_groups:
            group_data = {
                "key": group.key,
                "winner": winner_selections.get(group.key) if winner_selections else None,
                "services": []
            }
            
            winner_name = winner_selections.get(group.key) if winner_selections else None
            
            for service in group.services:
                service_name = service.name if hasattr(service, 'name') else str(service)
                all_duplicate_names.add(service_name)
                
                if winner_name and service_name == winner_name:
                    winner_services.add(service_name)
                elif winner_name:
                    loser_services.add(service_name)
                
                group_data["services"].append({
                    "name": service_name,
                    "protocol": getattr(service, 'protocol', ''),
                    "port": getattr(service, 'port', ''),
                    "device_group": getattr(service, 'device_group', ''),
                    "is_winner": service_name == winner_name if winner_name else None,
                })
            report_data["duplicate_groups"].append(group_data)
            report_data["summary"]["total_services_in_duplicates"] += len(group.services)
        
        # Categorize policies
        for policy in policies:
            policy_services = policy.get('services', []) if isinstance(policy, dict) else getattr(policy, 'services', [])
            if not isinstance(policy_services, list):
                policy_services = [policy_services]
            
            # Check if policy uses any duplicate services
            used_duplicates = [svc for svc in policy_services if svc in all_duplicate_names]
            if not used_duplicates:
                continue
            
            policy_info = {
                "name": policy.get('name') if isinstance(policy, dict) else getattr(policy, 'name', 'unknown'),
                "type": policy.get('type') if isinstance(policy, dict) else getattr(policy, 'type', 'security'),
                "device_group": policy.get('device_group') if isinstance(policy, dict) else getattr(policy, 'device_group', ''),
                "services_used": used_duplicates,
            }
            
            # Determine if policy uses winner or loser services
            uses_winner = any(svc in winner_services for svc in used_duplicates)
            uses_loser = any(svc in loser_services for svc in used_duplicates)
            
            if uses_loser:
                # Policy will be modified on commit (uses duplicate that will be replaced)
                report_data["policies_to_be_modified"].append(policy_info)
                report_data["summary"]["total_policies_to_be_modified"] += 1
            elif uses_winner:
                # Policy already uses winner, no modification needed
                report_data["policies_using_winners"].append(policy_info)
                report_data["summary"]["total_policies_using_winners"] += 1
        
        # Find affected service groups
        for group in service_groups:
            members = group.get('members', []) if isinstance(group, dict) else getattr(group, 'members', [])
            affected_members = [m for m in members if m in all_duplicate_names]
            if affected_members:
                report_data["affected_service_groups"].append({
                    "name": group.get('name') if isinstance(group, dict) else getattr(group, 'name', 'unknown'),
                    "duplicate_members": affected_members,
                })
                report_data["summary"]["total_affected_service_groups"] += 1
        
        # Save JSON report
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Save policy backup file
        policy_backup_path = Path(self.backup_dir) / f"{filename}_policies.txt"
        with open(policy_backup_path, 'w') as f:
            f.write("POLICIES UNCHANGED (using winners)\n")
            f.write("-" * 80 + "\n")
            for p in report_data['policies_using_winners']:
                f.write(f"{p['name']}\n")
            f.write(f"\nTotal: {len(report_data['policies_using_winners'])}\n\n")
            
            f.write("POLICIES TO BE CHANGED (using duplicates)\n")
            f.write("-" * 80 + "\n")
            for p in report_data['policies_to_be_modified']:
                f.write(f"{p['name']}\n")
            f.write(f"\nTotal: {len(report_data['policies_to_be_modified'])}\n")
        
        logger.info(f"Duplicate report saved: {filepath}")
        return str(filepath)


def create_backup(data: str, backup_dir: str = "./backups", prefix: str = "backup") -> str:
    manager = BackupManager(backup_dir)
    return manager.create_backup(data, prefix)


def create_rollback(backup_path: str, backup_dir: str = "./backups") -> str:
    manager = BackupManager(backup_dir)
    return manager.create_rollback_file(backup_path)