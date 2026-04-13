"""Unit tests for usage counting logic."""
import pytest

from src.models.service import Service, ServiceGroup
from src.services.usage import UsageCounter, count_service_usage


def test_count_policy_usage():
    """Test counting service usage in policies."""
    policies = [
        {"name": "policy1", "service": ["tcp-443-1", "tcp-80"]},
        {"name": "policy2", "service": ["tcp-443-1"]},
    ]
    
    counter = UsageCounter(policies, [])
    usage = counter.count_policy_usage()
    
    assert usage["tcp-443-1"] == 2
    assert usage["tcp-80"] == 1


def test_count_group_usage():
    """Test counting service usage in groups."""
    groups = [
        ServiceGroup(name="group1", members=["tcp-443-1"]),
        ServiceGroup(name="group2", members=["tcp-443-1", "tcp-80"]),
    ]
    
    counter = UsageCounter([], groups)
    usage = counter.count_group_usage()
    
    assert usage["tcp-443-1"] == 2
    assert usage["tcp-80"] == 1


def test_count_all():
    """Test counting total usage."""
    policies = [{"name": "p1", "service": ["tcp-443-1"]}]
    groups = [ServiceGroup(name="g1", members=["tcp-443-1"])]
    
    counter = UsageCounter(policies, groups)
    usage = counter.count_all()
    
    assert usage["tcp-443-1"] == 2


def test_get_policy_breakdown():
    """Test getting per-policy breakdown."""
    policies = [
        {"name": "policy1", "service": ["tcp-443-1"]},
        {"name": "policy2", "service": ["tcp-443-1"]},
    ]
    
    counter = UsageCounter(policies, [])
    breakdown = counter.get_policy_breakdown()
    
    assert breakdown["tcp-443-1"]["policy1"] == 1
    assert breakdown["tcp-443-1"]["policy2"] == 1


def test_count_service_usage():
    """Test standalone usage counting function."""
    policies = [{"name": "p1", "service": ["tcp-443"]}]
    groups = [ServiceGroup(name="g1", members=[])]

    svc = Service(name="tcp-443", protocol="tcp", port="443")
    usage = count_service_usage(svc, policies, groups)
    
    assert usage == 1


def test_no_usage():
    """Test handling of services with no usage."""
    policies = []
    groups = []
    
    counter = UsageCounter(policies, groups)
    usage = counter.count_all()
    
    assert usage == {}
