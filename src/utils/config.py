"""
Configuration parser and CLI argument handler.

Provides argparse.setup for all command-line arguments and optional config file support.
"""

import argparse
import logging
import os
from typing import Optional, Dict, Any
from src.utils.logger import get_logger


class Config:
    """Configuration class for duplicate service cleanup tool."""

    def __init__(
        self,
        panorama_ip: str,
        username: str,
        password: str,
        dry_run: bool = True,
        commit: bool = False,
        backup_dir: str = "./backups",
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        use_json_logging: bool = False,
    ):
        """
        Initialize configuration.

        Args:
            panorama_ip: Panorama manager IP address
            username: Panorama username
            password: Panorama password
            dry_run: Enable dry-run mode
            commit: Execute actual changes (overrides dry_run)
            backup_dir: Directory for backup files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            log_file: Path to log file
            use_json_logging: Use JSON format for logging
        """
        self.panorama_ip = panorama_ip
        self.username = username
        self.password = password
        self.dry_run = not commit if commit else dry_run
        self.commit = commit
        self.backup_dir = backup_dir
        self.log_level = log_level
        self.log_file = log_file
        self.use_json_logging = use_json_logging

        # Validate required fields
        self._validate()

    def _validate(self) -> None:
        """Validate required configuration values."""
        if not self.panorama_ip:
            raise ValueError("Panorama IP address is required")
        if not self.username:
            raise ValueError("Username is required")
        # Password can be empty if using other auth methods

        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if self.log_level not in valid_levels:
            raise ValueError(
                f"Invalid log level: {self.log_level}. Must be one of {valid_levels}"
            )

        # Create backup directory if needed
        if self.backup_dir:
            os.makedirs(self.backup_dir, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary (excluding password)."""
        return {
            "panorama_ip": self.panorama_ip,
            "username": self.username,
            "dry_run": self.dry_run,
            "commit": self.commit,
            "backup_dir": self.backup_dir,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "use_json_logging": self.use_json_logging,
        }


def setup_argparse() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="duplicate-service-cleanup",
        description="Identify and clean up duplicate services in Palo Alto Panorama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run mode (default - preview only)
  python3 -m src.duplicate_service_cleanup --panorama-ip 1.2.3.4 --username admin

  # Commit mode (makes actual changes)
  python3 -m src.duplicate_service_cleanup --panorama-ip 1.2.3.4 --username admin --commit

  # With custom backup directory
  python3 -m src.duplicate_service_cleanup --panorama-ip 1.2.3.4 --backup-dir /tmp/backups --commit
""",
    )

    # Required arguments
    parser.add_argument(
        "--panorama-ip",
        required=True,
        help="Panorama manager IP address (required)",
    )
    parser.add_argument(
        "--username",
        required=True,
        help="Panorama username (required)",
    )
    parser.add_argument(
        "--password",
        required=False,
        help="Panorama password (optional - will prompt if not provided)",
        nargs="?",
        const=None,
    )

    # Mode arguments
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview mode - no changes made (default: enabled)",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Execute changes - overrides dry-run mode",
    )

    # Configuration options
    parser.add_argument(
        "--backup-dir",
        default="./backups",
        help="Directory for backup files (default: ./backups)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Path to log file (optional)",
    )
    parser.add_argument(
        "--json-logging",
        action="store_true",
        help="Use JSON format for file logging",
    )

    # Config file option
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (YAML/JSON)",
    )

    return parser


def parse_args(args: Optional[list] = None) -> Config:
    """
    Parse command line arguments and return configuration.

    Args:
        args: Command line arguments (defaults to sys.argv)

    Returns:
        Config object with parsed values

    Raises:
        ValueError: If required arguments are missing or invalid
    """
    parser = setup_argparse()

    try:
        parsed = parser.parse_args(args)

        # Handle password - prompt if not provided
        password = parsed.password
        if password is None:
            import getpass
            password = getpass.getpass("Enter Panorama password: ")

        # Convert log level string to value
        log_level = getattr(logging, parsed.log_level.upper())

        # Determine mode
        dry_run = not parsed.commit  # commit overrides dry_run

        config = Config(
            panorama_ip=parsed.panorama_ip,
            username=parsed.username,
            password=password,
            dry_run=dry_run,
            commit=parsed.commit,
            backup_dir=parsed.backup_dir,
            log_level=parsed.log_level,
            log_file=parsed.log_file,
            use_json_logging=parsed.json_logging,
        )

        # Initialize logger
        get_logger(
            name="duplicate_service_cleanup",
            log_file=config.log_file,
            console_level=log_level,
            file_level=getattr(logging, "DEBUG"),
            use_json=config.use_json_logging,
        )

        return config

    except SystemExit:
        raise  # Re-raise argparse errors


def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML or JSON file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        if config_path.endswith(".yaml") or config_path.endswith(".yml"):
            try:
                import yaml

                return yaml.safe_load(f)
            except ImportError:
                raise ValueError(
                    "YAML library not installed. Install with: pip install pyyaml"
                )
        elif config_path.endswith(".json"):
            import json

            return json.load(f)
        else:
            raise ValueError(
                f"Unsupported config file format: {config_path}. Use .yaml, .yml, or .json"
            )


def create_sample_config() -> str:
    """Return sample configuration as string."""
    return """# Sample configuration file
# Save as config.yaml or config.json

panorama:
  ip: "192.168.1.1"
  username: "admin"

mode:
  dry_run: true
  # commit: true  # Uncomment to execute changes

logging:
  level: "INFO"
  file: "logs/duplicate_service_cleanup.log"
  json_format: false

backup:
  directory: "./backups"
"""