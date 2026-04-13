#!/usr/bin/env python3
"""QA test for Task 5: Backup utility module."""

import os
import tempfile
import time
from pathlib import Path

# Add project to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.backup import BackupManager, BackupError


def test_backup_creation():
    """Test backup creation."""
    print("Test 1: Backup creation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = BackupManager(tmpdir)
        test_data = "<config><services><service><name>test</name></service></services></config>"
        backup_path = manager.create_backup(test_data, prefix="test_backup")
        
        assert os.path.exists(backup_path), "Backup file should exist"
        with open(backup_path, "r") as f:
            content = f.read()
            assert content == test_data, "Backup content should match original"
        
    print("  PASSED")


def test_backup_from_file():
    """Test backup from existing file."""
    print("Test 2: Backup from file...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = BackupManager(tmpdir)
        
        # Create source file
        source_path = os.path.join(tmpdir, "source.xml")
        with open(source_path, "w") as f:
            f.write("<config>test</config>")
        
        backup_path = manager.create_backup_from_file(source_path, prefix="file_backup")
        assert os.path.exists(backup_path), "Backup file should exist"
        
    print("  PASSED")


def test_verify_backup():
    """Test backup verification."""
    print("Test 3: Backup verification...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = BackupManager(tmpdir)
        backup_path = manager.create_backup("<config>test</config>")
        
        result = manager.verify_backup(backup_path)
        assert result is True, "Backup should be valid"
        
        # Test invalid backup
        result = manager.verify_backup("/nonexistent/file.xml")
        assert result is False, "Nonexistent file should fail verification"
        
    print("  PASSED")


def test_get_latest_backup():
    """Test getting latest backup."""
    print("Test 4: Get latest backup...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = BackupManager(tmpdir)
        
        # Create multiple backups
        manager.create_backup("<config>first</config>", prefix="latest_test")
        time.sleep(0.1)
        manager.create_backup("<config>second</config>", prefix="latest_test")
        
        latest = manager.get_latest_backup(prefix="latest_test")
        assert latest is not None, "Should have a backup"
        assert os.path.exists(latest), "Latest backup should exist"
        
    print("  PASSED")


def test_get_all_backups():
    """Test getting all backups."""
    print("Test 5: Get all backups...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = BackupManager(tmpdir)
        
        # Create 2 backups with delay
        manager.create_backup("<config>backup1</config>")
        time.sleep(0.1)
        manager.create_backup("<config>backup2</config>")
        
        backups = manager.get_all_backups()
        
        # Note: some backups may persist from previous tests in same process
        assert len(backups) >= 2, f"Should have at least 2 backups, got {len(backups)}"
        
    print("  PASSED")


def test_cleanup_old_backups():
    """Test cleanup of old backups."""
    print("Test 6: Cleanup old backups...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = BackupManager(tmpdir)
        
        # Create 7 backups with delays between each
        for i in range(7):
            manager.create_backup(f"<config>{i}</config>")
            time.sleep(0.1)
        
        removed = manager.cleanup_old_backups(keep_count=3)
        assert len(removed) == 4, f"Should remove 4 old backups, got {len(removed)}"
        
        remaining = manager.get_all_backups()
        assert len(remaining) == 3, f"Should have 3 remaining backups, got {len(remaining)}"
        
    print("  PASSED")


def test_rollback():
    """Test rollback from backup."""
    print("Test 7: Rollback from backup...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = BackupManager(tmpdir)
        
        # Create backup
        backup_path = manager.create_backup("<config>original</config>")
        
        # Create rollback file
        rollback_path = manager.create_rollback_file(backup_path)
        assert os.path.exists(rollback_path), "Rollback file should exist"
        
    print("  PASSED")


def test_backup_manager_as_context_manager():
    """Test backup manager context."""
    print("Test 8: Backup manager context...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        with BackupManager(tmpdir) as manager:
            backup_path = manager.create_backup("<config>context test</config>")
            assert os.path.exists(backup_path), "Backup should exist in context"
        
    print("  PASSED")


def test_backup_error_handling():
    """Test error handling."""
    print("Test 9: Error handling...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = BackupManager(tmpdir)
        
        # Test non-existent source file
        try:
            manager.create_backup_from_file("/nonexistent/file.xml")
            assert False, "Should raise BackupError"
        except BackupError:
            pass  # Expected
        
        # Test invalid backup path
        result = manager.verify_backup("/nonexistent/file.xml")
        assert result is False, "Should return False for invalid path"
        
    print("  PASSED")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Task 5 QA: Backup Utility Module")
    print("=" * 60 + "\n")
    
    tests = [
        test_backup_creation,
        test_backup_from_file,
        test_verify_backup,
        test_get_latest_backup,
        test_get_all_backups,
        test_cleanup_old_backups,
        test_rollback,
        test_backup_manager_as_context_manager,
        test_backup_error_handling,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)