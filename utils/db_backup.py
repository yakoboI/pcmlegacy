"""
Database Backup and Restore Utility
Provides functions for backing up and restoring SQLite databases
"""
import os
import shutil
from datetime import datetime
from pathlib import Path
import sqlite3
from flask import current_app


def get_database_path():
    """Get the path to the database file"""
    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///pcm_store.db')
    
    if db_uri.startswith('sqlite:///'):
        # Extract database path
        db_path = db_uri.replace('sqlite:///', '')
        if db_path.startswith('/'):
            return db_path
        else:
            # Relative path - should be in instance/ directory
            instance_dir = Path(current_app.instance_path)
            return str(instance_dir / db_path)
    else:
        # Not SQLite - return None
        return None


def get_backup_directory():
    """Get or create the backup directory"""
    backup_dir = Path(current_app.instance_path) / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def format_file_size(size_bytes):
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def get_database_info():
    """Get database file information"""
    db_path = get_database_path()
    if not db_path or not os.path.exists(db_path):
        return {
            'exists': False,
            'path': db_path,
            'size': 0,
            'size_formatted': '0 B',
            'modified': None
        }
    
    stat = os.stat(db_path)
    return {
        'exists': True,
        'path': db_path,
        'size': stat.st_size,
        'size_formatted': format_file_size(stat.st_size),
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'tables': get_table_count(db_path)
    }


def get_table_count(db_path):
    """Get the number of tables in the database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        return len(tables)
    except Exception:
        return 0


def backup_database():
    """Create a backup of the database"""
    db_path = get_database_path()
    if not db_path or not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    backup_dir = get_backup_directory()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"pcm_store_backup_{timestamp}.db"
    backup_path = backup_dir / backup_filename
    
    try:
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        # Get backup file info
        backup_size = os.path.getsize(backup_path)
        
        return {
            'success': True,
            'backup_path': str(backup_path),
            'backup_filename': backup_filename,
            'size': backup_size,
            'size_formatted': format_file_size(backup_size),
            'timestamp': timestamp,
            'created_at': datetime.now()
        }
    except Exception as e:
        raise Exception(f"Failed to create backup: {str(e)}")


def list_backups():
    """List all available backups"""
    backup_dir = get_backup_directory()
    backups = []
    
    if not backup_dir.exists():
        return backups
    
    for backup_file in backup_dir.glob('pcm_store_backup_*.db'):
        try:
            stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'path': str(backup_file),
                'size': stat.st_size,
                'size_formatted': format_file_size(stat.st_size),
                'created_at': datetime.fromtimestamp(stat.st_mtime),
                'timestamp': backup_file.stem.replace('pcm_store_backup_', '')
            })
        except Exception:
            continue
    
    # Sort by creation time (newest first)
    backups.sort(key=lambda x: x['created_at'], reverse=True)
    return backups


def restore_database(backup_filename, create_backup=True):
    """Restore database from a backup file"""
    backup_dir = get_backup_directory()
    backup_path = backup_dir / backup_filename
    
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_filename}")
    
    db_path = get_database_path()
    if not db_path:
        raise ValueError("Database path not configured")
    
    try:
        # Create a backup of current database before restoring
        if create_backup and os.path.exists(db_path):
            current_backup = backup_database()
            current_app.logger.info(f"Created backup before restore: {current_backup['backup_filename']}")
        
        # Close any existing database connections
        # Note: In production, you may need to restart the app after restore
        
        # Copy backup file to database location
        shutil.copy2(backup_path, db_path)
        
        return {
            'success': True,
            'restored_from': backup_filename,
            'database_path': db_path,
            'restored_at': datetime.now()
        }
    except Exception as e:
        raise Exception(f"Failed to restore database: {str(e)}")


def delete_backup(backup_filename):
    """Delete a backup file"""
    backup_dir = get_backup_directory()
    backup_path = backup_dir / backup_filename
    
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_filename}")
    
    try:
        backup_path.unlink()
        return {
            'success': True,
            'deleted_file': backup_filename
        }
    except Exception as e:
        raise Exception(f"Failed to delete backup: {str(e)}")


def get_database_statistics():
    """Get database statistics"""
    db_path = get_database_path()
    if not db_path or not os.path.exists(db_path):
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        stats = {}
        total_rows = 0
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            stats[table] = count
            total_rows += count
        
        # Get database page count and size
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        db_size = page_count * page_size
        
        conn.close()
        
        return {
            'tables': stats,
            'total_tables': len(tables),
            'total_rows': total_rows,
            'page_count': page_count,
            'page_size': page_size,
            'calculated_size': db_size
        }
    except Exception as e:
        current_app.logger.error(f"Error getting database statistics: {e}")
        return None

