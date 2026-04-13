"""
ServiceGroupFetcher class to fetch service groups from all device groups and global groups.
"""
from src.models.service import ServiceGroup
from typing import List, Dict, Optional


class ServiceGroupFetcher:
    """
    Fetch service groups from all device groups and global groups.
    
    Requirements:
    1. Fetch service groups from ALL device groups AND global groups
    2. First discover device groups: /config/panorama/device-groups/entry
    3. For each device group, fetch service groups: /config/panorama/device-groups/{name}/service-group/entry
    4. Also fetch global service groups: /config/panorama/service-group/entry
    5. Return merged list of all service groups
    6. Use PanOS SDK (panos-python)
    7. Handle dry-run mode (mock data when no connection)
    8. Include proper error handling with PanDeviceError
    """
    
    def __init__(self, connection: object = None):
        """
        Initialize the ServiceGroupFetcher.
        
        Args:
            connection: PanOS connection object (optional)
        """
        self.connection = connection
        self.device_groups: List[str] = []
        self.service_groups: List[ServiceGroup] = []
        self._cached_groups: List[ServiceGroup] = []
        
    def fetch_all(self) -> List[ServiceGroup]:
        """
        Fetch all service groups from all sources.
        
        Returns:
            List of ServiceGroup objects
        """
        # If connection is not provided, use dry-run mode
        if self.connection is None:
            return self._mock_data()
        
        try:
            # Step 1: Discover device groups
            self.device_groups = self._discover_device_groups()
            
            # Step 2: Fetch service groups from device groups
            device_group_groups = self._fetch_device_group_service_groups()
            
            # Step 3: Fetch global service groups
            global_groups = self._fetch_global_service_groups()
            
            # Merge all groups
            self.service_groups = self._merge_groups(device_group_groups, global_groups)
            
            return self.service_groups
        except Exception as e:
            # Handle other unexpected errors
            raise RuntimeError(f"Error fetching service groups: {str(e)}") from e
    
    def _discover_device_groups(self) -> List[str]:
        """
        Discover device groups from Panorama.
        
        Returns:
            List of device group names
        """
        if self.connection is None:
            return []
        
        try:
            from panos.panorama import Panorama
            panorama = self.connection.get_panorama()
            # Fetch device groups using correct API
            result = panorama.op('<show><device-group><list></list></device-group></show>')
            
            # Extract device group names from XML
            device_group_names = []
            for entry in result.findall('.//entry'):
                name = entry.get('name')
                if name:
                    device_group_names.append(name)
            
            return device_group_names
        except Exception as e:
            raise RuntimeError(f"Error discovering device groups: {str(e)}") from e
    
    def _fetch_device_group_service_groups(self) -> List[ServiceGroup]:
        """
        Fetch service groups from each device group.
        
        Returns:
            List of ServiceGroup objects
        """
        if self.connection is None:
            return []
        
        device_group_groups = []
        
        for group_name in self.device_groups:
            try:
                from panos.panorama import Panorama
                panorama = self.connection.get_panorama()
                
                # Fetch service groups for this device group
                xpath = f"/config/panorama/device-groups/entry[@name='{group_name}']/service-group/entry"
                result = panorama.show_config(xpath=xpath)
                
                # Extract service groups
                for entry in result.findall('.//entry'):
                    name = entry.get('name')
                    if name:
                        # Extract members
                        members = [m.text for m in entry.findall('.//members/member')]
                        # Extract description
                        desc_elem = entry.find('.//description')
                        description = desc_elem.text if desc_elem is not None else None
                        # Extract tags
                        tag_elements = entry.findall('.//tag/member')
                        tags = [t.text for t in tag_elements] if tag_elements else []
                        
                        group = ServiceGroup(
                            name=name,
                            members=members,
                            description=description,
                            tag=tags
                        )
                        device_group_groups.append(group)
                        
            except Exception as e:
                raise RuntimeError(f"Error fetching service groups from device group {group_name}: {str(e)}") from e
        
        return device_group_groups
    
    def _fetch_global_service_groups(self) -> List[ServiceGroup]:
        """
        Fetch global service groups from Panorama.
        
        Returns:
            List of ServiceGroup objects
        """
        if self.connection is None:
            return []
        
        try:
            from panos.panorama import Panorama
            panorama = self.connection.get_panorama()
            # Fetch global service groups
            xpath = "/config/panorama/service-group/entry"
            result = panorama.show_config(xpath=xpath)
            
            # Extract service groups
            global_groups = []
            for entry in result.findall('.//entry'):
                name = entry.get('name')
                if name:
                    # Extract members
                    members = [m.text for m in entry.findall('.//members/member')]
                    # Extract description
                    desc_elem = entry.find('.//description')
                    description = desc_elem.text if desc_elem is not None else None
                    # Extract tags
                    tag_elements = entry.findall('.//tag/member')
                    tags = [t.text for t in tag_elements] if tag_elements else []
                    
                    group = ServiceGroup(
                        name=name,
                        members=members,
                        description=description,
                        tag=tags
                    )
                    global_groups.append(group)
                    
        except Exception as e:
            raise RuntimeError(f"Error fetching global service groups: {str(e)}") from e
        
        return global_groups
    
    def _merge_groups(self, device_groups: List[ServiceGroup], global_groups: List[ServiceGroup]) -> List[ServiceGroup]:
        """
        Merge device group service groups with global service groups.
        
        Args:
            device_groups: Service groups from device groups
            global_groups: Service groups from global groups
        
        Returns:
            Merged list of service groups
        """
        # Combine both lists
        all_groups = device_groups + global_groups
        
        # Remove duplicates (keep first occurrence)
        seen_names = set()
        unique_groups = []
        for group in all_groups:
            if group.name not in seen_names:
                seen_names.add(group.name)
                unique_groups.append(group)
        
        return unique_groups
    
    def extract_members(self) -> List[Dict]:
        """
        Extract member references from all service groups.
        
        Returns:
            List of member references as dictionaries
        """
        members = []
        
        for group in self.service_groups:
            for member in group.members:
                members.append({
                    'group_name': group.name,
                    'member': member
                })
        
        return members
    
    def get_groups_for_service(self, service_name: str) -> List[ServiceGroup]:
        """
        Get service groups that contain the specified service.
        
        Args:
            service_name: Name of the service to search for
        
        Returns:
            List of ServiceGroup objects that contain the service
        """
        return [group for group in self.service_groups if service_name in group.members]
    
    def clear_cache(self) -> None:
        """
        Clear the cached service groups.
        """
        self.service_groups = []
        self.device_groups = []
        self._cached_groups = []
    
    def _mock_data(self) -> List[ServiceGroup]:
        """
        Get mock service groups for dry-run mode.
        
        Returns:
            List of mock ServiceGroup objects
        """
        return [
            ServiceGroup(
                name="https-servers",
                members=["tcp-443", "tcp-8443"],
                description="HTTPS server access",
                tag=["web"]
            ),
            ServiceGroup(
                name="web-services",
                members=["tcp-80", "tcp-443"],
                description="Web traffic services",
                tag=["web"]
            ),
        ]