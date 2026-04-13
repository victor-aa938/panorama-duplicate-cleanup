# Draft: Duplicate Service Cleanup Tool

## Requirements (confirmed)
- **Goal**: Create Python script to clean up duplicate services in Palo Alto Panorama
- **Tool**: Use pan-os-python SDK
- **Problem**: Duplicate services exist for same port/protocol (e.g., 443-1 and 443-2 both serve same purpose)
- **Strategy**: Keep the most-used service (appears in most service policies/service groups), update all references, delete duplicates

## Technical Decisions
- **SDK**: pan-os-python (Palo Alto Networks official SDK)
- **Approach**: 
  1. Discover all services
  2. Identify duplicates (same port + protocol)
  3. Count usage in security policies and service groups
  4. Keep most-used, migrate references, delete others

## Research Findings
- **PanOS SDK**: Available via Context7 library `/paloaltonetworks/pan.dev`
- **API Capabilities**: 
  - GET services endpoint
  - GET security policies
  - GET service groups
  - PUT/DELETE operations for updates
- **Key Endpoints**: Services, policies/firewall (security rules), service groups

## Decisions Made
- **Connection Method**: Panorama Manager (centralized) - connect to Panorama as single source of truth
- **Dry-run Mode**: YES - Preview mode required, needs --commit flag to execute changes
- **Tie-Breaking Strategy**: Keep alphabetically first (e.g., '443-1' over '443-2')
- **Service Group Cleanup**: Report but don't delete empty groups after migration
- **Automated Tests**: YES - TDD approach with pytest and mock PanOS connections
- **Risk Tolerance**: Conservative - backup policies, detailed logging, step-by-step confirmation, dry-run required

## Scope Boundaries
### INCLUDE:
- Service discovery and duplicate detection (same port + protocol)
- Usage counting in security policies
- Usage counting in service groups
- Reference migration (security policies + service groups)
- Duplicate service deletion
- Logging and reporting
- Backup creation before changes
- Rollback capability

### EXCLUDE:
- Application firewall rules (only security policies)
- NAT policies
- QoS policies
- Interface configuration changes
- Commit/push operations (handled separately)
- Empty service group deletion (only reporting)

## Test Strategy Decision
- **Infrastructure exists**: NO (empty project - will be set up)
- **Automated tests**: YES (TDD approach)
- **Framework**: pytest with unittest.mock for PanOS SDK mocking
- **Testing Strategy**:
  - Mock all PanOS SDK interactions
  - Test duplicate detection logic
  - Test usage counting algorithms
  - Test migration logic
  - Test tie-breaking scenarios
  - Test error handling
- **Agent-Executed QA**: Will include manual verification scenarios against test Panorama instance

## Risk Assessment
- **HIGH RISK**: Modifying security policies directly
- **Mitigation**: 
  - Dry-run mode strongly recommended
  - Backup policies before changes
  - Rollback plan needed
  - Thorough testing in non-production first