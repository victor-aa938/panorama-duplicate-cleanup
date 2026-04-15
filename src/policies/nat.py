"""NAT Policy Fetcher using PanOS SDK."""

from typing import List, Dict, Optional, Any
from panos.errors import PanDeviceError

class NatPolicyFetcher:
    """Fetch and manage NAT policies from Panorama device groups and pre-rules."""

    def __init__(self, connection: Optional[Any] = None):
        """
        Initialize the NatPolicyFetcher.

        Args:
            connection: Optional PanOSConnection wrapper object. If not provided,
                       dry-run mode with mock data will be used.
        """
        import logging
        self.logger = logging.getLogger(__name__)
        
        self._connection_wrapper = connection
        self._connection = None
        if connection is None:
            raise ValueError("Connection is required for NatPolicyFetcher. Cannot use mock data.")
        
        # Extract the actual Panorama object from the wrapper
        self._connection = connection.get_panorama() if hasattr(connection, 'get_panorama') else connection
        self.logger.info(f"NatPolicyFetcher initialized with connection: {type(self._connection)}")
        self._cache: Optional[List[Dict]] = None

    def fetch_all(self) -> List[Dict]:
        """
        Fetch all NAT policies from all sources.

        Sources:
        - Pre-rules: NAT pre-rules
        - Device groups: Device group NAT policies

        Returns:
            List of NAT policy dictionaries merged from all sources.
        """
        if self._cache is not None:
            return self._cache.copy()

        policies: List[Dict] = []

        try:
            self.logger.info("Fetching real NAT policies from Panorama...")
            
            # Fetch device groups first
            device_groups = self._discover_device_groups()
            self.logger.info(f"Found {len(device_groups)} device groups")
            
            # For each device group, fetch pre-rules, policies, and post-rules
            for group in device_groups:
                # Fetch NAT pre-rules for this device group
                group_pre_rules = self._fetch_device_group_pre_rules(group['name'])
                self.logger.info(f"Fetched {len(group_pre_rules)} NAT pre-rules from device group '{group['name']}'")
                policies.extend(group_pre_rules)
                
                # Fetch regular NAT policies for this device group
                group_policies = self._fetch_device_group_policies(group['name'])
                self.logger.info(f"Fetched {len(group_policies)} NAT policies from device group '{group['name']}'")
                policies.extend(group_policies)
                
                # Fetch NAT post-rules for this device group
                group_post_rules = self._fetch_device_group_post_rules(group['name'])
                self.logger.info(f"Fetched {len(group_post_rules)} NAT post-rules from device group '{group['name']}'")
                policies.extend(group_post_rules)

        except Exception as e:
            self.logger.error(f"Error fetching NAT policies: {e}", exc_info=True)
            raise PanDeviceError(f"Failed to fetch NAT policies: {e}")

        self._cache = policies
        return policies

    def get_policies_for_service(self, service_name: str) -> List[Dict]:
        """
        Get all NAT policies that reference a specific service.

        Args:
            service_name: Name of the service to search for.

        Returns:
            List of NAT policy dictionaries that reference the service.
        """
        if self._cache is None:
            self.fetch_all()

        matching_policies = []

        for policy in self._cache:
            service = policy.get('service')
            if service and service_name.lower() in service.lower():
                matching_policies.append(policy)

        return matching_policies

    def clear_cache(self):
        """Clear the cached NAT policies."""
        self._cache = None

    def _discover_device_groups(self) -> List[Dict]:
        """
        Discover all device groups from Panorama.

        Returns:
            List of device group dictionaries.
        """
        try:
            from panos.panorama import DeviceGroup
            
            self.logger.info("Discovering device groups from Panorama...")
            # Refresh device groups from Panorama
            DeviceGroup.refreshall(self._connection)
            
            # Get all device groups
            device_groups = []
            for dg in self._connection.children:
                if isinstance(dg, DeviceGroup):
                    device_groups.append({
                        'name': dg.name
                    })
                    self.logger.debug(f"Found device group: {dg.name}")

            return device_groups

        except Exception as e:
            self.logger.error(f"Error discovering device groups: {e}", exc_info=True)
            raise PanDeviceError(f"Failed to discover device groups: {e}")

    def _fetch_device_group_pre_rules(self, group_name: str) -> List[Dict]:
        """
        Fetch NAT pre-rules from a specific device group.

        Args:
            group_name: Name of the device group.

        Returns:
            List of NAT pre-rule policy dictionaries for the device group.
        """
        try:
            from panos.panorama import DeviceGroup
            from panos.policies import PreRulebase, NatRule
            
            self.logger.info(f"Fetching NAT pre-rules for device group '{group_name}'...")
            # Find the device group
            device_group = self._connection.find(group_name, DeviceGroup)
            if not device_group:
                self.logger.warning(f"Device group '{group_name}' not found")
                return []
            
            # Get pre-rulebase for this device group
            pre_rulebase = PreRulebase()
            device_group.add(pre_rulebase)
            NatRule.refreshall(pre_rulebase)
            
            policies = []
            for rule in pre_rulebase.children:
                if isinstance(rule, NatRule):
                    policies.append(self._parse_nat_rule(rule, 'nat-pre-rule', group_name))
                    self.logger.debug(f"Found NAT pre-rule: {rule.name} in device group '{group_name}'")

            return policies

        except Exception as e:
            self.logger.error(f"Error fetching NAT pre-rules for device group '{group_name}': {e}", exc_info=True)
            raise PanDeviceError(f"Failed to fetch NAT pre-rules for device group '{group_name}': {e}")

    def _fetch_device_group_post_rules(self, group_name: str) -> List[Dict]:
        """
        Fetch NAT post-rules from a specific device group.

        Args:
            group_name: Name of the device group.

        Returns:
            List of NAT post-rule policy dictionaries for the device group.
        """
        try:
            from panos.panorama import DeviceGroup
            from panos.policies import PostRulebase, NatRule
            
            self.logger.info(f"Fetching NAT post-rules for device group '{group_name}'...")
            # Find the device group
            device_group = self._connection.find(group_name, DeviceGroup)
            if not device_group:
                self.logger.warning(f"Device group '{group_name}' not found")
                return []
            
            # Get post-rulebase for this device group
            post_rulebase = PostRulebase()
            device_group.add(post_rulebase)
            NatRule.refreshall(post_rulebase)
            
            policies = []
            for rule in post_rulebase.children:
                if isinstance(rule, NatRule):
                    policies.append(self._parse_nat_rule(rule, 'nat-post-rule', group_name))
                    self.logger.debug(f"Found NAT post-rule: {rule.name} in device group '{group_name}'")

            return policies

        except Exception as e:
            self.logger.error(f"Error fetching NAT post-rules for device group '{group_name}': {e}", exc_info=True)
            raise PanDeviceError(f"Failed to fetch NAT post-rules for device group '{group_name}': {e}")

    def _fetch_device_group_policies(self, group_name: str) -> List[Dict]:
        """
        Fetch NAT policies from a specific device group.

        Args:
            group_name: Name of the device group.

        Returns:
            List of NAT policy dictionaries for the device group.
        """
        try:
            from panos.panorama import DeviceGroup
            from panos.policies import Rulebase, NatRule
            
            self.logger.info(f"Fetching NAT policies for device group '{group_name}'...")
            # Find the device group
            device_group = self._connection.find(group_name, DeviceGroup)
            if not device_group:
                self.logger.warning(f"Device group '{group_name}' not found")
                return []
            
            # Get rulebase for this device group
            rulebase = Rulebase()
            device_group.add(rulebase)
            NatRule.refreshall(rulebase)
            
            policies = []
            for rule in rulebase.children:
                if isinstance(rule, NatRule):
                    policies.append(self._parse_nat_rule(rule, 'nat', group_name))
                    self.logger.debug(f"Found NAT policy: {rule.name} in device group '{group_name}'")

            return policies

        except Exception as e:
            self.logger.error(f"Error fetching NAT policies for device group '{group_name}': {e}", exc_info=True)
            raise PanDeviceError(f"Failed to fetch NAT policies for device group '{group_name}': {e}")

    def _parse_nat_rule(self, rule: Any, rule_type: str, device_group: Optional[str]) -> Dict:
        """
        Parse a NatRule object into a policy dictionary.

        Args:
            rule: NatRule object from PanOS SDK.
            rule_type: Type of rule ('nat-pre-rule' or 'nat').
            device_group: Device group name (None for pre-rules).

        Returns:
            Dictionary containing NAT rule/policy information.
        """
        # Location is always the device group name (pre-rules and post-rules are per-DG)
        location = device_group if device_group else 'shared'
        
        return {
            'name': rule.name,
            'type': rule_type,
            'source_zones': rule.fromzone if isinstance(rule.fromzone, list) else [rule.fromzone] if rule.fromzone else [],
            'destination_zones': rule.tozone if isinstance(rule.tozone, list) else [rule.tozone] if rule.tozone else [],
            'source_addresses': rule.source if isinstance(rule.source, list) else [rule.source] if rule.source else [],
            'destination_addresses': rule.destination if isinstance(rule.destination, list) else [rule.destination] if rule.destination else [],
            'service': rule.service or 'any',
            'description': rule.description or '',
            'device_group': device_group,
            'location': location,
            'disabled': rule.disabled if hasattr(rule, 'disabled') else False,
            'nat_type': rule.nat_type if hasattr(rule, 'nat_type') else 'unknown',
        }
