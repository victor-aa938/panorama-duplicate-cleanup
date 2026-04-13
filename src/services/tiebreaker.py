"""
Tie-breaking logic for duplicate service cleanup tool.

Provides deterministic selection of which service to keep when duplicates
have equal usage counts, using alphabetical ordering as the tie-breaker.
"""
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class TieBreaker:
    """Determines which service to keep when duplicates have equal usage."""

    @staticmethod
    def select_alphabetical_winners(services: List[str]) -> List[str]:
        """
        Select alphabetically first services from a list of service names.

        Args:
            services: List of service names (duplicates)

        Returns:
            List of alphabetically first services
        """
        if not services:
            return []

        # Sort alphabetically and return all instances of the first name
        sorted_services = sorted(services)
        winner = sorted_services[0]
        winners = [s for s in sorted_services if s == winner]

        logger.debug(f"Alphabetical tie-breaker: selected {winners} from {services}")
        return winners

    @staticmethod
    def select_by_usage_and_alpha(
        service_names: List[str],
        usage_counts: List[int]
    ) -> List[str]:
        """
        Select winners by highest usage, using alphabetical order for ties.

        Args:
            service_names: List of service names
            usage_counts: Corresponding usage counts

        Returns:
            List of winning service names
        """
        if not service_names or not usage_counts:
            return []

        # Pair services with their usage counts
        paired = list(zip(service_names, usage_counts))

        # Find maximum usage
        max_usage = max(count for _, count in paired)

        # Filter to services with max usage
        max_services = [name for name, count in paired if count == max_usage]

        # Use alphabetical tie-breaker
        winners = TieBreaker.select_alphabetical_winners(max_services)

        logger.info(f"Selected winner(s) {winners} from {service_names} with usage {max_usage}")
        return winners

    def select_winner(
        self,
        service_names: List[str],
        usage_counts: List[int],
        use_alpha_tiebreaker: bool = True
    ) -> Optional[str]:
        """
        Select a single winning service by usage count.

        Args:
            service_names: List of service names (duplicates)
            usage_counts: Corresponding usage counts
            use_alpha_tiebreaker: If True, use alphabetical tie-breaker

        Returns:
            Single winning service name, or None if tie-breaker needed
        """
        if not service_names or not usage_counts:
            return None

        if len(service_names) != len(usage_counts):
            logger.error("Service names and usage counts must have same length")
            return None

        # Find maximum usage
        max_usage = max(usage_counts)

        # Get all services with max usage
        max_services = [
            name for name, count in zip(service_names, usage_counts)
            if count == max_usage
        ]

        if len(max_services) == 1:
            logger.debug(f"Selected winner: {max_services[0]} (usage: {max_usage})")
            return max_services[0]

        # Tie exists - use alphabetical tie-breaker
        if use_alpha_tiebreaker:
            winner = self.select_alphabetical_winners(max_services)[0]
            logger.info(f"Tie-breaker selected: {winner} from {max_services}")
            return winner

        # Return all tied services if no tie-breaker
        logger.debug(f"No tie-breaker, returning all: {max_services}")
        return max_services[0]

    def generate_tiebreaker_report(
        self,
        duplicate_groups: List[Tuple[str, List[str]]],
        usage_data: Dict[str, int]
    ) -> str:
        """
        Generate a report of tie-breaking decisions for duplicate groups.

        Args:
            duplicate_groups: List of (key, service_names) tuples
            usage_data: Dictionary mapping service names to usage counts

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("TIE-BREAKING REPORT")
        lines.append("=" * 60)
        lines.append("")

        for key, services in duplicate_groups:
            usage_list = [usage_data.get(s, 0) for s in services]
            winner = self.select_winner(services, usage_list)

            lines.append(f"Duplicate Group: {key}")
            lines.append("  Services and usage:")
            for service, usage in zip(services, usage_list):
                marker = " <- SELECTED" if service == winner else ""
                lines.append(f"    - {service}: {usage}{marker}")
            lines.append("")

        lines.append("-" * 60)
        lines.append(f"Total duplicate groups: {len(duplicate_groups)}")
        lines.append("=" * 60)

        return "\n".join(lines)


def get_tiebreaker_winners(
    service_names: List[str],
    usage_counts: List[int],
    use_alpha_tiebreaker: bool = True
) -> List[str]:
    """
    Convenience function to get tie-breaking winners.

    Args:
        service_names: List of service names
        usage_counts: Corresponding usage counts
        use_alpha_tiebreaker: If True, use alphabetical tie-breaker

    Returns:
        List of winning service names
    """
    breaker = TieBreaker()
    return breaker.select_by_usage_and_alpha(service_names, usage_counts)