"""
Duplicate Service Cleanup Tool - Main CLI Entry Point

Identifies and cleans up duplicate services in Palo Alto Panorama.

Usage:
    python3 -m src.duplicate_service_cleanup [OPTIONS]

Options:
    --panorama-ip IP     Panorama manager IP address (required)
    --username USER      Panorama username (required)
    --password PASS      Panorama password (optional, will prompt if not provided)
    --dry-run            Preview mode - no changes made (default)
    --commit             Execute changes - overrides dry-run mode
    --backup-dir DIR     Directory for backup files (default: ./backups)
    --log-level LEVEL    Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
    --log-file FILE      Path to log file (optional)
    --json-logging       Use JSON format for file logging
    --config FILE        Path to configuration file (YAML/JSON)

Examples:
    # Preview mode (default)
    python3 -m src.duplicate_service_cleanup --panorama-ip 1.2.3.4 --username admin

    # Commit mode (makes actual changes)
    python3 -m src.duplicate_service_cleanup --panorama-ip 1.2.3.4 --username admin --commit

See README.md for more details.
"""
import sys
import getpass
from src.utils.config import parse_args


def main() -> int:
    """Main entry point."""
    try:
        config = parse_args()
        
        # Get password if not provided
        if not config.password:
            config.password = getpass.getpass(prompt="Enter Panorama password: ")
        
        print(f"Dry-run mode: {config.dry_run}")
        print(f"Panorama IP: {config.panorama_ip}")
        print(f"Username: {config.username}")
        print(f"Backup directory: {config.backup_dir}")
        
        # If in commit mode, warn user
        if not config.dry_run:
            print("\nWARNING: Commit mode enabled - changes will be applied!")
            print("Press Ctrl+C to cancel or wait 5 seconds to continue...")
            import time
            time.sleep(5)
        
        print("\n=== Duplicate Service Cleanup Tool ===")
        print("Connecting to Panorama...")
        
        # Connect to Panorama
        from src.utils.connection import PanOSConnection
        connection = PanOSConnection(
            hostname=config.panorama_ip,
            username=config.username,
            password=config.password,
            port=443,
            use_ssl=True,
            verify_ssl=False
        )
        connection.connect()
        print("Connected successfully!")
        
        # Discover services
        print("\nFetching services from Panorama...")
        from src.services.discovery import ServiceDiscovery
        discovery = ServiceDiscovery(connection)
        services = discovery.fetch_all()
        print(f"Found {len(services)} total services")
        
        # Find duplicates
        print("\nAnalyzing for duplicates...")
        from src.services.duplicates import find_duplicates, generate_duplicate_report
        duplicate_groups = find_duplicates(services)
        print(generate_duplicate_report(services))
        
        # If no duplicates, exit
        if not duplicate_groups:
            print("\nNo duplicate services found. Nothing to clean up.")
            connection.disconnect()
            print("\nCleanup analysis complete!")
            return 0
        
        # --- DRY-RUN MODE REPORT (WHAT WOULD BE DONE) ---
        print("\n" + "=" * 60)
        print("DRY-RUN CLEANUP PLAN")
        print("=" * 60)
        
        # Step 1: Count usage for each service
        print("\n--- Step 1: Counting Service Usage ---")
        from src.services.usage import UsageCounter
        from src.models.service import ServiceGroup
        
        # Fetch security policies (always use live connection)
        print("\nFetching security policies...")
        from src.policies.security import SecurityPolicyFetcher
        policy_fetcher = SecurityPolicyFetcher(connection)
        security_policies = policy_fetcher.fetch_all()
        print(f"Found {len(security_policies)} security policies")
        
        # Fetch NAT policies (always use live connection)
        print("\nFetching NAT policies...")
        from src.policies.nat import NatPolicyFetcher
        nat_fetcher = NatPolicyFetcher(connection)
        nat_policies = nat_fetcher.fetch_all()
        print(f"Found {len(nat_policies)} NAT policies")
        
        # Combine all policies for migration
        policies = security_policies + nat_policies
        print(f"Total policies: {len(policies)}")
        
        # Print all policies being considered for duplicate service detection
        print("\n--- All Policies Considered for Duplicate Service Detection ---")
        print(f"{'Policy Name':<50} {'Type':<20} {'Location':<30} {'Services'}")
        print("-" * 150)
        for policy in policies:
            policy_name = policy.get('name', 'Unknown')[:48]
            policy_type = policy.get('type', 'unknown')[:18]
            location = policy.get('location', policy.get('device_group', 'N/A'))[:28]
            
            # Get services - handle both list and single service (for NAT)
            services = policy.get('services', [])
            if not isinstance(services, list):
                services = [services] if services else []
            
            # For NAT policies, also check 'service' field
            if not services and 'service' in policy:
                services = [policy['service']]
            
            services_str = ', '.join(services) if services else 'any'
            if len(services_str) > 50:
                services_str = services_str[:47] + '...'
            
            print(f"{policy_name:<50} {policy_type:<20} {location:<30} {services_str}")
        print(f"\nTotal policies with services: {sum(1 for p in policies if p.get('services') or p.get('service'))}")
        print("-" * 150)
        
        # Fetch service groups (always use live connection)
        print("\nFetching service groups...")
        from src.policies.service_groups import ServiceGroupFetcher
        group_fetcher = ServiceGroupFetcher(connection)
        service_groups = group_fetcher.fetch_all()
        print(f"Found {len(service_groups)} service groups")
        
        # Convert ServiceGroup objects to dicts for migration
        service_groups_dicts = [sg.to_dict() for sg in service_groups]
        
        # Count usage (security policies + NAT policies)
        usage_counter = UsageCounter(policies, service_groups)
        usage_counts = usage_counter.count_all()
        print(f"Counted usage for {len(usage_counts)} services across security and NAT policies")
        
        # Step 2: Select winners for each duplicate group
        print("\n--- Step 2: Selecting Winner Services ---")
        from src.services.tiebreaker import TieBreaker
        breaker = TieBreaker()
        winners = {}
        
        # Apply limit filter if specified
        groups_to_process = duplicate_groups
        if config.limit_duplicates:
            groups_to_process = duplicate_groups[:config.limit_duplicates]
            print(f"  Processing {len(groups_to_process)} of {len(duplicate_groups)} duplicate groups (limited)")
        
        for group in groups_to_process:
            service_names = [s.name for s in group.services]
            usage_list = [usage_counts.get(name, 0) for name in service_names]
            winner = breaker.select_winner(service_names, usage_list)
            winners[group.key] = winner
            # losers = [s for s in group.services if s.name != winner]
            # print(f"  Group '{group.key}':")
            # print(f"    Winner: {winner}")
            # print(f"    Duplicates to update/delete:")
            # for loser in losers:
            #     print(f"      - {loser.name} ({loser.device_group})")
        
        print(f"  Selected winners for {len(winners)} duplicate groups")
        
        # === CREATE BACKUP REPORT ===
        print("\n--- Creating Backup Report ---")
        from src.utils.backup import BackupManager
        backup_manager = BackupManager(config.backup_dir)
        report_path = backup_manager.save_duplicate_report(duplicate_groups, policies, service_groups, winners)
        print(f"✓ Backup report saved: {report_path}")
        
        # Step 3: Migrate policy references
        print("\n--- Step 3: Migrating Policy References ---")
        from src.policies.migration import ReferenceMigrator
        
        # Build duplicate group mapping for migrator: {"key": [service_names]}
        dup_group_map = {g.key: [s.name for s in g.services] for g in duplicate_groups}
        
        migrator = ReferenceMigrator(
            connection=connection if not config.dry_run else None,
            dry_run=True,  # Always dry-run for reporting
            duplicate_groups=dup_group_map
        )
        
        policy_result = migrator.migrate_policy_refs(policies=policies)
        group_result = migrator.migrate_group_refs(groups=service_groups_dicts)
        
        print(f"  Policies with updated references: {policy_result.get('policies_updated', 0)}")
        print(f"  Service groups with updated members: {group_result.get('groups_updated', 0)}")
        
        # Save detailed policies-to-update report
        if policy_result.get('policies_updated', 0) > 0:
            policies_report_path = backup_manager.save_policies_to_update_report(policy_result)
            print(f"✓ Policies to update report saved: {policies_report_path}")
        
        # Step 4: Delete duplicates (dry-run)
        print("\n--- Step 4: Deleting Duplicate Services ---")
        from src.services.deletion import ServiceDeleter
        
        # Convert duplicate_groups to format deletion expects
        dup_services_map = {g.key: list(g.services) for g in duplicate_groups}
        
        deleter = ServiceDeleter(
            connection=connection if not config.dry_run else None,
            dry_run=True  # Always dry-run for reporting
        )
        
        del_result = deleter.delete_duplicates(
            duplicate_groups=dup_services_map,
            services_in_use=usage_counts,
            post_migration_usage=None
        )
        
        print(f"  Services to delete: {del_result.get('services_deleted', 0)}")
        print(f"  Services skipped: {del_result.get('services_skipped', 0)}")
        
        # Print final summary
        print("\n" + "=" * 60)
        print("DRY-RUN SUMMARY")
        print("=" * 60)
        print(f"Duplicate groups found: {len(duplicate_groups)}")
        print(f"Services selected as winners: {len(winners)}")
        print(f"Policies to update: {policy_result.get('policies_updated', 0)}")
        print(f"Service groups to update: {group_result.get('groups_updated', 0)}")
        print(f"Duplicate services to delete: {del_result.get('services_deleted', 0)}")
        print("=" * 60)
        print("")
        print("In commit mode, the script would:")
        print(f"  1. Update {policy_result.get('policies_updated', 0)} security policies")
        print(f"  2. Update {group_result.get('groups_updated', 0)} service groups")
        print(f"  3. Delete {del_result.get('services_deleted', 0)} duplicate services")
        print("  4. Keep the winner services")
        print("")
        print("(No actual changes will be made in dry-run mode)")
        print("")
        print("=" * 60)
        print("BACKUP REPORT")
        print("=" * 60)
        print(f"Report saved to: {report_path}")
        print("")
        print("This report contains:")
        print("  - All duplicate service groups with winners marked")
        print("  - Policies using winner services (no changes needed)")
        print("  - Policies to be modified on commit (using duplicates)")
        print("  - Service groups that contain duplicate services")
        print("")
        print("Review this report before running in commit mode.")
        print("=" * 60)
        
        # === COMMIT MODE EXECUTION ===
        if not config.dry_run:
            print("\n" + "=" * 60)
            print("COMMIT MODE - EXECUTING CHANGES")
            print("=" * 60)
            
            # Filter policies by type if specified
            policies_to_migrate = policies
            if config.policy_types:
                policies_to_migrate = [p for p in policies if p.get('type') in config.policy_types]
                print(f"\nFiltering policies by types: {', '.join(config.policy_types)}")
                print(f"  Policies to process: {len(policies_to_migrate)} of {len(policies)}")
            
            # Execute migrations with actual connection
            print("\n--- Executing Policy Migrations ---")
            migrator_commit = ReferenceMigrator(
                connection=connection,
                dry_run=False,
                duplicate_groups=dup_group_map
            )
            
            commit_policy_result = migrator_commit.migrate_policy_refs(policies=policies_to_migrate)
            commit_group_result = migrator_commit.migrate_group_refs(groups=service_groups_dicts)
            
            print(f"✓ Updated {commit_policy_result.get('policies_updated', 0)} policies")
            print(f"✓ Updated {commit_group_result.get('groups_updated', 0)} service groups")
            
            # Execute deletions
            print("\n--- Deleting Duplicate Services ---")
            deleter_commit = ServiceDeleter(
                connection=connection,
                dry_run=False
            )
            
            # Only delete duplicates from processed groups
            dup_services_to_delete = {g.key: list(g.services) for g in groups_to_process}
            
            commit_del_result = deleter_commit.delete_duplicates(
                duplicate_groups=dup_services_to_delete,
                services_in_use=usage_counts,
                post_migration_usage=None
            )
            
            print(f"✓ Deleted {commit_del_result.get('services_deleted', 0)} duplicate services")
            
            # Final commit summary
            print("\n" + "=" * 60)
            print("COMMIT SUMMARY")
            print("=" * 60)
            print(f"Duplicate groups processed: {len(groups_to_process)}")
            if config.limit_duplicates and len(groups_to_process) < len(duplicate_groups):
                print(f"  (Remaining: {len(duplicate_groups) - len(groups_to_process)})")
            print(f"Policies updated: {commit_policy_result.get('policies_updated', 0)}")
            if config.policy_types:
                print(f"  (Filtered by types: {', '.join(config.policy_types)})")
            print(f"Service groups updated: {commit_group_result.get('groups_updated', 0)}")
            print(f"Services deleted: {commit_del_result.get('services_deleted', 0)}")
            print("=" * 60)
            print("\n✓ Changes committed successfully!")
        
        connection.disconnect()
        print("\nCleanup analysis complete!")
        return 0
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())