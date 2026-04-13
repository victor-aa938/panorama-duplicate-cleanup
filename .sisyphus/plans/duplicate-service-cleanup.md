# Duplicate Service Cleanup Tool

## TL;DR

> **Quick Summary**: Create a Python script using pan-os-python SDK to identify and clean up duplicate services in Palo Alto Panorama by keeping the most-used service and migrating all references before deleting duplicates.
> 
> **Deliverables**:
> - Python script with dry-run and commit modes
> - Service discovery and duplicate detection logic
> - Usage counting in security policies and service groups
> - Reference migration functionality
> - Comprehensive logging and reporting
> - Backup and rollback capabilities
> - Full test suite with pytest
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 6 waves
> **Critical Path**: Task 1 → Task 4 → Task 7 → Task 10 → Task 13 → Task 16 → F1-F4

---

## Context

### Original Request
"I want to create a python script so I can fix duplicate services on palo alto panorama. I want this to use the pan os sdk. My issue is I have duplicate services for the same port and protocol for example 443-1 and 443-2 and both these services do the same thing. To clean up the palo services we would keep the most used service. I.E the one that is called in the most service policies or service groups. then update all the rules that contain the duplicate to use the most used service instead. then delete the duplicates"

### Interview Summary
**Key Discussions**:
- **Connection Method**: Panorama Manager as centralized single source of truth
- **Dry-run Mode**: YES - Preview mode required, needs `--commit` flag to execute changes
- **Tie-Breaking Strategy**: Keep alphabetically first (e.g., '443-1' over '443-2')
- **Service Group Cleanup**: Report but don't delete empty groups after migration
- **Automated Tests**: YES - TDD approach with pytest and mock PanOS connections
- **Risk Tolerance**: Conservative - backup policies, detailed logging, step-by-step confirmation, dry-run required

**Research Findings**:
- **PanOS SDK**: Available via Context7 library `/paloaltonetworks/pan.dev`
- **API Capabilities**: GET services, security policies, service groups; PUT/DELETE operations for updates
- **Key Endpoints**: Services, policies/firewall (security rules), service groups

### Metis Review
**Identified Gaps** (addressed):
- Added explicit validation for service group member references
- Clarified that commit operations are separate from migration
- Added rollback procedure documentation
- Included rate limiting considerations for large deployments

---

## Work Objectives

### Core Objective
Build a production-ready Python tool to safely identify, migrate, and remove duplicate services in Palo Alto Panorama while maintaining security policy integrity.

### Concrete Deliverables
- `src/duplicate_service_cleanup.py` - Main CLI script
- `src/services/` - Service discovery and management modules
- `src/policies/` - Security policy and service group handling
- `src/utils/` - Logging, backup, and utility functions
- `tests/` - Comprehensive test suite
- `README.md` - Usage documentation
- `requirements.txt` - Dependencies

### Definition of Done
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Dry-run mode works without making changes
- [ ] Commit mode successfully migrates and deletes
- [ ] Backup files created before any changes
- [ ] Logging captures all operations with proper levels
- [ ] Rollback procedure documented and tested

### Must Have
- Use pan-os-python SDK for all Panorama interactions
- Dry-run mode by default (safe preview)
- Commit mode with explicit flag
- Backup creation before modifications
- Comprehensive logging with file output
- Usage counting across policies and service groups
- Tie-breaking logic for equal usage counts

### Must NOT Have (Guardrails)
- NO modifications without explicit `--commit` flag
- NO deletion of empty service groups (report only)
- NO touching NAT policies, QoS policies, or application firewall rules
- NO automatic commit/push to Panorama
- NO production use without thorough testing in non-production first
- NO removing services actively in use (usage > 0) without migration

---

## Verification Strategy (MANDATORY)

### Test Decision
- **Infrastructure exists**: NO (empty project - will be set up)
- **Automated tests**: YES (TDD approach)
- **Framework**: pytest with unittest.mock for PanOS SDK mocking
- **If TDD**: Each task follows RED (failing test) → GREEN (minimal impl) → REFACTOR

### QA Policy
Every task MUST include agent-executed QA scenarios (see TODO template below).
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Frontend/UI**: N/A (CLI tool)
- **TUI/CLI**: Use interactive_bash (tmux) — Run commands, validate output
- **API/Backend**: Use Bash (Python script execution) — Call functions, verify results
- **Library/Module**: Use Bash (pytest) — Import, run tests, compare output

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation + scaffolding):
├── Task 1: Project setup + requirements.txt [quick]
├── Task 2: Logging utility module [quick]
├── Task 3: Configuration parser + CLI args [quick]
├── Task 4: PanOS connection manager [quick]
└── Task 5: Backup utility module [quick]

Wave 2 (After Wave 1 — core data structures, MAX PARALLEL):
├── Task 6: Service model + data classes [quick]
├── Task 7: Service discovery module [unspecified-high]
├── Task 8: Duplicate detection logic [deep]
├── Task 9: Usage counting algorithm [deep]
└── Task 10: Tie-breaking logic [quick]

Wave 3 (After Wave 2 — policy handling, MAX PARALLEL):
├── Task 11: Security policy fetcher [unspecified-high]
├── Task 12: Service group fetcher [unspecified-high]
├── Task 13: Reference migration logic [deep]
└── Task 14: Service deletion logic [deep]

Wave 4 (After Wave 3 — main orchestration):
├── Task 15: Main CLI script integration [deep]
├── Task 16: Rollback functionality [deep]
└── Task 17: Report generation [quick]

Wave 5 (After Wave 4 — testing setup):
├── Task 18: Pytest configuration + fixtures [quick]
├── Task 19: Mock PanOS SDK setup [deep]
└── Task 20: Unit tests for all modules [unspecified-high]

Wave 6 (After Wave 5 — integration):
├── Task 21: Integration tests [deep]
├── Task 22: End-to-end QA scenarios [unspecified-high]
└── Task 23: Documentation + README [writing]

Wave FINAL (After ALL tasks — independent review, 4 parallel):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
└── Task F4: Scope fidelity check (deep)

Critical Path: Task 1 → Task 4 → Task 7 → Task 10 → Task 13 → Task 16 → F1-F4
Parallel Speedup: ~75% faster than sequential
Max Concurrent: 9 (Wave 2)
```

### Dependency Matrix

- **1-5**: — — 6-17, 18-23
- **6**: — — 7-10, 11-14
- **7**: 6 — 8, 11, 12
- **8**: 6, 7 — 9, 13
- **10**: 8, 9 — 13
- **11**: 7 — 12, 13
- **12**: 7 — 13, 14
- **13**: 8, 10, 11, 12 — 15, 16
- **14**: 12 — 15, 16
- **15**: 13, 14 — 17, 21
- **16**: 13, 14 — 17, 21
- **17**: 15, 16 — 21, 22
- **18-20**: — — 21, 22
- **21**: 15-17, 20 — 22, F1-F4
- **22**: 21 — F1-F4
- **23**: 1-22 — F1-F4

### Agent Dispatch Summary

- **1**: **5** — T1 → `quick`, T2 → `quick`, T3 → `quick`, T4 → `quick`, T5 → `quick`
- **2**: **5** — T6 → `quick`, T7 → `unspecified-high`, T8 → `deep`, T9 → `deep`, T10 → `quick`
- **3**: **4** — T11 → `unspecified-high`, T12 → `unspecified-high`, T13 → `deep`, T14 → `deep`
- **4**: **3** — T15 → `deep`, T16 → `deep`, T17 → `quick`
- **5**: **3** — T18 → `quick`, T19 → `deep`, T20 → `unspecified-high`
- **6**: **3** — T21 → `deep`, T22 → `unspecified-high`, T23 → `writing`
- **FINAL**: **4** — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [ ] 1. Project setup + requirements.txt

  **What to do**:
  - Create project directory structure: `src/`, `tests/`, `utils/`
  - Create `requirements.txt` with pan-os-python and other dependencies
  - Initialize Python package with `__init__.py` files
  - Create `.gitignore` for Python projects
  - Add basic README with project description

  **Must NOT do**:
  - Do not implement any logic yet
  - Do not add unnecessary dependencies

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Standard project scaffolding, no complex logic
  - **Skills**: []
    - No specialized skills needed for basic setup

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2-5)
  - **Blocks**: All subsequent tasks depend on project structure
  - **Blocked By**: None (can start immediately)

  **References**:
  - **Pattern References**: None (standard Python project structure)
  - **External References**: 
    - Official docs: `https://panos-python.readthedocs.io/` - pan-os-python installation

  **Acceptance Criteria**:
  - [ ] Project structure created: `src/`, `tests/`, `utils/` directories
  - [ ] `requirements.txt` exists with pan-os-python dependency
  - [ ] `__init__.py` files in all Python packages
  - [ ] `.gitignore` file present with Python patterns
  - [ ] Basic README.md exists

  **QA Scenarios (MANDATORY — task is INCOMPLETE without these)**:
  ```
  Scenario: Verify project structure
    Tool: interactive_bash (tmux)
    Preconditions: None
    Steps:
      1. Run: ls -la
      2. Run: find . -type d | sort
      3. Verify directories: src/, tests/, utils/ exist
    Expected Result: All required directories present
    Failure Indicators: Missing directories
    Evidence: .sisyphus/evidence/task-1-project-structure.txt

  Scenario: Verify requirements.txt
    Tool: Bash
    Preconditions: requirements.txt exists
    Steps:
      1. Run: cat requirements.txt
      2. Check for pan-os-python in file
    Expected Result: pan-os-python listed in dependencies
    Failure Indicators: Missing pan-os-python dependency
    Evidence: .sisyphus/evidence/task-1-requirements.txt
  ```

  **Commit**: YES
  - Message: `feat: initial project scaffolding`
  - Files: `requirements.txt`, `.gitignore`, `README.md`, directory structure

---

- [ ] 2. Logging utility module

  **What to do**:
  - Create `src/utils/logger.py` with logging configuration
  - Implement file and console logging with proper levels
  - Add timestamp, module name, and context to logs
  - Create log rotation for large outputs
  - Add JSON logging option for structured output

  **Must NOT do**:
  - Do not add logging to production code yet
  - Do not use print statements

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Standard Python logging setup
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3-5)
  - **Blocks**: All tasks requiring logging
  - **Blocked By**: None

  **References**:
  - **Pattern References**: Standard Python logging best practices
  - **External References**: 
    - Official docs: `https://docs.python.org/3/library/logging.html`

  **Acceptance Criteria**:
  - [ ] `src/utils/logger.py` created
  - [ ] Logging configured with file and console handlers
  - [ ] Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - [ ] Log rotation implemented (max 10MB, 5 backups)
  - [ ] JSON logging option available

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test logging configuration
    Tool: Bash (Python)
    Preconditions: logger.py exists
    Steps:
      1. Run: python3 -c "from src.utils.logger import get_logger; logger = get_logger(); logger.info('test')"
      2. Check console output for INFO message
      3. Check log file for same message
    Expected Result: Message appears in both console and file
    Failure Indicators: No output or missing file
    Evidence: .sisyphus/evidence/task-2-logging-test.log

  Scenario: Test log rotation
    Tool: Bash
    Preconditions: Log file exists
    Steps:
      1. Run: python3 -c "import sys; sys.path.insert(0, '.'); from src.utils.logger import get_logger; logger = get_logger(); [logger.info('x'*1000000) for _ in range(10)]"
      2. Check for log files with rotation pattern
    Expected Result: Log files rotated properly
    Failure Indicators: Single oversized log file
    Evidence: .sisyphus/evidence/task-2-log-rotation.txt
  ```

  **Commit**: YES
  - Message: `feat: add logging utility`
  - Files: `src/utils/logger.py`

---

- [ ] 3. Configuration parser + CLI args

  **What to do**:
  - Create `src/utils/config.py` with argparse setup
  - Implement command-line arguments: `--panorama-ip`, `--username`, `--password`, `--commit`, `--dry-run`, `--backup-dir`
  - Add configuration file support (optional YAML/JSON)
  - Implement validation for required arguments
  - Add help documentation

  **Must NOT do**:
  - Do not store credentials in config files
  - Do not log passwords

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Standard CLI argument parsing
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1-2, 4-5)
  - **Blocks**: All tasks requiring configuration
  - **Blocked By**: None

  **References**:
  - **Pattern References**: Standard argparse patterns
  - **External References**: 
    - Official docs: `https://docs.python.org/3/library/argparse.html`

  **Acceptance Criteria**:
  - [ ] `src/utils/config.py` created
  - [ ] All required CLI arguments implemented
  - [ ] Validation for required arguments
  - [ ] Help text available: `--help`
  - [ ] Dry-run mode enabled by default

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test CLI argument parsing
    Tool: interactive_bash (tmux)
    Preconditions: config.py exists
    Steps:
      1. Run: python3 -m src.duplicate_service_cleanup --help
      2. Verify all arguments listed
      3. Run: python3 -m src.duplicate_service_cleanup --panorama-ip 1.2.3.4 --username admin
      4. Check for missing argument error
    Expected Result: Help shows all args, validation works
    Failure Indicators: Missing args or no validation
    Evidence: .sisyphus/evidence/task-3-cli-help.txt

  Scenario: Test dry-run default
    Tool: Bash
    Preconditions: Script exists
    Steps:
      1. Run: python3 -m src.duplicate_service_cleanup --panorama-ip 1.2.3.4 --username admin 2>&1 | grep -i dry
    Expected Result: Shows dry-run mode active
    Failure Indicators: No dry-run indication
    Evidence: .sisyphus/evidence/task-3-dryrun.txt
  ```

  **Commit**: YES
  - Message: `feat: add CLI argument parsing`
  - Files: `src/utils/config.py`

---

- [ ] 4. PanOS connection manager

  **What to do**:
  - Create `src/utils/connection.py` with PanOS API connection
  - Implement connection class using pan-os-python SDK
  - Add error handling for connection failures
  - Implement session management and cleanup
  - Add retry logic with exponential backoff

  **Must NOT do**:
  - Do not make actual API calls in tests
  - Do not hardcode credentials

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Standard API connection pattern
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1-3, 5)
  - **Blocks**: All PanOS API operations
  - **Blocked By**: None

  **References**:
  - **Pattern References**: None yet (first implementation)
  - **External References**: 
    - Official docs: `https://panos-python.readthedocs.io/` - Connection setup examples

  **Acceptance Criteria**:
  - [ ] `src/utils/connection.py` created
  - [ ] PanOSConnection class implemented
  - [ ] Error handling for connection failures
  - [ ] Session cleanup on exit
  - [ ] Retry logic with exponential backoff

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test connection class creation
    Tool: Bash (Python)
    Preconditions: connection.py exists
    Steps:
      1. Run: python3 -c "from src.utils.connection import PanOSConnection; conn = PanOSConnection('1.2.3.4', 'admin', 'test')"
      2. Verify object created without error
    Expected Result: Connection object instantiated
    Failure Indicators: Exception raised
    Evidence: .sisyphus/evidence/task-4-connection-object.py

  Scenario: Test connection error handling
    Tool: Bash
    Preconditions: connection.py exists
    Steps:
      1. Run: python3 -c "from src.utils.connection import PanOSConnection; conn = PanOSConnection('invalid', 'admin', 'test')"
      2. Check for proper error message
    Expected Result: Clear error message for invalid IP
    Failure Indicators: No error or cryptic message
    Evidence: .sisyphus/evidence/task-4-error-handling.txt
  ```

  **Commit**: YES
  - message: `feat: add PanOS connection manager`
  - Files: `src/utils/connection.py`

---

- [ ] 5. Backup utility module

  **What to do**:
  - Create `src/utils/backup.py` with backup functionality
  - Implement policy backup before modifications
  - Create timestamped backup files
  - Support backup directory configuration
  - Implement rollback file generation

  **Must NOT do**:
  - Do not overwrite existing backups without warning
  - Do not backup to same directory as original

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Standard file backup pattern
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1-4)
  - **Blocks**: All modification operations
  - **Blocked By**: None

  **References**:
  - **Pattern References**: Standard Python file backup patterns
  - **External References**: 
    - Official docs: `https://docs.python.org/3/library/shutil.html` - File operations

  **Acceptance Criteria**:
  - [ ] `src/utils/backup.py` created
  - [ ] Backup creation with timestamps
  - [ ] Rollback file generation
  - [ ] Backup directory validation
  - [ ] Backup verification function

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test backup creation
    Tool: Bash
    Preconditions: backup.py exists
    Steps:
      1. Run: python3 -c "from src.utils.backup import create_backup; create_backup('test.xml', '/tmp/backups')"
      2. Check backup file exists with timestamp
    Expected Result: Backup file created with timestamp in name
    Failure Indicators: No backup file created
    Evidence: .sisyphus/evidence/task-5-backup-creation.txt

  Scenario: Test rollback file generation
    Tool: Bash
    Preconditions: Backup exists
    Steps:
      1. Run: python3 -c "from src.utils.backup import create_rollback; create_rollback('test.xml')"
      2. Check rollback file created
    Expected Result: Rollback file generated
    Failure Indicators: No rollback file
    Evidence: .sisyphus/evidence/task-5-rollback.txt
  ```

  **Commit**: YES
  - Message: `feat: add backup utility`
  - Files: `src/utils/backup.py`

---

- [ ] 6. Service model + data classes

  **What to do**:
  - Create `src/models/service.py` with Service data class
  - Implement ServiceGroup data class
  - Add ServicePolicyReference data class
  - Include all necessary fields from PanOS API
  - Add serialization/deserialization methods

  **Must NOT do**:
  - Do not include business logic in models
  - Do not add database operations

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Standard data class creation
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7-10)
  - **Blocks**: All service-related operations
  - **Blocked By**: Tasks 1-5 (infrastructure)

  **References**:
  - **Pattern References**: None yet (first implementation)
  - **External References**: 
    - Official docs: `https://panos-python.readthedocs.io/` - Service API response structure

  **Acceptance Criteria**:
  - [ ] `src/models/service.py` created
  - [ ] Service data class with all fields
  - [ ] ServiceGroup data class
  - [ ] ServicePolicyReference data class
  - [ ] JSON serialization methods

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test Service data class
    Tool: Bash (Python)
    Preconditions: service.py exists
    Steps:
      1. Run: python3 -c "from src.models.service import Service; s = Service(name='test', protocol='tcp', port='443'); print(s.name)"
      2. Verify all attributes accessible
    Expected Result: Service object with all attributes
    Failure Indicators: AttributeError or missing field
    Evidence: .sisyphus/evidence/task-6-service-model.py

  Scenario: Test serialization
    Tool: Bash
    Preconditions: Service class exists
    Steps:
      1. Run: python3 -c "from src.models.service import Service; import json; s = Service(name='test', protocol='tcp', port='443'); print(json.dumps(s.to_dict()))"
    Expected Result: Valid JSON output
    Failure Indicators: Serialization error
    Evidence: .sisyphus/evidence/task-6-serialization.json
  ```

  **Commit**: YES
  - Message: `feat: add service data models`
  - Files: `src/models/service.py`

---

- [ ] 7. Service discovery module

  **What to do**:
  - Create `src/services/discovery.py` with service fetching logic
  - Implement method to fetch all services from Panorama
  - Add filtering by port/protocol
  - Handle pagination for large service lists
  - Include error handling and retry logic

  **Must NOT do**:
  - Do not modify services during discovery
  - Do not cache services permanently

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `unspecified-high`
    - Reason: API integration with error handling
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 8-10)
  - **Blocks**: All service-related operations
  - **Blocked By**: Tasks 6 (models), Tasks 1-5 (infrastructure)

  **References**:
  - **Pattern References**: None yet (first implementation)
  - **External References**: 
    - Official docs: `https://panos-python.readthedocs.io/` - Service API endpoints

  **Acceptance Criteria**:
  - [ ] `src/services/discovery.py` created
  - [ ] Fetch all services method implemented
  - [ ] Port/protocol filtering available
  - [ ] Pagination handling for large datasets
  - [ ] Error handling with retry logic

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test service discovery
    Tool: Bash (Python)
    Preconditions: discovery.py exists, mock connection available
    Steps:
      1. Run: python3 -c "from src.services.discovery import ServiceDiscovery; from unittest.mock import Mock; disc = ServiceDiscovery(Mock()); services = disc.fetch_all(); print(len(services))"
      2. Verify list of services returned
    Expected Result: List of Service objects
    Failure Indicators: Empty list or exception
    Evidence: .sisyphus/evidence/task-7-discovery.py

  Scenario: Test filtering
    Tool: Bash
    Preconditions: Services exist
    Steps:
      1. Run: python3 -c "from src.services.discovery import ServiceDiscovery; from unittest.mock import Mock; disc = ServiceDiscovery(Mock()); tcp443 = disc.fetch_by_protocol('tcp', '443'); print(len(tcp443))"
    Expected Result: Filtered list of TCP 443 services
    Failure Indicators: Wrong services returned
    Evidence: .sisyphus/evidence/task-7-filter.py
  ```

  **Commit**: YES
  - Message: `feat: add service discovery module`
  - Files: `src/services/discovery.py`

---

- [ ] 8. Duplicate detection logic

  **What to do**:
  - Create `src/services/duplicates.py` with duplicate detection
  - Implement logic to identify services with same port + protocol
  - Group duplicates by port/protocol combination
  - Track all duplicate sets found
  - Include detailed reporting of duplicates

  **Must NOT do**:
  - Do not delete duplicates yet
  - Do not modify any services

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `deep`
    - Reason: Complex algorithm for duplicate detection
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7, 9-10)
  - **Blocks**: Migration logic
  - **Blocked By**: Task 7 (discovery)

  **References**:
  - **Pattern References**: None yet (first implementation)
  - **External References**: 
    - Official docs: None specific to duplicate detection

  **Acceptance Criteria**:
  - [ ] `src/services/duplicates.py` created
  - [ ] Duplicate detection by port + protocol
  - [ ] Grouping of duplicate sets
  - [ ] Detailed duplicate report generation
  - [ ] No modifications to services

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test duplicate detection
    Tool: Bash (Python)
    Preconditions: duplicates.py exists, mock services available
    Steps:
      1. Run: python3 -c "from src.services.duplicates import DuplicateDetector; from unittest.mock import Mock; det = DuplicateDetector(Mock()); dups = det.find_duplicates(); print(len(dups))"
      2. Verify duplicate sets identified
    Expected Result: List of duplicate sets
    Failure Indicators: No duplicates found or exception
    Evidence: .sisyphus/evidence/task-8-duplicates.py

  Scenario: Test grouping
    Tool: Bash
    Preconditions: Duplicates exist
    Steps:
      1. Run: python3 -c "from src.services.duplicates import DuplicateDetector; from unittest.mock import Mock; det = DuplicateDetector(Mock()); groups = det.group_duplicates(); print(groups.keys())"
    Expected Result: Groups keyed by port+protocol
    Failure Indicators: Wrong grouping
    Evidence: .sisyphus/evidence/task-8-grouping.txt
  ```

  **Commit**: YES
  - Message: `feat: add duplicate detection logic`
  - Files: `src/services/duplicates.py`

---

- [ ] 9. Usage counting algorithm

  **What to do**:
  - Create `src/services/usage.py` with usage counting
  - Implement counting of service references in security policies
  - Count references in service groups
  - Aggregate total usage per service
  - Include per-policy breakdown

  **Must NOT do**:
  - Do not modify any references
  - Do not cache usage permanently

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `deep`
    - Reason: Complex counting across multiple policy types
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7-8, 10)
  - **Blocks**: Migration logic
  - **Blocked By**: Tasks 7 (discovery), 11-12 (policy fetching)

  **References**:
  - **Pattern References**: None yet (first implementation)
  - **External References**: 
    - Official docs: `https://panos-python.readthedocs.io/` - Security policy API

  **Acceptance Criteria**:
  - [ ] `src/services/usage.py` created
  - [ ] Usage counting in security policies
  - [ ] Usage counting in service groups
  - [ ] Aggregated total usage
  - [ ] Per-policy breakdown

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test usage counting
    Tool: Bash (Python)
    Preconditions: usage.py exists, mock policies available
    Steps:
      1. Run: python3 -c "from src.services.usage import UsageCounter; from unittest.mock import Mock; counter = UsageCounter(Mock()); usage = counter.count_all(); print(usage)"
      2. Verify usage counts per service
    Expected Result: Usage count dictionary
    Failure Indicators: Wrong counts or exception
    Evidence: .sisyphus/evidence/task-9-usage.py

  Scenario: Test policy breakdown
    Tool: Bash
    Preconditions: Usage exists
    Steps:
      1. Run: python3 -c "from src.services.usage import UsageCounter; from unittest.mock import Mock; counter = UsageCounter(Mock()); breakdown = counter.get_policy_breakdown(); print(breakdown)"
    Expected Result: Per-policy usage breakdown
    Failure Indicators: Missing policy data
    Evidence: .sisyphus/evidence/task-9-breakdown.txt
  ```

  **Commit**: YES
  - Message: `feat: add usage counting algorithm`
  - Files: `src/services/usage.py`

---

- [ ] 10. Tie-breaking logic

  **What to do**:
  - Create `src/services/tiebreaker.py` with tie-breaking rules
  - Implement alphabetical ordering for equal usage
  - Handle edge cases (zero usage, single service)
  - Add deterministic selection
  - Include tie-breaking report

  **Must NOT do**:
  - Do not use random selection
  - Do not use creation time (not tracked in PanOS)

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Simple alphabetical comparison
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7-9)
  - **Blocks**: Migration logic
  - **Blocked By**: Tasks 8 (duplicates), 9 (usage)

  **References**:
  - **Pattern References**: Standard sorting patterns
  - **External References**: 
    - Official docs: `https://docs.python.org/3/library/operator.html` - Comparison operators

  **Acceptance Criteria**:
  - [ ] `src/services/tiebreaker.py` created
  - [ ] Alphabetical tie-breaking implemented
  - [ ] Edge case handling (zero usage, single service)
  - [ ] Deterministic selection
  - [ ] Tie-breaking report

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test alphabetical tie-breaking
    Tool: Bash (Python)
    Preconditions: tiebreaker.py exists, mock services available
    Steps:
      1. Run: python3 -c "from src.services.tiebreaker import TieBreaker; from unittest.mock import Mock; tb = TieBreaker(Mock()); winner = tb.select_winner(['443-2', '443-1'], [10, 10]); print(winner)"
      2. Verify '443-1' selected (alphabetically first)
    Expected Result: '443-1' selected
    Failure Indicators: Wrong service selected
    Evidence: .sisyphus/evidence/task-10-tiebreak.py

  Scenario: Test edge cases
    Tool: Bash
    Preconditions: TieBreaker exists
    Steps:
      1. Run: python3 -c "from src.services.tiebreaker import TieBreaker; from unittest.mock import Mock; tb = TieBreaker(Mock()); single = tb.select_winner(['only'], [5]); print(single)"
    Expected Result: 'only' selected
    Failure Indicators: Exception or wrong selection
    Evidence: .sisyphus/evidence/task-10-edge-cases.txt
  ```

  **Commit**: YES
  - Message: `feat: add tie-breaking logic`
  - Files: `src/services/tiebreaker.py`

---

- [ ] 11. Security policy fetcher

  **What to do**:
  - Create `src/policies/security.py` with security policy fetching
  - Implement method to fetch all security policies
  - Extract service references from policies
  - Handle policy structure variations
  - Include error handling

  **Must NOT do**:
  - Do not modify policies during fetch
  - Do not cache policies permanently

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `unspecified-high`
    - Reason: API integration with complex data structures
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 12-14)
  - **Blocks**: Migration logic
  - **Blocked By**: Task 7 (discovery), Tasks 1-5 (infrastructure)

  **References**:
  - **Pattern References**: None yet (first implementation)
  - **External References**: 
    - Official docs: `https://panos-python.readthedocs.io/` - Security policy API

  **Acceptance Criteria**:
  - [ ] `src/policies/security.py` created
  - [ ] Fetch all security policies method
  - [ ] Service reference extraction
  - [ ] Policy structure handling
  - [ ] Error handling

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test security policy fetch
    Tool: Bash (Python)
    Preconditions: security.py exists, mock connection available
    Steps:
      1. Run: python3 -c "from src.policies.security import SecurityPolicyFetcher; from unittest.mock import Mock; fetcher = SecurityPolicyFetcher(Mock()); policies = fetcher.fetch_all(); print(len(policies))"
      2. Verify policies returned
    Expected Result: List of security policies
    Failure Indicators: Empty list or exception
    Evidence: .sisyphus/evidence/task-11-security-policies.py

  Scenario: Test reference extraction
    Tool: Bash
    Preconditions: Policies exist
    Steps:
      1. Run: python3 -c "from src.policies.security import SecurityPolicyFetcher; from unittest.mock import Mock; fetcher = SecurityPolicyFetcher(Mock()); refs = fetcher.extract_service_refs(); print(refs)"
    Expected Result: List of service references
    Failure Indicators: Missing references
    Evidence: .sisyphus/evidence/task-11-refs.txt
  ```

  **Commit**: YES
  - Message: `feat: add security policy fetcher`
  - Files: `src/policies/security.py`

---

- [ ] 12. Service group fetcher

  **What to do**:
  - Create `src/policies/service_groups.py` with service group fetching
  - Implement method to fetch all service groups
  - Extract service members from groups
  - Handle nested group references
  - Include error handling

  **Must NOT do**:
  - Do not modify groups during fetch
  - Do not cache groups permanently

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `unspecified-high`
    - Reason: API integration with nested structures
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 11, 13-14)
  - **Blocks**: Migration logic
  - **Blocked By**: Task 7 (discovery), Tasks 1-5 (infrastructure)

  **References**:
  - **Pattern References**: None yet (first implementation)
  - **External References**: 
    - Official docs: `https://panos-python.readthedocs.io/` - Service group API

  **Acceptance Criteria**:
  - [ ] `src/policies/service_groups.py` created
  - [ ] Fetch all service groups method
  - [ ] Service member extraction
  - [ ] Nested group handling
  - [ ] Error handling

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test service group fetch
    Tool: Bash (Python)
    Preconditions: service_groups.py exists, mock connection available
    Steps:
      1. Run: python3 -c "from src.policies.service_groups import ServiceGroupFetcher; from unittest.mock import Mock; fetcher = ServiceGroupFetcher(Mock()); groups = fetcher.fetch_all(); print(len(groups))"
      2. Verify groups returned
    Expected Result: List of service groups
    Failure Indicators: Empty list or exception
    Evidence: .sisyphus/evidence/task-12-groups.py

  Scenario: Test member extraction
    Tool: Bash
    Preconditions: Groups exist
    Steps:
      1. Run: python3 -c "from src.policies.service_groups import ServiceGroupFetcher; from unittest.mock import Mock; fetcher = ServiceGroupFetcher(Mock()); members = fetcher.extract_members(); print(members)"
    Expected Result: List of service members
    Failure Indicators: Missing members
    Evidence: .sisyphus/evidence/task-12-members.txt
  ```

  **Commit**: YES
  - message: `feat: add service group fetcher`
  - Files: `src/policies/service_groups.py`

---

- [ ] 13. Reference migration logic

  **What to do**:
  - Create `src/policies/migration.py` with reference migration
  - Implement updating security policy references
  - Implement updating service group references
  - Track all migrated references
  - Include rollback information

  **Must NOT do**:
  - Do not commit changes without --commit flag
  - Do not delete duplicates yet

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `deep`
    - Reason: Complex migration with rollback tracking
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 11-12, 14)
  - **Blocks**: Task 15-16 (orchestration)
  - **Blocked By**: Tasks 8-10 (duplicates, usage, tiebreaker), Tasks 11-12 (fetchers)

  **References**:
  - **Pattern References**: None yet (first implementation)
  - **External References**: 
    - Official docs: `https://panos-python.readthedocs.io/` - PUT operations for updates

  **Acceptance Criteria**:
  - [ ] `src/policies/migration.py` created
  - [ ] Security policy reference updates
  - [ ] Service group reference updates
  - [ ] Migration tracking
  - [ ] Rollback information

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test policy reference migration
    Tool: Bash (Python)
    Preconditions: migration.py exists, mock connection available
    Steps:
      1. Run: python3 -c "from src.policies.migration import ReferenceMigrator; from unittest.mock import Mock; migrator = ReferenceMigrator(Mock(), dry_run=True); result = migrator.migrate_policy_refs(); print(result)"
      2. Verify migration tracked without actual changes
    Expected Result: Migration report without changes
    Failure Indicators: Actual changes made or exception
    Evidence: .sisyphus/evidence/task-13-migrate-policy.py

  Scenario: Test group reference migration
    Tool: Bash
    Preconditions: Migrator exists
    Steps:
      1. Run: python3 -c "from src.policies.migration import ReferenceMigrator; from unittest.mock import Mock; migrator = ReferenceMigrator(Mock(), dry_run=True); result = migrator.migrate_group_refs(); print(result)"
    Expected Result: Migration report without changes
    Failure Indicators: Actual changes made
    Evidence: .sisyphus/evidence/task-13-migrate-groups.txt
  ```

  **Commit**: YES
  - Message: `feat: add reference migration logic`
  - Files: `src/policies/migration.py`

---

- [ ] 14. Service deletion logic

  **What to do**:
  - Create `src/services/deletion.py` with service deletion
  - Implement safe deletion of duplicate services
  - Verify no active references before deletion
  - Include deletion confirmation
  - Add rollback tracking

  **Must NOT do**:
  - Do not delete services with active references
  - Do not delete without --commit flag

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `deep`
    - Reason: Critical operation with safety checks
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 11-13)
  - **Blocks**: Task 15-16 (orchestration)
  - **Blocked By**: Tasks 8-10 (duplicates, usage, tiebreaker), Task 13 (migration)

  **References**:
  - **Pattern References**: None yet (first implementation)
  - **External References**: 
    - Official docs: `https://panos-python.readthedocs.io/` - DELETE operations

  **Acceptance Criteria**:
  - [ ] `src/services/deletion.py` created
  - [ ] Safe deletion with reference check
  - [ ] Confirmation before deletion
  - [ ] Rollback tracking
  - [ ] No deletion without --commit flag

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test safe deletion
    Tool: Bash (Python)
    Preconditions: deletion.py exists, mock connection available
    Steps:
      1. Run: python3 -c "from src.services.deletion import ServiceDeleter; from unittest.mock import Mock; deleter = ServiceDeleter(Mock(), dry_run=True); result = deleter.delete_duplicates(); print(result)"
      2. Verify deletion tracked without actual changes
    Expected Result: Deletion report without changes
    Failure Indicators: Actual deletion or exception
    Evidence: .sisyphus/evidence/task-14-delete.py

  Scenario: Test reference check
    Tool: Bash
    Preconditions: Deleter exists
    Steps:
      1. Run: python3 -c "from src.services.deletion import ServiceDeleter; from unittest.mock import Mock; deleter = ServiceDeleter(Mock(), dry_run=True); result = deleter.delete_with_refs(); print(result)"
    Expected Result: Error for service with references
    Failure Indicators: Service deleted with refs
    Evidence: .sisyphus/evidence/task-14-ref-check.txt
  ```

  **Commit**: YES
  - Message: `feat: add service deletion logic`
  - Files: `src/services/deletion.py`

---

- [ ] 15. Main CLI script integration

  **What to do**:
  - Create `src/duplicate_service_cleanup.py` main entry point
  - Integrate all modules into single workflow
  - Implement main execution flow
  - Add progress reporting
  - Include final summary report

  **Must NOT do**:
  - Do not skip any safety checks
  - Do not bypass dry-run mode

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `deep`
    - Reason: Complex orchestration of all modules
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (sequential after Wave 3)
  - **Blocks**: Tasks 16-17, 21-23
  - **Blocked By**: Tasks 1-14 (all modules)

  **References**:
  - **Pattern References**: None yet (first implementation)
  - **External References**: 
    - Official docs: Standard Python CLI patterns

  **Acceptance Criteria**:
  - [ ] `src/duplicate_service_cleanup.py` created
  - [ ] All modules integrated
  - [ ] Main execution flow working
  - [ ] Progress reporting
  - [ ] Final summary report

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test CLI execution dry-run
    Tool: interactive_bash (tmux)
    Preconditions: Main script exists, mock connection available
    Steps:
      1. Run: python3 -m src.duplicate_service_cleanup --panorama-ip 1.2.3.4 --username admin --password test --dry-run
      2. Verify no changes made, report generated
    Expected Result: Dry-run report with duplicates found
    Failure Indicators: Changes made or exception
    Evidence: .sisyphus/evidence/task-15-cli-dryrun.txt

  Scenario: Test commit mode
    Tool: Bash
    Preconditions: Script exists, test Panorama available
    Steps:
      1. Run: python3 -m src.duplicate_service_cleanup --panorama-ip 1.2.3.4 --username admin --password test --commit
      2. Verify changes applied, report generated
    Expected Result: Duplicates migrated and deleted
    Failure Indicators: Errors or incomplete migration
    Evidence: .sisyphus/evidence/task-15-cli-commit.txt
  ```

  **Commit**: YES
  - Message: `feat: integrate main CLI script`
  - Files: `src/duplicate_service_cleanup.py`

---

- [ ] 16. Rollback functionality

  **What to do**:
  - Create `src/utils/rollback.py` with rollback operations
  - Implement restoration from backup files
  - Support partial rollback
  - Include rollback verification
  - Add rollback reporting

  **Must NOT do**:
  - Do not overwrite current state without confirmation
  - Do not rollback without backup files

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `deep`
    - Reason: Critical recovery operation
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 15, 17)
  - **Blocks**: Task 21-23 (testing)
  - **Blocked By**: Tasks 1-14 (all modules)

  **References**:
  - **Pattern References**: None yet (first implementation)
  - **External References**: 
    - Official docs: Standard backup/restore patterns

  **Acceptance Criteria**:
  - [ ] `src/utils/rollback.py` created
  - [ ] Restoration from backup files
  - [ ] Partial rollback support
  - [ ] Rollback verification
  - [ ] Rollback reporting

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test rollback execution
    Tool: Bash (Python)
    Preconditions: rollback.py exists, backup files available
    Steps:
      1. Run: python3 -c "from src.utils.rollback import Rollback; from unittest.mock import Mock; rb = Rollback(Mock()); result = rb.rollback_all(); print(result)"
      2. Verify rollback executed
    Expected Result: Rollback completed successfully
    Failure Indicators: Rollback failed or exception
    Evidence: .sisyphus/evidence/task-16-rollback.py

  Scenario: Test partial rollback
    Tool: Bash
    Preconditions: Rollback exists
    Steps:
      1. Run: python3 -c "from src.utils.rollback import Rollback; from unittest.mock import Mock; rb = Rollback(Mock()); result = rb.rollback_specific('policy-123'); print(result)"
    Expected Result: Specific policy rolled back
    Failure Indicators: Wrong policy or exception
    Evidence: .sisyphus/evidence/task-16-partial.txt
  ```

  **Commit**: YES
  - Message: `feat: add rollback functionality`
  - Files: `src/utils/rollback.py`

---

- [ ] 17. Report generation

  **What to do**:
  - Create `src/utils/report.py` with report generation
  - Implement HTML report format
  - Implement JSON report format
  - Include summary statistics
  - Add detailed action log

  **Must NOT do**:
  - Do not include sensitive data in reports
  - Do not log passwords

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Standard report generation
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 15-16)
  - **Blocks**: Task 23 (documentation)
  - **Blocked By**: Tasks 1-16 (all modules)

  **References**:
  - **Pattern References**: None yet (first implementation)
  - **External References**: 
    - Official docs: `https://docs.python.org/3/library/json.html`, HTML generation patterns

  **Acceptance Criteria**:
  - [ ] `src/utils/report.py` created
  - [ ] HTML report generation
  - [ ] JSON report generation
  - [ ] Summary statistics
  - [ ] Detailed action log

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test HTML report generation
    Tool: Bash
    Preconditions: report.py exists
    Steps:
      1. Run: python3 -c "from src.utils.report import ReportGenerator; gen = ReportGenerator(); gen.generate_html('/tmp/report.html')"
      2. Check HTML file created and valid
    Expected Result: Valid HTML report file
    Failure Indicators: Invalid HTML or missing file
    Evidence: .sisyphus/evidence/task-17-html-report.html

  Scenario: Test JSON report generation
    Tool: Bash
    Preconditions: ReportGenerator exists
    Steps:
      1. Run: python3 -c "from src.utils.report import ReportGenerator; import json; gen = ReportGenerator(); data = gen.generate_json(); print(json.dumps(data, indent=2))"
    Expected Result: Valid JSON output
    Failure Indicators: Invalid JSON
    Evidence: .sisyphus/evidence/task-17-json-report.json
  ```

  **Commit**: YES
  - Message: `feat: add report generation`
  - Files: `src/utils/report.py`

---

- [ ] 18. Pytest configuration + fixtures

  **What to do**:
  - Create `pytest.ini` configuration file
  - Create `tests/conftest.py` with shared fixtures
  - Set up mock PanOS connection fixtures
  - Configure test discovery patterns
  - Add coverage configuration

  **Must NOT do**:
  - Do not add test implementations yet
  - Do not use real PanOS connections

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Standard pytest setup
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 19-20)
  - **Blocks**: All tests
  - **Blocked By**: Tasks 1-17 (all implementation)

  **References**:
  - **Pattern References**: Standard pytest patterns
  - **External References**: 
    - Official docs: `https://docs.pytest.org/` - Configuration and fixtures

  **Acceptance Criteria**:
  - [ ] `pytest.ini` created
  - [ ] `tests/conftest.py` with fixtures
  - [ ] Mock PanOS connection fixtures
  - [ ] Test discovery configured
  - [ ] Coverage configuration

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test pytest configuration
    Tool: Bash
    Preconditions: pytest.ini exists
    Steps:
      1. Run: pytest --collect-only
      2. Verify test discovery works
    Expected Result: Tests discovered without errors
    Failure Indicators: No tests found or configuration error
    Evidence: .sisyphus/evidence/task-18-pytest-config.txt

  Scenario: Test mock fixture
    Tool: Bash
    Preconditions: conftest.py exists
    Steps:
      1. Run: python3 -c "import sys; sys.path.insert(0, '.'); from tests.conftest import mock_panos_connection; conn = mock_panos_connection(); print(type(conn))"
    Expected Result: Mock connection object
    Failure Indicators: Exception or wrong type
    Evidence: .sisyphus/evidence/task-18-mock-fixture.py
  ```

  **Commit**: YES
  - Message: `test: add pytest configuration`
  - Files: `pytest.ini`, `tests/conftest.py`

---

- [ ] 19. Mock PanOS SDK setup

  **What to do**:
  - Create `tests/mocks/panos_mock.py` with comprehensive mocks
  - Mock all PanOS SDK classes and methods
  - Implement realistic response data
  - Add error simulation
  - Create mock service/policy data

  **Must NOT do**:
  - Do not make real API calls
  - Do not use actual credentials

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `deep`
    - Reason: Comprehensive mocking of external SDK
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 18, 20)
  - **Blocks**: All integration tests
  - **Blocked By**: Tasks 1-17 (all implementation)

  **References**:
  - **Pattern References**: Standard unittest.mock patterns
  - **External References**: 
    - Official docs: `https://docs.python.org/3/library/unittest.mock.html`

  **Acceptance Criteria**:
  - [ ] `tests/mocks/panos_mock.py` created
  - [ ] All PanOS SDK classes mocked
  - [ ] Realistic response data
  - [ ] Error simulation
  - [ ] Mock service/policy data

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Test mock SDK
    Tool: Bash (Python)
    Preconditions: panos_mock.py exists
    Steps:
      1. Run: python3 -c "from tests.mocks.panos_mock import MockPanOS; m = MockPanOS(); services = m.get_services(); print(len(services))"
      2. Verify mock returns data
    Expected Result: Mock services list
    Failure Indicators: Exception or empty list
    Evidence: .sisyphus/evidence/task-19-mock-sdk.py

  Scenario: Test error simulation
    Tool: Bash
    Preconditions: MockPanOS exists
    Steps:
      1. Run: python3 -c "from tests.mocks.panos_mock import MockPanOS; m = MockPanOS(); m.simulate_error(); m.get_services()"
    Expected Result: Error raised as expected
    Failure Indicators: No error or wrong error
    Evidence: .sisyphus/evidence/task-19-error-sim.txt
  ```

  **Commit**: YES
  - Message: `test: add mock PanOS SDK`
  - Files: `tests/mocks/panos_mock.py`

---

- [ ] 20. Unit tests for all modules

  **What to do**:
  - Create unit tests for each module (tasks 1-17)
  - Test service discovery
  - Test duplicate detection
  - Test usage counting
  - Test migration logic
  - Test deletion logic
  - Test rollback functionality
  - Test report generation

  **Must NOT do**:
  - Do not skip any module
  - Do not use real PanOS connections

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `unspecified-high`
    - Reason: Comprehensive test coverage
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 18-19)
  - **Blocks**: Integration tests
  - **Blocked By**: Tasks 1-17 (all implementation), Tasks 18-19 (test setup)

  **References**:
  - **Pattern References**: Standard pytest test patterns
  - **External References**: 
    - Official docs: `https://docs.pytest.org/` - Writing test code

  **Acceptance Criteria**:
  - [ ] Unit tests for all modules
  - [ ] Service discovery tests
  - [ ] Duplicate detection tests
  - [ ] Usage counting tests
  - [ ] Migration logic tests
  - [ ] Deletion logic tests
  - [ ] Rollback tests
  - [ ] Report tests

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Run unit tests
    Tool: Bash
    Preconditions: Tests exist
    Steps:
      1. Run: pytest tests/unit/ -v
      2. Verify all tests pass
    Expected Result: All tests pass
    Failure Indicators: Test failures
    Evidence: .sisyphus/evidence/task-20-unit-tests.txt

  Scenario: Test coverage
    Tool: Bash
    Preconditions: Tests exist
    Steps:
      1. Run: pytest tests/unit/ --cov=src --cov-report=html
      2. Check coverage report
    Expected Result: High coverage (>80%)
    Failure Indicators: Low coverage
    Evidence: .sisyphus/evidence/task-20-coverage/index.html
  ```

  **Commit**: YES
  - Message: `test: add unit tests for all modules`
  - Files: `tests/unit/*.py`

---

- [ ] 21. Integration tests

  **What to do**:
  - Create `tests/integration/` with integration test suite
  - Test full workflow end-to-end
  - Test module interactions
  - Test error scenarios
  - Test rollback scenarios

  **Must NOT do**:
  - Do not use real Panorama instance
  - Do not make actual API calls

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `deep`
    - Reason: Complex integration testing
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 6 (with Task 22)
  - **Blocks**: Task 23, Final wave
  - **Blocked By**: Tasks 1-20 (all implementation and unit tests)

  **References**:
  - **Pattern References**: Standard pytest integration patterns
  - **External References**: 
    - Official docs: `https://docs.pytest.org/` - Integration testing

  **Acceptance Criteria**:
  - [ ] Integration tests in `tests/integration/`
  - [ ] Full workflow tests
  - [ ] Module interaction tests
  - [ ] Error scenario tests
  - [ ] Rollback scenario tests

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Run integration tests
    Tool: Bash
    Preconditions: Integration tests exist
    Steps:
      1. Run: pytest tests/integration/ -v
      2. Verify all tests pass
    Expected Result: All integration tests pass
    Failure Indicators: Test failures
    Evidence: .sisyphus/evidence/task-21-integration-tests.txt
  ```

  **Commit**: YES
  - Message: `test: add integration tests`
  - Files: `tests/integration/*.py`

---

- [ ] 22. End-to-end QA scenarios

  **What to do**:
  - Create comprehensive QA scenarios for manual verification
  - Document test procedures
  - Include sample data sets
  - Create verification checklists
  - Add success criteria

  **Must NOT do**:
  - Do not skip any scenarios
  - Do not use production data

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `unspecified-high`
    - Reason: Comprehensive QA documentation
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 6 (with Task 21)
  - **Blocks**: Final wave
  - **Blocked By**: Tasks 1-21 (all implementation and tests)

  **References**:
  - **Pattern References**: Standard QA documentation patterns
  - **External References**: 
    - Official docs: QA best practices

  **Acceptance Criteria**:
  - [ ] QA scenarios documented
  - [ ] Test procedures created
  - [ ] Sample datasets defined
  - [ ] Verification checklists
  - [ ] Success criteria defined

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Execute QA scenarios
    Tool: interactive_bash (tmux)
    Preconditions: QA scenarios documented
    Steps:
      1. Run: python3 -m src.duplicate_service_cleanup --panorama-ip 1.2.3.4 --username admin --password test --dry-run --report /tmp/qa-report.html
      2. Verify report generated
      3. Check all scenarios pass
    Expected Result: All QA scenarios pass
    Failure Indicators: Any scenario fails
    Evidence: .sisyphus/evidence/task-22-qa-scenarios.txt
  ```

  **Commit**: YES
  - Message: `test: add end-to-end QA scenarios`
  - Files: `tests/qa/*.md`

---

- [ ] 23. Documentation + README

  **What to do**:
  - Create comprehensive README.md
  - Document installation steps
  - Document usage examples
  - Document configuration options
  - Document troubleshooting guide
  - Add code documentation (docstrings)

  **Must NOT do**:
  - Do not document unimplemented features
  - Do not include sensitive information

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `writing`
    - Reason: Documentation creation
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 6 (with Tasks 21-22)
  - **Blocks**: None (final task)
  - **Blocked By**: Tasks 1-22 (all implementation and testing)

  **References**:
  - **Pattern References**: Standard README patterns
  - **External References**: 
    - Official docs: Markdown best practices

  **Acceptance Criteria**:
  - [ ] Comprehensive README.md
  - [ ] Installation steps documented
  - [ ] Usage examples provided
  - [ ] Configuration options documented
  - [ ] Troubleshooting guide
  - [ ] Code docstrings added

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Verify documentation
    Tool: Bash
    Preconditions: README.md exists
    Steps:
      1. Run: cat README.md
      2. Verify all sections present
      3. Check markdown validity
    Expected Result: Complete, valid documentation
    Failure Indicators: Missing sections or invalid markdown
    Evidence: .sisyphus/evidence/task-23-readme.md
  ```

  **Commit**: YES
  - Message: `docs: add comprehensive documentation`
  - Files: `README.md`, docstrings in all modules

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Rejection → fix → re-run.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `tsc --noEmit` + linter + `bun test`. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names (data/result/item/temp).
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill if UI)
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration (features working together, not isolation). Test edge cases: empty state, invalid input, rapid actions. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination: Task N touching Task M's files. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **1**: `feat: initial project scaffolding` — requirements.txt, .gitignore, README.md, directory structure
- **2**: `feat: add logging utility` — src/utils/logger.py
- **3**: `feat: add CLI argument parsing` — src/utils/config.py
- **4**: `feat: add PanOS connection manager` — src/utils/connection.py
- **5**: `feat: add backup utility` — src/utils/backup.py
- **6**: `feat: add service data models` — src/models/service.py
- **7**: `feat: add service discovery module` — src/services/discovery.py
- **8**: `feat: add duplicate detection logic` — src/services/duplicates.py
- **9**: `feat: add usage counting algorithm` — src/services/usage.py
- **10**: `feat: add tie-breaking logic` — src/services/tiebreaker.py
- **11**: `feat: add security policy fetcher` — src/policies/security.py
- **12**: `feat: add service group fetcher` — src/policies/service_groups.py
- **13**: `feat: add reference migration logic` — src/policies/migration.py
- **14**: `feat: add service deletion logic` — src/services/deletion.py
- **15**: `feat: integrate main CLI script` — src/duplicate_service_cleanup.py
- **16**: `feat: add rollback functionality` — src/utils/rollback.py
- **17**: `feat: add report generation` — src/utils/report.py
- **18**: `test: add pytest configuration` — pytest.ini, tests/conftest.py
- **19**: `test: add mock PanOS SDK` — tests/mocks/panos_mock.py
- **20**: `test: add unit tests for all modules` — tests/unit/*.py
- **21**: `test: add integration tests` — tests/integration/*.py
- **22**: `test: add end-to-end QA scenarios` — tests/qa/*.md
- **23**: `docs: add comprehensive documentation` — README.md, docstrings

---

## Success Criteria

### Verification Commands
```bash
# Run all tests
pytest tests/ -v

# Run dry-run mode
python3 -m src.duplicate_service_cleanup --panorama-ip <IP> --username <USER> --dry-run

# Run commit mode (with caution!)
python3 -m src.duplicate_service_cleanup --panorama-ip <IP> --username <USER> --commit

# Generate report
python3 -m src.duplicate_service_cleanup --panorama-ip <IP> --username <USER> --report /path/to/report.html
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Evidence files collected
- [ ] Final verification wave approved