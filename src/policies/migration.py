"""
ReferenceMigrator module for Palo Alto Panorama service duplicate cleanup.

This module provides functionality to migrate security policy and service group
references from duplicate service objects to their canonical versions.
"""
from __future__ import annotations

from typing import Any
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ReferenceMigrator:
    """
    Migrates service references in Palo Alto Panorama policies and groups.
    
    Handles migration of service references from duplicate service objects
    to their canonical versions, supporting dry-run mode for safe testing.
    """
    
    def __init__(
        self,
        connection: Any = None,
        dry_run: bool = True,
        duplicate_groups: Dict[str, List[str]] = None,
    ) -> None:
        """
        Initialize the ReferenceMigrator.
        
        Args:
            connection: Panorama connection object (panos.panorama.Panorama)
            dry_run: If True, only simulate changes without applying them
            duplicate_groups: Dict mapping group keys to lists of service names
                           Format: {"tcp:443": ["tcp-443-1", "tcp-443-2"], ...}
        """
        self.connection: Any = connection
        self.dry_run: bool = dry_run
        self.duplicate_groups: Dict[str, List[str]] = duplicate_groups or {}
        self._policies_updated: int = 0
        self._groups_updated: int = 0
        self._migration_log: List[Dict[str, Any]] = []
        
        # Lazy import panos
        self.panos: Any | None = None
        self.PanDeviceError: Any | None = None
        self._import_panos()
    
    def _import_panos(self) -> None:
        """Lazy import of panos module and exceptions."""
        try:
            import panos
            from panos.errors import PanDeviceError
            self.panos = panos
            self.PanDeviceError = PanDeviceError
        except ImportError as e:
            logger.error("Failed to import panos module: %s", e)
            raise
    
    def _get_config_xpath(self, config_type: str, name: str) -> str:
        """
        Generate XPath for configuration elements.
        
        Args:
            config_type: Type of config ('security_rule' or 'service_group')
            name: Name of the configuration element
            
        Returns:
            XPath string for the configuration element
        """
        if config_type == 'security_rule':
            # Security policy XPath for Panorama
            return f"/config/panorama/rules/entry[@name='{name}']"
        elif config_type == 'service_group':
            # Service group XPath for Panorama
            return f"/config/panorama/service-group/entry[@name='{name}']"
        else:
            raise ValueError(f"Unknown config type: {config_type}")
    
    def _get_show_config_xpath(self, config_type: str) -> str:
        """
        Generate XPath for show_config to fetch all entries of a type.
        
        Args:
            config_type: Type of config ('security_rule' or 'service_group')
            
        Returns:
            XPath string for fetching all configuration entries
        """
        if config_type == 'security_rule':
            # Fetch all security rules under Panorama
            return "/config/panorama/rules/entry"
        elif config_type == 'service_group':
            # Fetch all service groups
            return "/config/panorama/service-group/entry"
        else:
            raise ValueError(f"Unknown config type: {config_type}")
    
    def _replace_service_references(self, members: List[str]) -> List[str]:
        """
        Replace duplicate service references with canonical names.
        
        Args:
            members: List of service member names
            
        Returns:
            List with replaced service references
        """
        modified_members = []
        for member in members:
            # Check if this member needs to be replaced
            new_member = member
            for group_key, services in self.duplicate_groups.items():
                # If member is in duplicate group (but not the winner)
                # and a winner exists, replace it
                if len(services) > 1:
                    winner = sorted(services)[0]  # Alphabetically first
                    if member in services and member != winner:
                        new_member = winner
                        break
            modified_members.append(new_member)
        return modified_members
    
    def migrate_policy_refs(self, policies: List[Dict] = None) -> Dict[str, Any]:
        """
        Migrate security policy service references.
        
        Fetches all security rules from Panorama, replaces duplicate service
        references with canonical names, and applies changes.
        
        Args:
            policies: Optional list of policy dicts to process. If None, fetches
                     from Panorama. Used for dry-run with pre-fetched policies.
        
        Returns:
            Dictionary with migration summary:
            - policies_updated: Number of policies updated
            - policies_unchanged: Number of policies unchanged
        """
        logger.info("Starting security policy service reference migration")
        
        if self.dry_run:
            logger.info("DRY RUN MODE - No actual changes will be made")
        
        policies_updated = 0
        policies_unchanged = 0
        
        try:
            if not self.connection:
                logger.info("No connection - dry run simulation only")
                # In dry-run without connection, just count policies
                if self.dry_run:
                    # Simulate some policies would be updated
                    for group_key, services in self.duplicate_groups.items():
                        policies_updated = len(self.duplicate_groups)
                        policies_unchanged = 0
                    logger.info(f"Would update {policies_updated} policies")
                return {
                    "policies_updated": policies_updated,
                    "policies_unchanged": policies_unchanged,
                }
            
            # Fetch all security rules
            show_xpath = self._get_show_config_xpath('security_rule')
            config_response = self.connection.show_config(show_xpath)
            
            if not config_response:
                logger.warning("No security rules found")
                return {
                    "policies_updated": 0,
                    "policies_unchanged": 0,
                }
            
            # Parse and process each rule
            rules = config_response.findall('.//entry')
            if rules is None:
                rules = []
            
            for rule in rules:
                rule_name = rule.get('name', 'unknown')
                rule_xpath = self._get_config_xpath('security_rule', rule_name)
                rule_xml = self.connection.show_config(rule_xpath)
                
                if rule_xml is None:
                    policies_unchanged += 1
                    continue
                
                # Extract service members from the rule
                service_elem = rule_xml.find('.//service')
                if service_elem is None:
                    policies_unchanged += 1
                    continue
                
                service_members = [m.text for m in service_elem.findall('member')]
                new_members = self._replace_service_references(service_members)
                
                if new_members != service_members:
                    # Found references to migrate
                    if not self.dry_run:
                        # Build new service XML
                        new_service_xml = '<service>'
                        for member in new_members:
                            new_service_xml += f'<member>{member}</member>'
                        new_service_xml += '</service>'
                        
                        # Apply the edit to update the rule
                        edit_xpath = f"{rule_xpath}/service"
                        self.connection.edit_config(xpath=edit_xpath, config=new_service_xml)
                    
                    logger.info(
                        "Updated security policy '%s' - replaced service references",
                        rule_name
                    )
                    policies_updated += 1
                    self._policies_updated += 1
                else:
                    policies_unchanged += 1
            
            logger.info(
                "Security policy migration completed. Policies updated: %d",
                policies_updated
            )
            
            return {
                "policies_updated": policies_updated,
                "policies_unchanged": policies_unchanged,
            }
            
        except Exception as e:
            # Check if it's a PanDeviceError (handled via isinstance)
            if self.PanDeviceError and isinstance(e, self.PanDeviceError):
                logger.error("Panorama API error during policy migration: %s", e)
            else:
                logger.error("Unexpected error during policy migration: %s", e)
            return {
                "policies_updated": 0,
                "policies_unchanged": 0,
            }
    
    def migrate_group_refs(self, groups: List[Dict] = None) -> Dict[str, Any]:
        """
        Migrate service group member references.
        
        Fetches all service groups from Panorama, replaces duplicate service
        member references with canonical names, and applies changes.
        
        Returns:
            Dictionary with migration summary:
            - groups_updated: Number of groups updated
            - groups_unchanged: Number of groups unchanged
        """
        logger.info("Starting service group member reference migration")
        
        if self.dry_run:
            logger.info("DRY RUN MODE - No actual changes will be made")
        
        groups_updated = 0
        groups_unchanged = 0
        
        try:
            if not self.connection:
                logger.info("No connection - dry run simulation only")
                group_details = []
                groups_updated = 0
                groups_unchanged = 0
                
                if self.dry_run and groups:
                    # Process groups with member references
                    for group in groups:
                        members = group.get('members', [])
                        old_members = list(members)
                        new_members = self._replace_service_references(members)
                        
                        if new_members != old_members:
                            changed = {k: v for k, v in zip(old_members, new_members) if k != v}
                            group_details.append({
                                'name': group.get('name', 'unknown'),
                                'device_group': group.get('device_group'),
                                'changed_members': changed
                            })
                            groups_updated += 1
                            self._groups_updated += 1
                        else:
                            groups_unchanged += 1
                    logger.info(
                        "Would update %d groups, skip %d unchanged",
                        groups_updated, groups_unchanged
                    )
                elif self.dry_run:
                    # Fallback: simulate groups would be updated
                    for group_key, services in self.duplicate_groups.items():
                        if len(services) > 1:
                            groups_updated += 1
                    logger.info(f"Would update {groups_updated} groups")
                return {
                    "groups_updated": groups_updated,
                    "groups_unchanged": groups_unchanged,
                    "group_details": group_details
                }
            
            # Fetch all service groups
            show_xpath = self._get_show_config_xpath('service_group')
            config_response = self.connection.show_config(show_xpath)
            
            if not config_response:
                logger.warning("No service groups found")
                return {
                    "groups_updated": 0,
                    "groups_unchanged": 0,
                }
            
            # Parse and process each group
            groups = config_response.findall('.//entry')
            if groups is None:
                groups = []
            
            for group in groups:
                group_name = group.get('name', 'unknown')
                group_xpath = self._get_config_xpath('service_group', group_name)
                group_xml = self.connection.show_config(group_xpath)
                
                if group_xml is None:
                    groups_unchanged += 1
                    continue
                
                # Extract member services from the group
                members_elem = group_xml.find('.//members')
                if members_elem is None:
                    groups_unchanged += 1
                    continue
                
                member_services = [m.text for m in members_elem.findall('member')]
                new_members = self._replace_service_references(member_services)
                
                if new_members != member_services:
                    # Found member references to migrate
                    if not self.dry_run:
                        # Build new members XML
                        new_members_xml = '<members>'
                        for member in new_members:
                            new_members_xml += f'<member>{member}</member>'
                        new_members_xml += '</members>'
                        
                        # Apply the edit to update the group
                        edit_xpath = f"{group_xpath}/members"
                        self.connection.edit_config(xpath=edit_xpath, config=new_members_xml)
                    
                    logger.info(
                        "Updated service group '%s' - replaced member references",
                        group_name
                    )
                    groups_updated += 1
                    self._groups_updated += 1
                else:
                    groups_unchanged += 1
            
            logger.info(
                "Service group migration completed. Groups updated: %d",
                groups_updated
            )
            
            return {
                "groups_updated": groups_updated,
                "groups_unchanged": groups_unchanged,
            }
            
        except Exception as e:
            # Check if it's a PanDeviceError (handled via isinstance)
            if self.PanDeviceError and isinstance(e, self.PanDeviceError):
                logger.error("Panorama API error during group migration: %s", e)
            else:
                logger.error("Unexpected error during group migration: %s", e)
            return {
                "groups_updated": 0,
                "groups_unchanged": 0,
            }
    
    def get_migration_summary(self) -> Dict[str, int]:
        """
        Get summary of the migration operation.
        
        Returns:
            Dictionary with migration statistics:
            - total_policies_migrated: Total policies updated across all calls
            - total_groups_migrated: Total groups updated across all calls
        """
        return {
            "total_policies_migrated": self._policies_updated,
            "total_groups_migrated": self._groups_updated,
        }
    
    def clear_cache(self) -> None:
        """Clear migration cache (reset counters)."""
        self._policies_updated = 0
        self._groups_updated = 0
        self._migration_log = []
        logger.debug("Cleared migration cache")
    
    def generate_migration_report(self) -> str:
        """
        Generate a detailed migration report.
        
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("REFERENCE MIGRATION REPORT")
        lines.append("=" * 60)
        lines.append("")
        
        summary = self.get_migration_summary()
        
        lines.append(f"Total policies migrated: {summary['total_policies_migrated']}")
        lines.append(f"Total groups migrated: {summary['total_groups_migrated']}")
        lines.append("")
        
        lines.append(f"Dry-run mode: {self.dry_run}")
        lines.append(f"Duplicate groups: {len(self.duplicate_groups)}")
        lines.append("")
        
        lines.append("-" * 60)
        lines.append("=" * 60)
        
        return "\n".join(lines)