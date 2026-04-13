"""
Mock PanOS SDK fixtures for testing.

Provides comprehensive mock objects to simulate PanOS SDK behavior without
actually connecting to a Panorama device.
"""
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any
import xml.etree.ElementTree as ET


class MockPanOSConnection:
    """Mock connection class that simulates PanOS SDK connection."""

    def __init__(self, ip: str = "1.2.3.4", username: str = "admin"):
        self.ip = ip
        self.username = username
        self._connected = True

    @property
    def is_connected(self):
        """Return connection status."""
        return self._connected

    @is_connected.setter
    def is_connected(self, value):
        """Set connection status."""
        self._connected = value

    def get_panorama(self):
        """Get the Panorama instance (for panos SDK)."""
        return self

    def __enter__(self):
        self._connected = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._connected = False

    def op(self, cmd: str, is_xml: bool = False, **kwargs) -> str:
        """Execute operational command (panos SDK compatibility)."""
        return self.execute_op(cmd)

    def execute_op(self, cmd: str, vsys: str = "vsys1") -> str:
        """Execute operational command and return XML response."""
        if "services" in cmd.lower():
            return self._mock_xml_services()
        elif "security" in cmd.lower() and "rules" in cmd.lower():
            return self._mock_xml_security()
        elif "service-group" in cmd.lower() or "service_group" in cmd.lower():
            return self._mock_xml_service_groups()
        elif "xpath" in cmd.lower():
            if "security" in cmd:
                return self._mock_xml_security()
            elif "service-group" in cmd or "service_group" in cmd:
                return self._mock_xml_service_groups()
            elif "service" in cmd:
                return self._mock_xml_services()
        return self._mock_xml_empty()

    def _mock_xml_services(self) -> str:
        """Return mock services XML."""
        root = ET.Element("response", {"status": "success"})
        result = ET.SubElement(root, "result")
        services = ET.SubElement(result, "result")

        for name, protocol, port in [
            ("tcp-443-1", "tcp", "443"),
            ("tcp-443-2", "tcp", "443"),
            ("tcp-80-1", "tcp", "80"),
            ("tcp-22-1", "tcp", "22"),
        ]:
            entry = ET.SubElement(services, "entry", {"name": name})
            protocol_elem = ET.SubElement(entry, "protocol")
            protocol_name = ET.SubElement(protocol_elem, protocol)
            port_elem = ET.SubElement(protocol_name, "port")
            port_elem.text = port

        return ET.tostring(root, encoding="unicode")

    def _mock_xml_security(self) -> str:
        """Return mock security rules XML."""
        root = ET.Element("response", {"status": "success"})
        result = ET.SubElement(root, "result")
        rules = ET.SubElement(result, "result")

        for name, svcs, src, dst in [
            ("allow-https-1", ["tcp-443-1", "tcp-80-1"], "any", "internal"),
            ("allow-https-2", ["tcp-443-2"], "external", "web-servers"),
            ("allow-web", ["tcp-80-1"], "any", "web-servers"),
        ]:
            entry = ET.SubElement(rules, "entry", {"name": name})
            service = ET.SubElement(entry, "service")
            for svc in svcs:
                member = ET.SubElement(service, "member")
                member.text = svc

            src_elem = ET.SubElement(entry, "source")
            for s in src:
                member = ET.SubElement(src_elem, "member")
                member.text = s

            dst_elem = ET.SubElement(entry, "destination")
            for d in dst:
                member = ET.SubElement(dst_elem, "member")
                member.text = d

            action = ET.SubElement(entry, "action")
            action.text = "allow"

        return ET.tostring(root, encoding="unicode")

    def _mock_xml_service_groups(self) -> str:
        """Return mock service groups XML."""
        root = ET.Element("response", {"status": "success"})
        result = ET.SubElement(root, "result")
        groups = ET.SubElement(result, "result")

        for name, members in [
            ("https-servers", ["tcp-443-1", "tcp-443-2"]),
            ("web-services", ["tcp-80-1"]),
            ("internal-services", ["tcp-22-1"]),
        ]:
            entry = ET.SubElement(groups, "entry", {"name": name})
            members_elem = ET.SubElement(entry, "members")
            for member in members:
                member_elem = ET.SubElement(members_elem, "member")
                member_elem.text = member

        return ET.tostring(root, encoding="unicode")

    def _mock_xml_empty(self) -> str:
        """Return empty XML response."""
        root = ET.Element("response", {"status": "success"})
        result = ET.SubElement(root, "result")
        return ET.tostring(root, encoding="unicode")


def create_mock_connection() -> MockPanOSConnection:
    """Create and return a mock connection instance."""
    return MockPanOSConnection()


def patch_panosa_connection():
    """Decorator to patch PanOS connection for tests."""
    return patch("src.utils.connection.PanOSConnection", MockPanOSConnection)


def mock_service(name: str, protocol: str = "tcp", port: str = "443") -> Any:
    """Create a mock service object."""
    svc = MagicMock()
    svc.name = name
    svc.protocol = protocol
    svc.port = port
    svc.description = f"Mock service {name}"
    svc.tag = []
    svc.members = []
    return svc


def mock_security_rule(
    name: str,
    services: List[str],
    source: List[str] = None,
    dest: List[str] = None,
) -> Any:
    """Create a mock security rule object."""
    rule = MagicMock()
    rule.name = name
    rule.service = services
    rule.source = source or ["any"]
    rule.destination = dest or ["any"]
    rule.action = "allow"
    rule.enabled = True
    return rule


def mock_service_group(
    name: str,
    members: List[str],
) -> Any:
    """Create a mock service group object."""
    group = MagicMock()
    group.name = name
    group.members = members
    group.description = f"Mock group {name}"
    group.tag = []
    return group
