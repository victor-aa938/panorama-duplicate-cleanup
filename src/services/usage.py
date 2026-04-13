"""
Usage counting algorithm for duplicate service cleanup tool.

Provides functionality to count service references in security policies
and service groups to determine which service to keep when duplicates exist.
"""
import logging
from typing import Dict, List, Optional
from collections import defaultdict

from src.models.service import Service, ServiceGroup

logger = logging.getLogger(__name__)


class UsageCounter:
    """Counts service usage across security policies and service groups."""

    def __init__(self, policies: List[Dict], service_groups: List[ServiceGroup]):
        """
        Initialize usage counter.

        Args:
            policies: List of security policy dictionaries with service references
            service_groups: List of ServiceGroup objects to check for service members
        """
        self.policies = policies
        self.service_groups = service_groups
        self._usage_cache: Optional[Dict[str, int]] = None

    def count_all(self) -> Dict[str, int]:
        """
        Count total usage for each service across policies and groups.

        Returns:
            Dictionary mapping service names to usage counts
        """
        policy_usage = self.count_policy_usage()
        group_usage = self.count_group_usage()

        # Combine usage counts
        total_usage = defaultdict(int)
        for service_name, count in policy_usage.items():
            total_usage[service_name] += count
        for service_name, count in group_usage.items():
            total_usage[service_name] += count

        result = dict(total_usage)
        logger.debug(f"Counted usage for {len(result)} services")
        return result

    def count_policy_usage(self) -> Dict[str, int]:
        """
        Count service references in security policies.

        Returns:
            Dictionary mapping service names to policy usage counts
        """
        usage: Dict[str, int] = defaultdict(int)

        for policy in self.policies:
            services = policy.get("service", [])
            if isinstance(services, list):
                for service_name in services:
                    if isinstance(service_name, str):
                        usage[service_name] += 1
            elif isinstance(services, str):
                usage[services] += 1

        logger.debug(f"Found {len(usage)} services referenced in policies")
        return dict(usage)

    def count_group_usage(self) -> Dict[str, int]:
        """
        Count service references in service groups.

        Returns:
            Dictionary mapping service names to group usage counts
        """
        usage: Dict[str, int] = defaultdict(int)

        for group in self.service_groups:
            members = group.members or []
            for member in members:
                if isinstance(member, str):
                    usage[member] += 1

        logger.debug(f"Found {len(usage)} services referenced in groups")
        return dict(usage)

    def get_policy_breakdown(self) -> Dict[str, Dict[str, int]]:
        """
        Get per-policy usage breakdown for each service.

        Returns:
            Dictionary mapping service names to their usage counts per policy
        """
        breakdown: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for policy in self.policies:
            policy_name = policy.get("name", "unknown")
            services = policy.get("service", [])

            if isinstance(services, list):
                for service_name in services:
                    if isinstance(service_name, str):
                        breakdown[service_name][policy_name] += 1
            elif isinstance(services, str):
                breakdown[services][policy_name] += 1

        # Convert nested defaultdicts to regular dicts
        result = {service: dict(policies) for service, policies in breakdown.items()}
        logger.debug(f"Generated policy breakdown for {len(result)} services")
        return result

    def aggregate_usage(self, services: List[Service]) -> Dict[str, Dict]:
        """
        Aggregate usage information for a list of services.

        Args:
            services: List of Service objects to aggregate usage for

        Returns:
            Dictionary mapping service names to usage info (total, policies, groups)
        """
        policy_usage = self.count_policy_usage()
        group_usage = self.count_group_usage()

        result = {}
        for service in services:
            service_name = service.name
            policy_count = policy_usage.get(service_name, 0)
            group_count = group_usage.get(service_name, 0)

            result[service_name] = {
                "total": policy_count + group_count,
                "policy_count": policy_count,
                "group_count": group_count,
                "policy_breakdown": self.get_policy_breakdown().get(service_name, {}),
            }

        return result


def count_service_usage(
    service: Service,
    policies: List[Dict],
    service_groups: List[ServiceGroup]
) -> int:
    """
    Count total usage for a single service across policies and groups.

    Args:
        service: Service object to count
        policies: List of security policy dictionaries
        service_groups: List of ServiceGroup objects

    Returns:
        Total usage count for the service
    """
    counter = UsageCounter(policies, service_groups)

    # Count in policies
    policy_count = 0
    for policy in policies:
        services = policy.get("service", [])
        service_names = (
            services if isinstance(services, list)
            else [services] if isinstance(services, str)
            else []
        )
        if service.name in service_names:
            policy_count += 1

    # Count in groups
    group_count = 0
    for group in service_groups:
        if service.name in (group.members or []):
            group_count += 1

    total = policy_count + group_count
    logger.debug(f"Service '{service.name}' used {total} times ({policy_count} policies, {group_count} groups)")
    return total