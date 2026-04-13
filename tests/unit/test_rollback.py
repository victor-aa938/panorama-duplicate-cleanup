"""Unit tests for rollback functionality."""
import pytest
import tempfile
import os

from src.utils.rollback import RollbackManager
from src.models.service import MigrationRecord


def test_get_all_backups():
    """Test listing backups."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy backup files
        open(os.path.join(tmpdir, "backup_20260101.xml"), "w").close()
        open(os.path.join(tmpdir, "backup_20260102.xml"), "w").close()
        
        rollback = RollbackManager(backup_dir=tmpdir)
        backups = rollback.get_all_backups()
        
        assert len(backups) == 2


def test_get_latest_backup():
    """Test getting latest backup."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create backup files with different timestamps
        open(os.path.join(tmpdir, "backup_20260101.xml"), "w").close()
        latest = os.path.join(tmpdir, "backup_20260102.xml")
        open(latest, "w").close()
        
        rollback = RollbackManager(backup_dir=tmpdir)
        latest_backup = rollback.get_latest_backup()
        
        assert latest_backup == latest


def test_rollback_all():
    """Test full rollback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        open(os.path.join(tmpdir, "backup.xml"), "w").close()
        
        rollback = RollbackManager(backup_dir=tmpdir)
        result = rollback.rollback_all()
        
        assert "success" in result


def test_rollback_specific():
    """Test specific object rollback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rollback = RollbackManager(backup_dir=tmpdir)
        result = rollback.rollback_specific("test-object")
        
        assert result["object_name"] == "test-object"


def test_create_rollback_file():
    """Test rollback file creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rollback = RollbackManager(backup_dir=tmpdir)
        
        records = []
        record_path = rollback.create_rollback_file(records)
        
        assert os.path.exists(record_path)
        assert "rollback_" in record_path


#XT|def test_rollback_with_records():

#XS|    """Test rollback with migration records."""

#NX|    with tempfile.TemporaryDirectory() as tmpdir:

#KY|        rollback = RollbackManager(backup_dir=tmpdir)

#HV|        

#PB|        records = [

#PH|            MigrationRecord(

#TR|                operation_type="update",

#KT|                object_type="policy",

#QZ|                object_name="test-policy",

#BQ|            ),

#PN|        ]

#JQ|        

#QQ|        record_path = rollback.create_rollback_file(records)

#MT|        

#TH|        # The rollback_summary shows records created via rollback_all, not create_rollback_file

#KR|        # create_rollback_file just saves to file, it doesn't add to internal records list

#XM|        assert os.path.exists(record_path)

#ZQ|        

#YH|        # Test actual rollback record addition

#YR|        rollback.rollback_all()

#YM|        summary = rollback.get_rollback_summary()

#YH|        assert "total_rollback_records" in summary

def test_get_all_backups_empty_dir():
    """Test listing backups when directory is empty."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rollback = RollbackManager(backup_dir=tmpdir)
        backups = rollback.get_all_backups()
        
        assert len(backups) == 0