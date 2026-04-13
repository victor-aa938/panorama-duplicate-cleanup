"""Unit tests for service deletion logic."""
import pytest

from src.models.service import Service
from src.services.deletion import ServiceDeleter


def test_delete_duplicates():
    """Test duplicate deletion (dry-run mode)."""
    deleter = ServiceDeleter(connection=None, dry_run=True)
    
    duplicate_groups = {
        "tcp:443": [
            Service(name="tcp-443-1", protocol="tcp", port="443"),
            Service(name="tcp-443-2", protocol="tcp", port="443"),
        ]
    }
    
    result = deleter.delete_duplicates(duplicate_groups, services_in_use={})
    
    assert "services_deleted" in result
    assert "services_skipped" in result


def test_get_deletion_summary():
    """Test deletion summary."""
    deleter = ServiceDeleter(connection=None, dry_run=True)
    
    deleter.clear_cache()
    summary = deleter.get_deletion_summary()
    
    assert "total_services_prepared" in summary
    assert "services_to_delete" in summary


def test_generate_deletion_report():
    """Test deletion report generation."""
    deleter = ServiceDeleter(connection=None, dry_run=True)
    
    report = deleter.generate_deletion_report()
    assert "SERVICE DELETION REPORT" in report


def test_rollback_deletions():
    """Test rollback of deletions."""
    deleter = ServiceDeleter(connection=None, dry_run=True)
    
    result = deleter.rollback_deletions()
    
    assert "rollbacks_attempted" in result
    assert "rollbacks_completed" in result
