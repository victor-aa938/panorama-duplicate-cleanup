"""Unit tests for duplicate detection logic."""
import pytest

from src.models.service import Service
from src.services.duplicates import (
    find_duplicates,
    group_duplicates,
    get_duplicate_sets,
    get_unique_services,
    generate_duplicate_report,
)


def test_find_duplicates():
    """Test duplicate detection finds duplicate services."""
    services = [
        Service(name="tcp-443-1", protocol="tcp", port="443"),
        Service(name="tcp-443-2", protocol="tcp", port="443"),
        Service(name="tcp-80-1", protocol="tcp", port="80"),
    ]
    
    duplicates = find_duplicates(services)
    
    assert len(duplicates) == 1
    assert duplicates[0].key == "tcp:443"
    assert len(duplicates[0].services) == 2


def test_group_duplicates():
    """Test grouping services by protocol:port."""
    services = [
        Service(name="svc1", protocol="tcp", port="443"),
        Service(name="svc2", protocol="tcp", port="443"),
        Service(name="svc3", protocol="udp", port="53"),
    ]
    
    groups = group_duplicates(services)
    
    assert "tcp:443" in groups
    assert len(groups["tcp:443"]) == 2
    assert "udp:53" in groups


def test_get_duplicate_sets():
    """Test getting only duplicate sets."""
    services = [
        Service(name="tcp-443-1", protocol="tcp", port="443"),
        Service(name="tcp-443-2", protocol="tcp", port="443"),
        Service(name="tcp-80-1", protocol="tcp", port="80"),
    ]
    
    dup_sets = get_duplicate_sets(services)
    
    assert len(dup_sets) == 1
    assert dup_sets[0][0] == "tcp:443"


def test_get_unique_services():
    """Test getting services with no duplicates."""
    services = [
        Service(name="tcp-443-1", protocol="tcp", port="443"),
        Service(name="tcp-443-2", protocol="tcp", port="443"),
        Service(name="tcp-80-1", protocol="tcp", port="80"),
    ]
    
    unique = get_unique_services(services)
    
    assert len(unique) == 1
    assert unique[0].name == "tcp-80-1"


def test_generate_duplicate_report():
    """Test report generation."""
    services = [
        Service(name="tcp-443-1", protocol="tcp", port="443"),
        Service(name="tcp-443-2", protocol="tcp", port="443"),
    ]
    
    report = generate_duplicate_report(services)
    
    assert "tcp:443" in report
    assert "tcp-443-1" in report
    assert "tcp-443-2" in report


def test_empty_service_list():
    """Test handling of empty service list."""
    duplicates = find_duplicates([])
    assert duplicates == []
    
    groups = group_duplicates([])
    assert groups == {}
    
    unique = get_unique_services([])
    assert unique == []
