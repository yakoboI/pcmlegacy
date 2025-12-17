#!/usr/bin/env python
"""
Safe Deployment Script
Ensures database backup before deployment and safe migration
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask
from app import app, db
from utils.db_backup import backup_database, get_database_info


def safe_deploy():
    """Perform safe deployment with automatic backup"""
    print("=" * 60)
    print("SAFE DEPLOYMENT SCRIPT")
    print("=" * 60)
    
    with app.app_context():
        # Step 1: Check database status
        print("\n1. Checking database status...")
        db_info = get_database_info()
        
        if not db_info['exists']:
            print("⚠ Database file not found. Will be created on first run.")
        else:
            print(f"✓ Database found: {db_info['path']}")
            print(f"  Size: {db_info['size_formatted']}")
            print(f"  Last modified: {db_info['modified']}")
        
        # Step 2: Create backup before migration
        if db_info['exists']:
            print("\n2. Creating backup before migration...")
            try:
                backup_result = backup_database()
                print(f"✓ Backup created: {backup_result['backup_filename']}")
                print(f"  Size: {backup_result['size_formatted']}")
                print(f"  Location: {backup_result['backup_path']}")
            except Exception as e:
                print(f"✗ Backup failed: {e}")
                response = input("\n⚠ Backup failed! Continue anyway? (yes/no): ")
                if response.lower() != 'yes':
                    print("Deployment cancelled.")
                    return False
        
        # Step 3: Run safe migration
        print("\n3. Running database migration...")
        try:
            from utils.db_migrations import safe_migrate_database
            migration_result = safe_migrate_database()
            
            if migration_result['success']:
                print(f"✓ {migration_result['message']}")
                if migration_result.get('migrations_applied'):
                    print("\n  Applied migrations:")
                    for migration in migration_result['migrations_applied']:
                        print(f"    - {migration}")
            else:
                print(f"✗ Migration failed: {migration_result['message']}")
                return False
        except Exception as e:
            print(f"✗ Migration error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Step 4: Verify database
        print("\n4. Verifying database...")
        try:
            db_info_after = get_database_info()
            if db_info_after['exists']:
                print(f"✓ Database verified: {db_info_after['size_formatted']}")
            else:
                print("⚠ Database file not found after migration")
        except Exception as e:
            print(f"⚠ Verification warning: {e}")
        
        print("\n" + "=" * 60)
        print("✓ SAFE DEPLOYMENT COMPLETED")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Upload your code to the server")
        print("2. Run migrations on the server (they will be automatic)")
        print("3. Reload your web application")
        print("\n⚠ IMPORTANT: Keep your backup file safe!")
        
        return True


if __name__ == '__main__':
    success = safe_deploy()
    sys.exit(0 if success else 1)

