"""
Service models for duplicate service cleanup tool.

Provides data classes for representing services, service groups, and policy references.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class Service:
    """Represents a Palo Alto service object."""
    name: str
    protocol: str
    port: str
    description: Optional[str] = None
    tag: List[str] = field(default_factory=list)
    members: List[str] = field(default_factory=list)
    device_group: Optional[str] = None
    
    def __hash__(self):
        return hash((self.protocol, self.port))
    
    def __eq__(self, other):
        if not isinstance(other, Service):
            return False
        return self.protocol == other.protocol and self.port == other.port
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "protocol": self.protocol,
            "port": self.port,
            "description": self.description,
            "tag": self.tag,
            "members": self.members,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Service":
        """Create Service from dictionary."""
        return cls(
            name=data["name"],
            protocol=data["protocol"],
            port=data["port"],
            description=data.get("description"),
            tag=data.get("tag", []),
            members=data.get("members", []),
        )
    
    @classmethod
    def from_panos(cls, panos_service: Any) -> "Service":
        """Create Service from PanOS SDK Service object."""
        return cls(
            name=panos_service.name,
            protocol=panos_service.protocol,
            port=getattr(panos_service, "port", ""),
            description=getattr(panos_service, "description", ""),
            tag=getattr(panos_service, "tag", []),
            members=getattr(panos_service, "members", []),
        )


@dataclass
class ServiceGroup:
    """Represents a Palo Alto service group."""
    name: str
    members: List[str] = field(default_factory=list)
    description: Optional[str] = None
    tag: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "members": self.members,
            "description": self.description,
            "tag": self.tag,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceGroup":
        """Create ServiceGroup from dictionary."""
        return cls(
            name=data["name"],
            members=data.get("members", []),
            description=data.get("description"),
            tag=data.get("tag", []),
        )
    
    @classmethod
    def from_panos(cls, panos_group: Any) -> "ServiceGroup":
        """Create ServiceGroup from PanOS SDK ServiceGroup object."""
        return cls(
            name=panos_group.name,
            members=getattr(panos_group, "members", []),
            description=getattr(panos_group, "description", ""),
            tag=getattr(panos_group, "tag", []),
        )


@dataclass
class ServicePolicyReference:
    """Represents a service reference in a security policy."""
    policy_name: str
    service: str
    rule_type: str  # 'security' or 'service-group'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "policy_name": self.policy_name,
            "service": self.service,
            "rule_type": self.rule_type,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServicePolicyReference":
        """Create ServicePolicyReference from dictionary."""
        return cls(
            policy_name=data["policy_name"],
            service=data["service"],
            rule_type=data["rule_type"],
        )


@dataclass
class DuplicateGroup:
    """Represents a group of duplicate services."""
    key: str  # Protocol + port combination (e.g., "tcp:443")
    services: List[Service] = field(default_factory=list)
    total_usage: int = 0
    usage_by_policy: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "service_names": [s.name for s in self.services],
            "total_usage": self.total_usage,
            "usage_by_policy": self.usage_by_policy,
        }


@dataclass
class MigrationRecord:
    """Records a migration operation for rollback."""
    operation_type: str  # 'update' or 'delete'
    object_type: str  # 'service', 'policy', 'group'
    object_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_type": self.operation_type,
            "object_type": self.object_type,
            "object_name": self.object_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp,
        }