#SM|"""Integration tests for full cleanup workflow."""

#TJ|import pytest

#HB|from unittest.mock import MagicMock, patch

#MQ|import tempfile

#VK|import os

#SY|
import tempfile
import os

from src.models.service import Service, ServiceGroup
from src.services.duplicates import find_duplicates
from src.services.usage import UsageCounter
from src.policies.migration import ReferenceMigrator
from src.services.deletion import ServiceDeleter


def test_full_workflow_integration():
    """Test the complete workflow with mock data."""
    # Sample services with duplicates
    services = [
        Service(name="tcp-443-1", protocol="tcp", port="443"),
        Service(name="tcp-443-2", protocol="tcp", port="443"),
        Service(name="tcp-80-1", protocol="tcp", port="80"),
    ]
    
    # Find duplicates
    duplicates = find_duplicates(services)
    assert len(duplicates) == 1
    assert duplicates[0].key == "tcp:443"
    
    # Mock policies and groups
    policies = [
        {"name": "policy1", "service": ["tcp-443-1", "tcp-80-1"]},
        {"name": "policy2", "service": ["tcp-443-2"]},
    ]
    groups = [ServiceGroup(name="https-group", members=["tcp-443-1"])]
    
    # Count usage
    counter = UsageCounter(policies, groups)
    usage = counter.count_all()
    assert usage["tcp-443-1"] == 2
    assert usage["tcp-443-2"] == 1
    
    # Migrate references (dry-run)
    migrator = ReferenceMigrator(
        connection=None,
        dry_run=True,
        duplicate_groups={"tcp:443": ["tcp-443-1", "tcp-443-2"]}
    )
    
    policy_result = migrator.migrate_policy_refs()
    assert "policies_updated" in policy_result
    
    # Delete duplicates (dry-run)
    deleter = ServiceDeleter(connection=None, dry_run=True)
    dup_map = {"tcp:443": [services[0], services[1]]}
    del_result = deleter.delete_duplicates(dup_map, services_in_use=usage)
    assert del_result["services_deleted"] == 1


def test_workflow_with_rollback():
    """Test workflow with rollback capability."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from src.utils.rollback import RollbackManager
        from src.utils.backup import BackupManager
        
        # Create backup
        backup_manager = BackupManager(tmpdir)
        backup_manager.create_backup("<config>test</config>")
        
        # Verify backup exists
        backups = backup_manager.get_all_backups()
        assert len(backups) == 1
        
        # Rollback (dry-run mode)
        rollback = RollbackManager(backup_dir=tmpdir)
        result = rollback.rollback_all()
        assert "success" in result
        assert "backups_affected" in result