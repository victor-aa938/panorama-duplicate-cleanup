"""Security Policy Fetcher using PanOS SDK."""

from typing import List, Dict, Optional, Any
from xml.etree.ElementTree import Element
from panos.errors import PanDeviceError

class SecurityPolicyFetcher:
    """Fetch and manage security policies from Panorama device groups and pre-rules."""

    def __init__(self, connection: Optional[Any] = None):
        """
        Initialize the SecurityPolicyFetcher.

        Args:
            connection: Optional PanOSConnection wrapper object. If not provided,
                       dry-run mode with mock data will be used.
        """
        self._connection_wrapper = connection
        self._connection = None
        if connection is not None:
            # Extract the actual Panorama object from the wrapper
            self._connection = connection.get_panorama() if hasattr(connection, 'get_panorama') else connection
        self._cache: Optional[List[Dict]] = None
        self._is_dry_run = connection is None

    def fetch_all(self) -> List[Dict]:
        """
        Fetch all security policies from all sources.

        Sources:
        - Pre-rules: /config/panorama/rules/entry
        - Device groups: /config/panorama/device-groups/{name}/rules/entry

        Returns:
            List of policy dictionaries merged from all sources.
        """
        if self._cache is not None:
            return self._cache.copy()

        policies: List[Dict] = []

        if self._is_dry_run:
            policies = self._get_mock_policies()
        else:
            try:
                # Fetch pre-rules
                pre_rules = self._fetch_pre_rules()
                policies.extend(pre_rules)

                # Fetch device groups and their policies
                device_groups = self._discover_device_groups()
                for group in device_groups:
                    group_policies = self._fetch_device_group_policies(group['name'])
                    policies.extend(group_policies)

            except PanDeviceError as e:
                raise PanDeviceError(f"Failed to fetch security policies: {e}")

        self._cache = policies
        return policies

    def extract_service_refs(self) -> List[Dict]:
        """
        Extract all unique service references from policies.

        Returns:
            List of dictionaries containing service reference information.
        """
        if self._cache is None:
            self.fetch_all()

        service_refs: List[Dict] = []
        seen_services = set()

        for policy in self._cache:
            services = policy.get('services', [])
            if services:
                for service in services:
                    service_name = service.get('member', service) if isinstance(service, dict) else service
                    if service_name and service_name not in seen_services:
                        seen_services.add(service_name)
                        service_refs.append({
                            'name': service_name,
                            'source_policies': [policy.get('name', 'Unknown')]
                        })
                    elif service_name:
                        # Update existing service ref with additional source policy
                        for ref in service_refs:
                            if ref['name'] == service_name:
                                ref['source_policies'].append(policy.get('name', 'Unknown'))
                                break

        return service_refs

    def get_policies_for_service(self, service_name: str) -> List[Dict]:
        """
        Get all policies that reference a specific service.

        Args:
            service_name: Name of the service to search for.

        Returns:
            List of policy dictionaries that reference the service.
        """
        if self._cache is None:
            self.fetch_all()

        matching_policies = []

        for policy in self._cache:
            services = policy.get('services', [])
            for service in services:
                service_ref = service.get('member', service) if isinstance(service, dict) else service
                if service_ref and service_name.lower() in service_ref.lower():
                    matching_policies.append(policy)
                    break

        return matching_policies

    def clear_cache(self):
        """Clear the cached policies."""
        self._cache = None

    def _discover_device_groups(self) -> List[Dict]:
        """
        Discover all device groups from Panorama.

        Returns:
            List of device group dictionaries.
        """
        if self._is_dry_run:
            return self._get_mock_device_groups()

        try:
            from panos.panorama import DeviceGroup
            
            # Refresh device groups from Panorama
            DeviceGroup.refreshall(self._connection)
            
            # Get all device groups
            device_groups = []
            for dg in self._connection.children:
                if isinstance(dg, DeviceGroup):
                    device_groups.append({
                        'name': dg.name
                    })

            return device_groups

        except Exception as e:
            raise PanDeviceError(f"Failed to discover device groups: {e}")

    def _fetch_pre_rules(self) -> List[Dict]:
        """
        Fetch pre-rules from Panorama.

        Returns:
            List of pre-rule policy dictionaries.
        """
        if self._is_dry_run:
            return self._get_mock_pre_rules()

        try:
            from panos.policies import PreRulebase, SecurityRule
            
            # Get pre-rulebase
            pre_rulebase = PreRulebase()
            self._connection.add(pre_rulebase)
            SecurityRule.refreshall(pre_rulebase)
            
            policies = []
            for rule in pre_rulebase.children:
                if isinstance(rule, SecurityRule):
                    policies.append(self._parse_security_rule(rule, 'pre-rule', None))

            return policies

        except Exception as e:
            raise PanDeviceError(f"Failed to fetch pre-rules: {e}")

    def _fetch_device_group_policies(self, group_name: str) -> List[Dict]:
        """
        Fetch security policies from a specific device group.

        Args:
            group_name: Name of the device group.

        Returns:
            List of policy dictionaries for the device group.
        """
        if self._is_dry_run:
            return self._get_mock_device_group_policies(group_name)

        try:
            from panos.panorama import DeviceGroup
            from panos.policies import Rulebase, SecurityRule
            
            # Find the device group
            device_group = self._connection.find(group_name, DeviceGroup)
            if not device_group:
                return []
            
            # Get rulebase for this device group
            rulebase = Rulebase()
            device_group.add(rulebase)
            SecurityRule.refreshall(rulebase)
            
            policies = []
            for rule in rulebase.children:
                if isinstance(rule, SecurityRule):
                    policies.append(self._parse_security_rule(rule, 'security', group_name))

            return policies

        except Exception as e:
            raise PanDeviceError(f"Failed to fetch policies for device group '{group_name}': {e}")

    def _parse_security_rule(self, rule: Any, rule_type: str, device_group: Optional[str]) -> Dict:
        """
        Parse a SecurityRule object into a policy dictionary.

        Args:
            rule: SecurityRule object from PanOS SDK.
            rule_type: Type of rule ('pre-rule' or 'security').
            device_group: Device group name (None for pre-rules).

        Returns:
            Dictionary containing rule/policy information.
        """
        return {
            'name': rule.name,
            'type': rule_type,
            'source_zones': rule.fromzone if isinstance(rule.fromzone, list) else [rule.fromzone] if rule.fromzone else [],
            'destination_zones': rule.tozone if isinstance(rule.tozone, list) else [rule.tozone] if rule.tozone else [],
            'source_addresses': rule.source if isinstance(rule.source, list) else [rule.source] if rule.source else [],
            'destination_addresses': rule.destination if isinstance(rule.destination, list) else [rule.destination] if rule.destination else [],
            'services': rule.service if isinstance(rule.service, list) else [rule.service] if rule.service else [],
            'action': rule.action,
            'description': rule.description or '',
            'device_group': device_group,
            'disabled': rule.disabled if hasattr(rule, 'disabled') else False,
        }
    
    def _parse_rule_element(self, rule_elem, rule_type: str) -> Dict:
        """
        Parse a rule XML element into a policy dictionary.

        Args:
            rule_elem: XML element representing a rule.
            rule_type: Type of rule ('pre-rule' or 'device-group').

        Returns:
            Dictionary containing rule/policy information.
        """
        policy = {
            'name': rule_elem.get('name', 'Unknown'),
            'type': rule_type,
            'status': rule_elem.get('status', 'enabled'),
            'source_zones': [],
            'destination_zones': [],
            'source_addresses': [],
            'destination_addresses': [],
            'services': [],
            'action': rule_elem.find('.//action') is not None,
            'description': '',
            'device_group': None
        }

        # Extract source zones
        src_zones = rule_elem.find('.//from')
        if src_zones is not None:
            policy['source_zones'] = [zone.text for zone in src_zones.findall('entry') if zone.text]

        # Extract destination zones
        dst_zones = rule_elem.find('.//to')
        if dst_zones is not None:
            policy['destination_zones'] = [zone.text for zone in dst_zones.findall('entry') if zone.text]

        # Extract source addresses
        src_addrs = rule_elem.find('.//source')
        if src_addrs is not None:
            policy['source_addresses'] = [addr.text for addr in src_addrs.findall('address') if addr.text]

        # Extract destination addresses
        dst_addrs = rule_elem.find('.//destination')
        if dst_addrs is not None:
            policy['destination_addresses'] = [addr.text for addr in dst_addrs.findall('address') if addr.text]

        # Extract services
        services_elem = rule_elem.find('.//service')
        if services_elem is not None:
            policy['services'] = [svc.text for svc in services_elem.findall('entry') if svc.text]

        # Extract action
        action_elem = rule_elem.find('.//action')
        if action_elem is not None and action_elem.text:
            policy['action'] = action_elem.text

        # Extract description
        desc_elem = rule_elem.find('.//description')
        if desc_elem is not None and desc_elem.text:
            policy['description'] = desc_elem.text

        return policy

    def _get_mock_policies(self) -> List[Dict]:
        """
        Get mock policies for dry-run mode.

        Returns:
            List of mock policy dictionaries.
        """
        return [
            {
                'name': 'mock-pre-rule-1',
                'type': 'pre-rule',
                'status': 'enabled',
                'source_zones': ['untrust'],
                'destination_zones': ['trust'],
                'source_addresses': ['any'],
                'destination_addresses': ['any'],
                'services': ['web-browsing', 'ssl'],
                'action': 'allow',
                'description': 'Mock pre-rule 1',
                'device_group': None
            },
            {
                'name': 'mock-device-group-rule-1',
                'type': 'device-group',
                'status': 'enabled',
                'source_zones': ['trust'],
                'destination_zones': ['dmz'],
                'source_addresses': ['internal-network'],
                'destination_addresses': ['web-server'],
                'services': ['web-browsing', 'ssh'],
                'action': 'allow',
                'description': 'Mock device group rule 1',
                'device_group': 'Default'
            }
        ]

    def _get_mock_device_groups(self) -> List[Dict]:
        """
        Get mock device groups for dry-run mode.

        Returns:
            List of mock device group dictionaries.
        """
        return [
            {'name': 'Default'},
            {'name': 'Engineering'},
            {'name': 'Finance'}
        ]

    def _get_mock_pre_rules(self) -> List[Dict]:
        """
        Get mock pre-rules for dry-run mode.

        Returns:
            List of mock pre-rule dictionaries.
        """
        return [
            {
                'name': 'mock-pre-rule-1',
                'type': 'pre-rule',
                'status': 'enabled',
                'source_zones': ['untrust'],
                'destination_zones': ['trust'],
                'source_addresses': ['any'],
                'destination_addresses': ['any'],
                'services': ['web-browsing', 'ssl'],
                'action': 'allow',
                'description': 'Mock pre-rule 1',
                'device_group': None
            }
        ]

    def _get_mock_device_group_policies(self, group_name: str) -> List[Dict]:
        """
        Get mock device group policies for dry-run mode.

        Args:
            group_name: Name of the device group.

        Returns:
            List of mock policy dictionaries for the device group.
        """
        return [
            {
                'name': f'mock-{group_name.lower()}-rule-1',
                'type': 'device-group',
                'status': 'enabled',
                'source_zones': ['trust'],
                'destination_zones': ['dmz'],
                'source_addresses': ['internal-network'],
                'destination_addresses': ['web-server'],
                'services': ['web-browsing', 'ssh'],
                'action': 'allow',
                'description': f'Mock {group_name} rule 1',
                'device_group': group_name
            }
        ]