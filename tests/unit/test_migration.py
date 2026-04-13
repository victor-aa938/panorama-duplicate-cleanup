"""Unit tests for reference migration logic."""
import pytest

from src.policies.migration import ReferenceMigrator


def test_migrate_policy_refs():
    """Test policy reference migration (dry-run mode)."""
    migrator = ReferenceMigrator(connection=None, dry_run=True, duplicate_groups={
        "tcp:443": ["tcp-443-1", "tcp-443-2"]
    })
    
    result = migrator.migrate_policy_refs()
    
    assert "policies_updated" in result
    assert "policies_unchanged" in result


def test_migrate_group_refs():
    """Test group reference migration (dry-run mode)."""
    migrator = ReferenceMigrator(connection=None, dry_run=True, duplicate_groups={
        "tcp:443": ["tcp-443-1", "tcp-443-2"]
    })
    
    result = migrator.migrate_group_refs()
    
    assert "groups_updated" in result
    assert "groups_unchanged" in result


def test_get_migration_summary():
    """Test migration summary generation."""
    migrator = ReferenceMigrator(connection=None, dry_run=True, duplicate_groups={})
    
    migrator.clear_cache()
    summary = migrator.get_migration_summary()
    
    assert "total_policies_migrated" in summary
    assert "total_groups_migrated" in summary


def test_generate_migration_report():
    """Test report generation."""
    migrator = ReferenceMigrator(connection=None, dry_run=True, duplicate_groups={})
    
    report = migrator.generate_migration_report()
    assert "REFERENCE MIGRATION REPORT" in report
