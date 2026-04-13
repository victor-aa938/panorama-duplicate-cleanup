"""
Service discovery module for duplicate service cleanup tool.

Provides methods to fetch and filter services from Panorama using pan-os-python SDK.
"""
import logging
import time
from typing import List, Dict, Optional, cast, Any
from collections import defaultdict

# Import panos lazily to allow testing without the library
try:
    from panos.panorama import Panorama
    from panos.objects import ServiceObject
    from panos.errors import PanDeviceError, PanURLError
    _PANOS_AVAILABLE = True
except ImportError:
    Panorama = None
    ServiceObject = None
    PanDeviceError = Exception
    PanURLError = Exception
    _PANOS_AVAILABLE = False

from src.utils.connection import PanOSConnection
from src.models.service import Service

logger = logging.getLogger(__name__)

# Pagination settings
DEFAULT_PAGE_SIZE = 1000
MAX_PAGES = 100  # Safety limit for pagination
MAX_RETRIES = 3
BASE_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 30.0  # seconds


class DiscoveryError(Exception):
    """Exception raised for service discovery errors."""

    def __init__(self, message: str, *args: object):
        super().__init__(message, *args)
        self.message = message


class ServiceDiscovery:
    """Discovers and fetches services from Panorama."""

    def __init__(self, connection: PanOSConnection):
        """
        Initialize service discovery.

        Args:
            connection: PanOSConnection instance for Panorama access
        """
        self.connection = connection
        self._panorama: Optional[Panorama] = None

    def _get_panorama(self) -> Panorama:
        """
        Get Panorama instance with connection check.

        Returns:
            Panorama instance
        """
        if self._panorama is None:
            if not self.connection.is_connected:
                self.connection.connect()
            self._panorama = self.connection.get_panorama()
        return self._panorama

    def _retry_request(self, func, *args, **kwargs):
        """
        Execute a request with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result from the function

        Raises:
            DiscoveryError: If all retries fail
        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except (PanDeviceError, PanURLError) as e:
                logger.warning(
                    f"Request attempt {attempt} failed: {str(e)}"
                )

                if attempt < MAX_RETRIES:
                    delay = min(
                        BASE_RETRY_DELAY * (2 ** (attempt - 1)),
                        MAX_RETRY_DELAY,
                    )
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise DiscoveryError(
                        f"Failed to execute request after {MAX_RETRIES} attempts: {str(e)}"
                    ) from e
            except Exception as e:
                raise DiscoveryError(f"Unexpected error during request: {str(e)}") from e

        raise DiscoveryError(
            f"Failed to execute request after {MAX_RETRIES} attempts"
        )

    def fetch_all(self, page_size: int = DEFAULT_PAGE_SIZE) -> List[Service]:
        """
        Fetch all services from Panorama.

        Args:
            page_size: Number of services to fetch per page (unused for Panorama)

        Returns:
            List of Service objects

        Raises:
            DiscoveryError: If fetching services fails
        """
        services: List[Service] = []

        try:
            panorama = self._get_panorama()

            # Use panos object model to fetch shared services
            if not _PANOS_AVAILABLE:
                logger.error("panos library not available")
                return []

            # Use ServiceObject.refreshall to get all shared services from Panorama
            panos_services = ServiceObject.refreshall(panorama, add=True)

            for service_obj in panos_services:
                service = self._parse_service_object(service_obj, device_group="shared")
                if service:
                    services.append(service)

            # Also fetch from each device group
            from panos.panorama import DeviceGroup
            try:
                device_groups = DeviceGroup.refreshall(panorama, add=True)
                for dg in device_groups:
                    dg_services = ServiceObject.refreshall(dg, add=True)
                    for service_obj in dg_services:
                        service = self._parse_service_object(service_obj, device_group=dg.name)
                        if service:
                            services.append(service)
            except Exception as e:
                logger.warning(f"Could not fetch device group services: {e}")

            if not services:
                logger.info("No services found")
                return []

            logger.info(f"Total services fetched: {len(services)}")
            return services

        except Exception as e:
            logger.error(f"Failed to fetch all services: {e}")
            raise DiscoveryError(f"Failed to fetch services: {str(e)}") from e

    def _parse_service_object(self, service_obj: ServiceObject, device_group: str = None) -> Optional[Service]:
        """
        Parse a ServiceObject into a Service model.

        Args:
            service_obj: ServiceObject instance from panos
            device_group: Device group name (or "shared")

        Returns:
            Service model or None if parsing fails
        """
        try:
            return Service(
                name=service_obj.name,
                protocol=service_obj.protocol,
                port=service_obj.destination_port,
                description=service_obj.description or "",
                tag=service_obj.tag if hasattr(service_obj, 'tag') else [],
                device_group=device_group
            )
        except Exception as e:
            logger.error(f"Error parsing ServiceObject: {e}")
            return None

    def fetch_by_protocol(self, protocol: str, port: Optional[str] = None) -> List[Service]:
        """
        Fetch services filtered by protocol and optionally by port.

        Args:
            protocol: Protocol to filter by (tcp, udp, etc.)
            port: Optional port to filter by (e.g., '443')

        Returns:
            List of Service objects matching the criteria

        Raises:
            DiscoveryError: If fetching fails
        """
        all_services = self.fetch_all()

        # Filter by protocol
        filtered = [s for s in all_services if s.protocol.lower() == protocol.lower()]

        # Filter by port if specified
        if port:
            filtered = [s for s in filtered if s.port == port]

        logger.info(f"Found {len(filtered)} services for {protocol}" +
                   (f":{port}" if port else ""))

        return filtered

    def fetch_duplicates(self) -> Dict[str, List[Service]]:
        """
        Get services grouped by port+protocol for duplicate detection.

        Returns:
            Dictionary mapping "protocol:port" keys to lists of services

        Raises:
            DiscoveryError: If fetching fails
        """
        all_services = self.fetch_all()

        # Group services by protocol and port
        duplicates: Dict[str, List[Service]] = defaultdict(list)

        for service in all_services:
            key = f"{service.protocol}:{service.port}"
            duplicates[key].append(service)

        # Filter to only groups with duplicates (more than one service)
        result = {k: v for k, v in duplicates.items() if len(v) > 1}

        total_groups = len(result)
        total_dupes = sum(len(v) for v in result.values())

        logger.info(f"Found {total_groups} duplicate groups with {total_dupes} total services")

        return result

    def get_service_count(self) -> int:
        """
        Get total count of services in Panorama.

        Returns:
            Total number of services

        Raises:
            DiscoveryError: If fetching fails
        """
        try:
            all_services = self.fetch_all()
            return len(all_services)
        except Exception as e:
            logger.error(f"Failed to get service count: {e}")
            raise DiscoveryError(f"Failed to get service count: {str(e)}") from e

    def get_protocols(self) -> List[str]:
        """
        Get list of unique protocols in use.

        Returns:
            List of protocol names (tcp, udp, etc.)

        Raises:
            DiscoveryError: If fetching fails
        """
        all_services = self.fetch_all()
        protocols = list(set(s.protocol for s in all_services))
        return sorted(protocols)

    def get_ports_by_protocol(self, protocol: str) -> List[str]:
        """
        Get list of ports used by a specific protocol.

        Args:
            protocol: Protocol to filter by

        Returns:
            List of port strings

        Raises:
            DiscoveryError: If fetching fails
        """
        all_services = self.fetch_all()
        protocol_lower = protocol.lower()
        ports = list(set(
            s.port for s in all_services
            if s.protocol.lower() == protocol_lower
        ))
        return sorted(ports)