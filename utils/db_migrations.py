"""
Database Migration System
Safely migrates database schema without losing data
"""
from sqlalchemy import inspect, text, MetaData
from flask import current_app
from models import db
import traceback


def get_table_columns(table_name):
    """Get all column names for a table"""
    try:
        inspector = inspect(db.engine)
        if table_name not in inspector.get_table_names():
            return []
        columns = inspector.get_columns(table_name)
        return [col['name'] for col in columns]
    except Exception as e:
        current_app.logger.error(f"Error getting columns for {table_name}: {e}")
        return []


def get_table_info(table_name):
    """Get detailed column information for a table"""
    try:
        inspector = inspect(db.engine)
        if table_name not in inspector.get_table_names():
            return []
        return inspector.get_columns(table_name)
    except Exception:
        return []


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    columns = get_table_columns(table_name)
    return column_name in columns


def table_exists(table_name):
    """Check if a table exists"""
    try:
        inspector = inspect(db.engine)
        return table_name in inspector.get_table_names()
    except Exception:
        return False


def safe_add_column(table_name, column_name, column_type, default_value=None, nullable=True):
    """
    Safely add a column to a table if it doesn't exist
    Returns True if column was added, False if it already exists
    """
    if column_exists(table_name, column_name):
        return False
    
    try:
        with db.engine.begin() as conn:
            # Build ALTER TABLE statement
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            
            # Add DEFAULT if provided
            if default_value is not None:
                if isinstance(default_value, str):
                    alter_sql += f" DEFAULT '{default_value}'"
                else:
                    alter_sql += f" DEFAULT {default_value}"
            
            # Add NOT NULL if not nullable
            if not nullable:
                alter_sql += " NOT NULL"
            
            conn.execute(text(alter_sql))
            
            # If default was provided and column is nullable, update existing rows
            if default_value is not None and nullable:
                update_sql = f"UPDATE {table_name} SET {column_name} = :default_val WHERE {column_name} IS NULL"
                if isinstance(default_value, str):
                    conn.execute(text(update_sql), {"default_val": default_value})
                else:
                    conn.execute(text(update_sql), {"default_val": default_value})
            
            current_app.logger.info(f"✓ Added column {column_name} to table {table_name}")
            return True
    except Exception as e:
        error_msg = str(e).lower()
        if 'duplicate column' in error_msg or 'already exists' in error_msg:
            return False
        current_app.logger.error(f"Error adding column {column_name} to {table_name}: {e}")
        raise


def migrate_all_tables():
    """
    Migrate all tables to match current models
    This function adds missing columns without dropping existing ones
    """
    migrations_applied = []
    
    try:
        # Import all models to get their definitions
        from models import (
            User, Category, Material, AdminLog, MobilePaymentMethod,
            DownloadRecord, VisitorRecord, PageView, News, Subscription,
            SubscriptionPlan, PasswordResetToken, LimitedAccessDownload,
            TermsOfService, HelpRequest, TopUser, UserVisit, MpesaTransaction,
            MaterialView
        )
        
        # Define all tables and their columns with types
        # Format: table_name: [(column_name, column_type, default, nullable), ...]
        table_definitions = {
            'users': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('email', 'VARCHAR(120)', None, False),
                ('password_hash', 'VARCHAR(128)', None, False),
                ('first_name', 'VARCHAR(50)', None, False),
                ('last_name', 'VARCHAR(50)', None, False),
                ('phone', 'VARCHAR(20)', None, True),
                ('is_admin', 'BOOLEAN', '0', True),
                ('is_active', 'BOOLEAN', '1', True),
                ('created_at', 'DATETIME', None, True),
                ('last_login', 'DATETIME', None, True),
            ],
            'subscriptions': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('user_id', 'INTEGER', None, False),
                ('plan_id', 'INTEGER', None, True),  # Can be NULL for manual subscriptions
                ('start_date', 'DATETIME', None, False),
                ('end_date', 'DATETIME', None, False),
                ('max_materials', 'INTEGER', '100', False),
                ('materials_accessed', 'INTEGER', '0', True),
                ('is_active', 'BOOLEAN', '1', True),
                ('payment_status', 'VARCHAR(20)', "'pending'", True),
                ('created_at', 'DATETIME', None, True),
            ],
            'mobile_payment_methods': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('name', 'VARCHAR(100)', None, False),
                ('phone_number', 'VARCHAR(20)', None, False),
                ('is_active', 'BOOLEAN', '1', True),
                ('supports_click_to_pay', 'BOOLEAN', '0', True),
                ('created_at', 'DATETIME', None, True),
            ],
            'materials': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('title', 'VARCHAR(200)', None, False),
                ('description', 'TEXT', None, True),
                ('category_id', 'INTEGER', None, True),
                ('file_path', 'VARCHAR(500)', None, True),
                ('file_size', 'INTEGER', None, True),
                ('file_format', 'VARCHAR(50)', None, True),
                ('image_path', 'VARCHAR(500)', None, True),
                ('video_thumbnail', 'VARCHAR(500)', None, True),
                ('is_video', 'BOOLEAN', '0', True),
                ('video_duration', 'INTEGER', None, True),
                ('video_quality', 'VARCHAR(20)', None, True),
                ('price', 'DECIMAL(10,2)', None, True),
                ('is_premium', 'BOOLEAN', '0', True),
                ('created_at', 'DATETIME', None, True),
                ('updated_at', 'DATETIME', None, True),
            ],
            'categories': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('name', 'VARCHAR(100)', None, False),
                ('description', 'TEXT', None, True),
                ('icon', 'VARCHAR(10)', None, True),
                ('parent_id', 'INTEGER', None, True),
                ('level', 'VARCHAR(50)', None, True),
                ('created_at', 'DATETIME', None, True),
            ],
            'subscription_plans': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('name', 'VARCHAR(100)', None, False),
                ('description', 'TEXT', None, True),
                ('price', 'DECIMAL(10,2)', None, False),
                ('duration_days', 'INTEGER', None, False),
                ('max_materials', 'INTEGER', '100', True),
                ('features', 'TEXT', None, True),
                ('is_active', 'BOOLEAN', '1', True),
                ('is_popular', 'BOOLEAN', '0', True),
                ('sort_order', 'INTEGER', '0', True),
                ('created_at', 'DATETIME', None, True),
                ('updated_at', 'DATETIME', None, True),
            ],
            'admin_logs': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('admin_id', 'INTEGER', None, False),
                ('action', 'VARCHAR(100)', None, False),
                ('table_name', 'VARCHAR(50)', None, True),
                ('record_id', 'INTEGER', None, True),
                ('details', 'TEXT', None, True),
                ('ip_address', 'VARCHAR(45)', None, True),
                ('created_at', 'DATETIME', None, True),
            ],
            'download_records': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('user_id', 'INTEGER', None, False),
                ('material_id', 'INTEGER', None, False),
                ('download_type', 'VARCHAR(20)', "'purchase'", True),
                ('ip_address', 'VARCHAR(45)', None, True),
                ('user_agent', 'TEXT', None, True),
                ('download_count', 'INTEGER', '1', True),
                ('last_downloaded', 'DATETIME', None, True),
                ('created_at', 'DATETIME', None, True),
            ],
            'visitor_records': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('ip_address', 'VARCHAR(45)', None, False),
                ('user_agent', 'TEXT', None, True),
                ('country', 'VARCHAR(100)', None, True),
                ('city', 'VARCHAR(100)', None, True),
                ('referrer', 'VARCHAR(500)', None, True),
                ('first_visit', 'DATETIME', None, True),
                ('last_visit', 'DATETIME', None, True),
                ('visit_count', 'INTEGER', '1', True),
                ('is_unique', 'BOOLEAN', '1', True),
            ],
            'page_views': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('page_url', 'VARCHAR(500)', None, False),
                ('page_title', 'VARCHAR(200)', None, True),
                ('visitor_id', 'INTEGER', None, True),
                ('ip_address', 'VARCHAR(45)', None, True),
                ('user_agent', 'TEXT', None, True),
                ('referrer', 'VARCHAR(500)', None, True),
                ('view_count', 'INTEGER', '1', True),
                ('last_viewed', 'DATETIME', None, True),
                ('created_at', 'DATETIME', None, True),
            ],
            'news': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('title', 'VARCHAR(200)', None, False),
                ('content', 'TEXT', None, False),
                ('excerpt', 'VARCHAR(500)', None, True),
                ('author_id', 'INTEGER', None, False),
                ('is_published', 'BOOLEAN', '1', True),
                ('is_featured', 'BOOLEAN', '0', True),
                ('view_count', 'INTEGER', '0', True),
                ('created_at', 'DATETIME', None, True),
                ('updated_at', 'DATETIME', None, True),
                ('published_at', 'DATETIME', None, True),
            ],
            'wishlist_items': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('user_id', 'INTEGER', None, False),
                ('material_id', 'INTEGER', None, False),
                ('added_at', 'DATETIME', None, True),
            ],
            'password_reset_tokens': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('user_id', 'INTEGER', None, False),
                ('token', 'VARCHAR(100)', None, False),
                ('expires_at', 'DATETIME', None, False),
                ('used', 'BOOLEAN', '0', True),
                ('created_at', 'DATETIME', None, True),
            ],
            'limited_access_downloads': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('user_id', 'INTEGER', None, False),
                ('material_id', 'INTEGER', None, False),
                ('download_date', 'DATE', None, False),
                ('download_type', 'VARCHAR(20)', None, False),
                ('created_at', 'DATETIME', None, True),
            ],
            'terms_of_service': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('content', 'TEXT', None, False),
                ('updated_by', 'INTEGER', None, False),
                ('updated_at', 'DATETIME', None, True),
                ('created_at', 'DATETIME', None, True),
            ],
            'help_requests': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('user_id', 'INTEGER', None, False),
                ('subject', 'VARCHAR(200)', None, False),
                ('message', 'TEXT', None, False),
                ('status', 'VARCHAR(20)', "'pending'", True),
                ('admin_response', 'TEXT', None, True),
                ('responded_by', 'INTEGER', None, True),
                ('responded_at', 'DATETIME', None, True),
                ('created_at', 'DATETIME', None, True),
                ('updated_at', 'DATETIME', None, True),
            ],
            'user_visits': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('user_id', 'INTEGER', None, False),
                ('visit_date', 'DATE', None, False),
                ('visit_count', 'INTEGER', '1', True),
                ('created_at', 'DATETIME', None, True),
            ],
            'top_users': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('user_id', 'INTEGER', None, False),
                ('serial_number', 'INTEGER', None, False),
                ('days_or_months', 'VARCHAR(50)', None, True),
                ('admin_gift', 'DECIMAL(10,2)', '0', True),
                ('status', 'VARCHAR(50)', "'active'", True),
                ('is_visible', 'BOOLEAN', '1', True),
                ('created_at', 'DATETIME', None, True),
                ('updated_at', 'DATETIME', None, True),
            ],
            'mpesa_transactions': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('user_id', 'INTEGER', None, False),
                ('material_id', 'INTEGER', None, True),
                ('msisdn', 'VARCHAR(20)', None, False),
                ('amount', 'DECIMAL(10,2)', None, False),
                ('currency', 'VARCHAR(10)', "'TZS'", True),
                ('conversation_id', 'VARCHAR(64)', None, False),
                ('transaction_reference', 'VARCHAR(64)', None, False),
                ('status', 'VARCHAR(30)', "'pending'", True),
                ('response_payload', 'TEXT', None, True),
                ('error_message', 'TEXT', None, True),
                ('created_at', 'DATETIME', None, True),
                ('updated_at', 'DATETIME', None, True),
            ],
            'material_views': [
                ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', None, False),
                ('user_id', 'INTEGER', None, False),
                ('material_id', 'INTEGER', None, False),
                ('view_count', 'INTEGER', '1', True),
                ('first_viewed', 'DATETIME', None, True),
                ('last_viewed', 'DATETIME', None, True),
            ],
        }
        
        # Migrate each table
        for table_name, columns in table_definitions.items():
            if not table_exists(table_name):
                # Table doesn't exist - db.create_all() will handle it
                continue
            
            # Add missing columns
            for column_name, column_type, default_value, nullable in columns:
                # Skip primary key columns
                if 'PRIMARY KEY' in column_type:
                    continue
                
                try:
                    if safe_add_column(table_name, column_name, column_type, default_value, nullable):
                        migrations_applied.append(f"Added {column_name} to {table_name}")
                except Exception as e:
                    current_app.logger.error(f"Failed to add {column_name} to {table_name}: {e}")
        
        return migrations_applied
        
    except Exception as e:
        current_app.logger.error(f"Error in migrate_all_tables: {e}")
        traceback.print_exc()
        return migrations_applied


def safe_migrate_database():
    """
    Safe database migration - ensures all tables and columns exist
    without dropping any existing data
    """
    try:
        # First, create all tables (only creates if they don't exist)
        db.create_all()
        
        # Then, migrate columns
        migrations = migrate_all_tables()
        
        # Also run the legacy add_missing_columns for backward compatibility
        from app import add_missing_columns
        add_missing_columns()
        
        return {
            'success': True,
            'migrations_applied': migrations,
            'message': f'Database migration completed. Applied {len(migrations)} migrations.'
        }
    except Exception as e:
        current_app.logger.error(f"Database migration error: {e}")
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'message': f'Database migration failed: {str(e)}'
        }

