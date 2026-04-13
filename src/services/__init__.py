# Duplicate Service Cleanup Tool - Services Package
#
# Expose discovery module
from src.services.discovery import ServiceDiscovery, DiscoveryError

__all__ = [
    "ServiceDiscovery",
    "DiscoveryError",
]