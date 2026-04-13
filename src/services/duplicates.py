"""
Duplicate detection logic for duplicate service cleanup tool.

Provides logic to identify, group, and report on duplicate services
based on protocol and port combinations.
"""

import logging
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

from src.models.service import Service, DuplicateGroup

logger = logging.getLogger(__name__)


def find_duplicates(services: List[Service]) -> List[DuplicateGroup]:
    """
    Find all duplicate services in the provided list.

    A duplicate is defined as a service with the same protocol and port
    as another service.

    Args:
        services: List of Service objects to check for duplicates

    Returns:
        List of DuplicateGroup objects containing duplicate services

    Example:
        >>> services = [
        ...     Service(name="tcp-443-1", protocol="tcp", port="443"),
        ...     Service(name="tcp-443-2", protocol="tcp", port="443"),
        ...     Service(name="tcp-80", protocol="tcp", port="80"),
        ... ]
        >>> duplicates = find_duplicates(services)
        >>> len(duplicates)
        1
    """
    if not services:
        logger.debug("No services provided for duplicate detection")
        return []

    # Group services by protocol:port key
    grouped = group_duplicates(services)

    # Convert groups to DuplicateGroup objects
    duplicate_groups: List[DuplicateGroup] = []

    for key, group_services in grouped.items():
        if len(group_services) > 1:
            group = DuplicateGroup(
                key=key,
                services=group_services.copy()
            )
            duplicate_groups.append(group)
            logger.info(
                f"Found duplicate group '{key}' with {len(group_services)} services: "
                f"{', '.join(s.name for s in group_services)}"
            )

    logger.info(f"Total duplicate groups found: {len(duplicate_groups)}")
    return duplicate_groups


def group_duplicates(services: List[Service]) -> Dict[str, List[Service]]:
    """
    Group services by their protocol and port combination.

    This function creates a mapping from protocol:port keys to lists
    of services that share that combination.

    Args:
        services: List of Service objects to group

    Returns:
        Dictionary mapping "protocol:port" keys to lists of services

    Example:
        >>> services = [
        ...     Service(name="svc1", protocol="tcp", port="443"),
        ...     Service(name="svc2", protocol="tcp", port="443"),
        ...     Service(name="svc3", protocol="udp", port="53"),
        ... ]
        >>> groups = group_duplicates(services)
        >>> "tcp:443" in groups
        True
        >>> len(groups["tcp:443"])
        2
    """
    if not services:
        return {}

    groups: Dict[str, List[Service]] = defaultdict(list)

    for service in services:
        key = f"{service.protocol}:{service.port}"
        groups[key].append(service)

    logger.debug(f"Grouped {len(services)} services into {len(groups)} unique keys")
    return dict(groups)


def get_duplicate_sets(services: List[Service]) -> List[Tuple[str, List[Service]]]:
    """
    Get list of duplicate sets (groups with more than one service).

    This is a convenience function that returns only the groups that
    actually contain duplicates (i.e., groups with more than one service).

    Args:
        services: List of Service objects to check

    Returns:
        List of tuples containing (key, services) for each duplicate set

    Example:
        >>> services = [
        ...     Service(name="tcp-443-1", protocol="tcp", port="443"),
        ...     Service(name="tcp-443-2", protocol="tcp", port="443"),
        ...     Service(name="tcp-80", protocol="tcp", port="80"),
        ... ]
        >>> dup_sets = get_duplicate_sets(services)
        >>> len(dup_sets)
        1
        >>> dup_sets[0][0]
        'tcp:443'
    """
    grouped = group_duplicates(services)

    # Filter to only groups with more than one service
    duplicate_sets = [
        (key, group_services)
        for key, group_services in grouped.items()
        if len(group_services) > 1
    ]

    logger.debug(f"Found {len(duplicate_sets)} duplicate sets")
    return duplicate_sets


def get_unique_services(services: List[Service]) -> List[Service]:
    """
    Get services that have no duplicates.

    A service is considered unique if no other service shares
    its protocol and port combination.

    Args:
        services: List of Service objects to check

    Returns:
        List of unique services (no duplicates)

    Example:
        >>> services = [
        ...     Service(name="tcp-443-1", protocol="tcp", port="443"),
        ...     Service(name="tcp-443-2", protocol="tcp", port="443"),
        ...     Service(name="tcp-80", protocol="tcp", port="80"),
        ... ]
        >>> unique = get_unique_services(services)
        >>> len(unique)
        1
        >>> unique[0].name
        'tcp-80'
    """
    grouped = group_duplicates(services)

    unique = []
    for key, group_services in grouped.items():
        if len(group_services) == 1:
            unique.append(group_services[0])

    logger.debug(f"Found {len(unique)} unique services out of {len(services)} total")
    return unique


def generate_duplicate_report(services: List[Service]) -> str:
    """
    Generate a detailed text report of all duplicate groups.

    Args:
        services: List of Service objects to analyze

    Returns:
        Formatted string report of duplicate services

    Example:
        >>> services = [
        ...     Service(name="tcp-443-1", protocol="tcp", port="443", description="Original"),
        ...     Service(name="tcp-443-2", protocol="tcp", port="443", description="Duplicate"),
        ... ]
        >>> report = generate_duplicate_report(services)
        >>> "tcp:443" in report
        True
    """
    duplicate_groups = find_duplicates(services)

    if not duplicate_groups:
        return "No duplicate services found."

    lines = []
    lines.append("=" * 60)
    lines.append("DUPLICATE SERVICES REPORT")
    lines.append("=" * 60)
    lines.append("")

    for group in duplicate_groups:
        lines.append(f"Key: {group.key}")
        lines.append(f"  Total services: {len(group.services)}")
        lines.append("  Services:")

        for i, service in enumerate(group.services, 1):
            desc = f" - {service.description}" if service.description else ""
            lines.append(f"    {i}. {service.name}{desc} (DG: {service.device_group})")

        lines.append("")

    total_dupes = sum(len(g.services) for g in duplicate_groups)
    lines.append("-" * 60)
    lines.append(f"Total duplicate groups: {len(duplicate_groups)}")
    lines.append(f"Total services in duplicate groups: {total_dupes}")
    lines.append(f"Unique services (no duplicates): {len(get_unique_services(services))}")
    lines.append("=" * 60)

    return "\n".join(lines)