"""Unit tests for service data model."""
import pytest

from src.models.service import Service, ServiceGroup, ServicePolicyReference, DuplicateGroup, MigrationRecord


def test_service_creation():
    """Test Service object creation."""
    svc = Service(name="tcp-443", protocol="tcp", port="443")
    assert svc.name == "tcp-443"
    assert svc.protocol == "tcp"
    assert svc.port == "443"
    assert svc.description is None


def test_service_from_dict():
    """Test creating Service from dictionary."""
    data = {
        "name": "tcp-443",
        "protocol": "tcp",
        "port": "443",
        "description": "HTTPS service",
    }
    svc = Service.from_dict(data)
    assert svc.name == "tcp-443"
    assert svc.description == "HTTPS service"


def test_service_to_dict():
    """Test converting Service to dictionary."""
    svc = Service(name="tcp-443", protocol="tcp", port="443", description="HTTPS")
    result = svc.to_dict()
    assert result["name"] == "tcp-443"
    assert result["description"] == "HTTPS"


def test_service_equality():
    """Test Service equality based on protocol and port."""
    svc1 = Service(name="svc-1", protocol="tcp", port="443")
    svc2 = Service(name="svc-2", protocol="tcp", port="443")
    svc3 = Service(name="svc-3", protocol="udp", port="443")
    
    assert svc1 == svc2
    assert svc1 != svc3


def test_duplicate_group_creation():
    """Test DuplicateGroup object creation."""
    services = [
        Service(name="tcp-443-1", protocol="tcp", port="443"),
        Service(name="tcp-443-2", protocol="tcp", port="443"),
    ]
    group = DuplicateGroup(key="tcp:443", services=services)
    assert group.key == "tcp:443"
    assert len(group.services) == 2


def test_migration_record_creation():
    """Test MigrationRecord object creation."""
    record = MigrationRecord(
        operation_type="update",
        object_type="policy",
        object_name="test-policy",
    )
    assert record.operation_type == "update"
    assert record.object_type == "policy"
    assert record.object_name == "test-policy"
