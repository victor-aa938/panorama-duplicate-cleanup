"""Unit tests for tie-breaking logic."""
import pytest

from src.services.tiebreaker import TieBreaker, get_tiebreaker_winners


def test_select_alphabetical_winners():
    """Test alphabetical tie-breaking."""
    breaker = TieBreaker()
    services = ["svc-3", "svc-1", "svc-2"]
    winners = breaker.select_alphabetical_winners(services)
    
    assert len(winners) == 1
    assert winners[0] == "svc-1"


def test_select_by_usage_and_alpha():
    """Test selection by usage with alphabetical tie-breaker."""
    breaker = TieBreaker()
    
    # Equal usage - should pick alphabetically first
    names = ["svc-2", "svc-1"]
    usage = [10, 10]
    winner = breaker.select_by_usage_and_alpha(names, usage)
    
    assert winner == ["svc-1"]


def test_select_winner():
    """Test selecting single winner."""
    breaker = TieBreaker()
    
    # Different usage - highest wins
    names = ["svc-1", "svc-2"]
    usage = [10, 20]
    winner = breaker.select_winner(names, usage)
    
    assert winner == "svc-2"
    
    # Equal usage with tie-breaker
    winner = breaker.select_winner(["svc-2", "svc-1"], [10, 10])
    assert winner == "svc-1"


def test_no_tiebreaker():
    """Test selection without tie-breaker."""
    breaker = TieBreaker()
    winner = breaker.select_winner(
        ["svc-2", "svc-1"], [10, 10], use_alpha_tiebreaker=False
    )
    # Returns first of equal winners
    assert winner in ["svc-1", "svc-2"]


def test_get_tiebreaker_winners():
    """Test standalone winner function."""
    winners = get_tiebreaker_winners(["svc-2", "svc-1"], [10, 10])
    assert winners == ["svc-1"]
