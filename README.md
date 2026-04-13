# Duplicate Service Cleanup Tool

A Python tool to identify and clean up duplicate services in Palo Alto Panorama using the pan-os-python SDK.

## Overview

This tool helps you identify duplicate services (e.g., "443-1" and "443-2" for port 443/TCP), determines which service to keep based on usage counts, migrates all references, and safely removes duplicates.

## Features

- **Dry-run mode**: Preview changes without making modifications
- **Usage counting**: Track service references in security policies and service groups
- **Smart tie-breaking**: Alphabetically first service wins when usage is equal
- **Backup and rollback**: Safety features for recovery
- **Comprehensive logging**: Detailed operation tracking

## Requirements

- Python 3.8+
- Palo Alto Panorama with API access
- pan-os-python SDK

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Dry-run mode (recommended for first run)

```bash
python3 -m src.duplicate_service_cleanup \
    --panorama-ip <IP> \
    --username <username> \
    --password <password>
```

### Commit mode (makes actual changes)

```bash
python3 -m src.duplicate_service_cleanup \
    --panorama-ip <IP> \
    --username <username> \
    --password <password> \
    --commit
```

### Command-line options

| Option | Description |
|--------|-------------|
| `--panorama-ip` | Panorama manager IP address (required) |
| `--username` | Panorama username (required) |
| `--password` | Panorama password (required) |
| `--commit` | Execute changes (default: dry-run) |
| `--backup-dir` | Directory for backup files (default: ./backups) |
| `--log-level` | Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO) |

## Safety Features

-Dry-run is the default mode
- Backup created before any modifications
- No deletion of services with active references
- Rollback capability available
- Detailed logging of all operations

## Directory Structure

```
.
├── src/              # Main source code
│   ├── utils/       # Utility modules
│   ├── models/      # Data models
│   ├── services/    # Service operations
│   ├── policies/    # Policy operations
│   └── duplicate_service_cleanup.py
├── tests/           # Test suite
│   ├── mocks/       # Mock fixtures
│   └── unit/        # Unit tests
├── utils/           # Additional utilities
├── requirements.txt
└── README.md
```

## Contributing

1. Create a feature branch
2. Run tests: `pytest tests/ -v`
3. Ensure coverage stays high
4. Create a pull request

## License

MIT