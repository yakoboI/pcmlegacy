from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_from_directory, Response, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
try:
    from flask_compress import Compress
    COMPRESS_AVAILABLE = True
except ImportError:
    COMPRESS_AVAILABLE = False
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from sqlalchemy import inspect, text, func
import os
import uuid
import re
import traceback
from datetime import datetime, timedelta, timezone
from decimal import Decimal
try:
    from utils.image_optimizer import convert_to_webp, optimize_image, WEBP_QUALITY
    IMAGE_OPTIMIZATION_AVAILABLE = True
except ImportError:
    IMAGE_OPTIMIZATION_AVAILABLE = False
try:
    from utils.db_backup import (
        backup_database, restore_database, list_backups, 
        delete_backup, get_database_info, get_database_statistics
    )
    DB_BACKUP_AVAILABLE = True
except ImportError:
    DB_BACKUP_AVAILABLE = False
from models import db, User, Category, Material, AdminLog, MobilePaymentMethod, DownloadRecord, VisitorRecord, PageView, News, Subscription, SubscriptionPlan, PasswordResetToken, LimitedAccessDownload, TermsOfService, HelpRequest, TopUser, UserVisit, MpesaTransaction, MaterialView
from forms import *
from config import config
from services.mpesa_client import (
    MpesaClient,
    MpesaConfigError,
    MpesaRequestError,
    generate_conversation_id,
    generate_transaction_reference,
    normalize_msisdn,
)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
app = Flask(__name__, static_url_path='/static', static_folder='static')
env = os.environ.get('FLASK_ENV', 'development').lower()
config_name = 'production' if env == 'production' else 'development'
app.config.from_object(config[config_name])
_total_users_cache = {'count': 0, 'timestamp': None}
CACHE_DURATION = 300
PAYMENT_TIMEOUT_MINUTES = 30
_rate_limit_storage = {}
RATE_LIMIT_WINDOW = 3600
RATE_LIMIT_MAX_REQUESTS = 10
def check_rate_limit(user_id=None, ip_address=None):
    """Simple rate limiting for payment endpoints"""
    key = f"user_{user_id}" if user_id else f"ip_{ip_address}"
    now = datetime.now(timezone.utc)
    if key not in _rate_limit_storage:
        _rate_limit_storage[key] = []
    _rate_limit_storage[key] = [
        timestamp for timestamp in _rate_limit_storage[key]
        if (now - timestamp).total_seconds() < RATE_LIMIT_WINDOW
    ]
    if len(_rate_limit_storage[key]) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    _rate_limit_storage[key].append(now)
    return True
def cleanup_expired_payments():
    """Clean up expired pending payments and transactions"""
    try:
        now = datetime.now(timezone.utc)
        timeout_threshold = now - timedelta(minutes=PAYMENT_TIMEOUT_MINUTES)
        expired_subscriptions = Subscription.query.filter(
            Subscription.payment_status == 'pending',
            Subscription.created_at < timeout_threshold
        ).all()
        for subscription in expired_subscriptions:
            subscription.payment_status = 'failed'
            subscription.is_active = False
            current_app.logger.info(f"Cancelled expired subscription {subscription.id}")
        expired_transactions = MpesaTransaction.query.filter(
            MpesaTransaction.status.in_(['pending', 'submitted']),
            MpesaTransaction.created_at < timeout_threshold
        ).all()
        for transaction in expired_transactions:
            transaction.status = 'failed'
            transaction.error_message = 'Payment timeout - no response received'
            current_app.logger.info(f"Cancelled expired transaction {transaction.id}")
        db.session.commit()
        return len(expired_subscriptions) + len(expired_transactions)
    except Exception as e:
        current_app.logger.error(f"Error cleaning up expired payments: {e}")
        db.session.rollback()
        return 0
@app.context_processor
def inject_total_users():
    """Make total users count available in all templates - Cached for performance"""
    global _total_users_cache
    now = datetime.now(timezone.utc)
    if (_total_users_cache['timestamp'] is None or
        (now - _total_users_cache['timestamp']).total_seconds() > CACHE_DURATION):
        try:
            _total_users_cache['count'] = User.query.count()
            _total_users_cache['timestamp'] = now
        except:
            _total_users_cache['count'] = 0
    return dict(total_users=_total_users_cache['count'])

@app.template_filter('webp_image')
def webp_image_filter(image_path):
    """Generate WebP image path with fallback to original"""
    if not image_path:
        return None
    
    # Check if image is already WebP
    if image_path.lower().endswith('.webp'):
        return image_path
    
    # Generate WebP path
    base_path = os.path.splitext(image_path)[0]
    webp_path = f"{base_path}.webp"
    
    # Check if WebP version exists
    full_webp_path = os.path.join(app.static_folder, webp_path)
    if os.path.exists(full_webp_path):
        return webp_path
    
    # Return original if WebP doesn't exist
    return image_path
@app.after_request
def add_security_headers(response):
    """Add security headers and cache headers for all responses"""
    # Security Headers
    # Content Security Policy - Prevents XSS attacks
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'self'; "
        "upgrade-insecure-requests;"
    )
    response.headers['Content-Security-Policy'] = csp_policy
    
    # X-Frame-Options - Prevents clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # X-Content-Type-Options - Prevents MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # X-XSS-Protection - Legacy XSS protection (for older browsers)
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Referrer-Policy - Controls referrer information
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions-Policy - Controls browser features
    response.headers['Permissions-Policy'] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=()"
    )
    
    # Strict-Transport-Security (HSTS) - Only in production with HTTPS
    if app.config.get('PREFERRED_URL_SCHEME') == 'https' or os.environ.get('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    
    # Cache Headers
    if request.endpoint == 'static':
        response.cache_control.max_age = 31536000
        response.cache_control.public = True
        response.cache_control.must_revalidate = True
    elif response.content_type and response.content_type.startswith('text/html'):
        response.cache_control.max_age = 300
        response.cache_control.public = True
        response.cache_control.must_revalidate = True
    elif response.content_type and response.content_type.startswith(('image/', 'video/')):
        response.cache_control.max_age = 3600
        response.cache_control.public = True
    response.headers.add('Vary', 'Accept-Encoding')
    return response
app.config['MAX_FORM_MEMORY_SIZE'] = 512 * 1024 * 1024
db.init_app(app)
mail = Mail(app)
if COMPRESS_AVAILABLE:
    compress = Compress(app)
else:
    print("Warning: flask_compress not installed. Compression disabled.")
from werkzeug.middleware.proxy_fix import ProxyFix
env = os.environ.get('FLASK_ENV', 'development').lower()
if env == 'production':
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_port=1)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        print(f"Error loading user {user_id}: {e}")
        traceback.print_exc()
        return None
@app.before_request
def track_visitor():
    """Track website visitors and page views"""
    if request.path in ['/sitemap.xml', '/sitemap', '/sitemap/', '/robots.txt']:
        return None
    if not request.endpoint or request.endpoint.startswith('static') or 'admin' in request.endpoint or request.endpoint.startswith('video') or request.endpoint.startswith('track_') or request.endpoint in ['sitemap', 'sitemap_xml', 'sitemap_slash', 'robots_txt']:
        return
    if request.is_json or request.headers.get('Content-Type', '').startswith('application/json'):
        return
    try:
        visitor_ip = request.remote_addr
        now = datetime.now(timezone.utc)
        visitor = VisitorRecord.query.filter_by(ip_address=visitor_ip).first()
        if not visitor:
            visitor = VisitorRecord(
                ip_address=visitor_ip,
                user_agent=request.headers.get('User-Agent', '')[:255],
                first_visit=now
            )
            db.session.add(visitor)
            db.session.flush()
        else:
            if visitor.visit_count % 10 == 0 or (visitor.last_visit and (now - visitor.last_visit).total_seconds() > 300):
                visitor.last_visit = now
                visitor.visit_count += 1
        if current_user.is_authenticated and not current_user.is_admin:
            today = now.date()
            user_visit = UserVisit.query.filter_by(
                user_id=current_user.id,
                visit_date=today
            ).first()
            if user_visit:
                user_visit.visit_count += 1
            else:
                user_visit = UserVisit(
                    user_id=current_user.id,
                    visit_date=today,
                    visit_count=1
                )
                db.session.add(user_visit)
        if request.endpoint and request.endpoint not in ['static', 'video_content', 'track_video_progress', 'track_video_completion']:
            page_url = request.url[:500]
            page_view = PageView.query.filter_by(
                page_url=page_url,
                visitor_id=visitor.id
            ).first()
            if page_view:
                if not page_view.last_viewed or (now - page_view.last_viewed).total_seconds() > 30:
                    page_view.view_count += 1
                    page_view.last_viewed = now
            else:
                page_view = PageView(
                    page_url=page_url,
                    page_title=request.endpoint[:100] if request.endpoint else None,
                    visitor_id=visitor.id,
                    ip_address=visitor_ip,
                    user_agent=request.headers.get('User-Agent', '')[:255],
                    referrer=request.headers.get('Referer', '')[:500]
                )
                db.session.add(page_view)
        db.session.commit()
    except Exception:
        db.session.rollback()
        pass
@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    size_mb = 0
    try:
        if request.content_length:
            size_mb = round(request.content_length / (1024 * 1024), 2)
    except Exception:
        pass
    flash(f'Upload too large ({size_mb} MB). Maximum allowed is 512 MB.', 'error')
    return redirect(request.referrer or url_for('admin_add_material'))
@app.errorhandler(413)
def handle_413(e):
    size_mb = 0
    try:
        if request.content_length:
            size_mb = round(request.content_length / (1024 * 1024), 2)
    except Exception:
        pass
    flash(f'Upload too large ({size_mb} MB). Maximum allowed is 512 MB.', 'error')
    return redirect(request.referrer or url_for('admin_add_material'))
def init_db():
    """Initialize database - safe migration that preserves data"""
    with app.app_context():
        # Use safe migration that never drops tables or data
        try:
            from utils.db_migrations import safe_migrate_database
            migration_result = safe_migrate_database()
            if migration_result['success']:
                print(f"✓ {migration_result['message']}")
                if migration_result.get('migrations_applied'):
                    for migration in migration_result['migrations_applied']:
                        print(f"  - {migration}")
            else:
                print(f"⚠ Migration warning: {migration_result['message']}")
                # Fallback to basic create_all
                db.create_all()
                add_missing_columns()
        except ImportError:
            # Fallback if migration module not available
            print("⚠ Migration module not available, using basic migration")
            db.create_all()
            add_missing_columns()
        
        create_default_data()
def add_missing_columns():
    """Add missing columns to existing database tables - Legacy function for backward compatibility"""
    try:
        inspector = inspect(db.engine)
        if 'subscriptions' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('subscriptions')]
            if 'payment_status' not in columns:
                with db.engine.begin() as conn:
                    conn.execute(text("""
                        ALTER TABLE subscriptions 
                        ADD COLUMN payment_status VARCHAR(20) DEFAULT 'paid'
                    """))
                    conn.execute(text("""
                        UPDATE subscriptions 
                        SET payment_status = 'paid'
                    """))
                print("✓ Added payment_status column to subscriptions table")
        if 'mobile_payment_methods' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('mobile_payment_methods')]
            if 'supports_click_to_pay' not in columns:
                with db.engine.begin() as conn:
                    conn.execute(text("""
                        ALTER TABLE mobile_payment_methods 
                        ADD COLUMN supports_click_to_pay BOOLEAN DEFAULT 0
                    """))
                print("✓ Added supports_click_to_pay column to mobile_payment_methods table")
    except Exception as e:
        if 'duplicate column' not in str(e).lower() and 'already exists' not in str(e).lower():
            print(f"Migration note: {e}")
def create_default_data():
    """Create default data for the application"""
    existing_categories = Category.query.count()
    if existing_categories > 0:
        print("Categories already exist, skipping creation.")
        return
    main_categories = [
        {'name': 'Physics', 'description': 'Physics principles and applications', 'icon': '⚛️'},
        {'name': 'Mathematics', 'description': 'Mathematics and arithmetic concepts', 'icon': '🔢'},
        {'name': 'Chemistry', 'description': 'Chemistry concepts and experiments', 'icon': '🧪'},
        {'name': 'General', 'description': 'General educational materials', 'icon': '📚'}
    ]
    levels = ['Form 1', 'Form 2', 'Form 3', 'Form 4', 'Form 5', 'Form 6', 'University']
    for cat_data in main_categories:
        category = Category(**cat_data)
        db.session.add(category)
    db.session.flush()
    subject_categories = ['Physics', 'Mathematics', 'Chemistry']
    for subject in subject_categories:
        parent_category = Category.query.filter_by(name=subject).first()
        if parent_category:
            for level in levels:
                subcategory = Category(
                    name=f"{subject} - {level}",
                    description=f"{subject} materials for {level}",
                    icon=parent_category.icon,
                    parent_id=parent_category.id,
                    level=level
                )
                db.session.add(subcategory)
    if User.query.filter_by(is_admin=True).count() == 0:
        admin = User(
            email='admin@pcmlegacy.store',
            first_name='Admin',
            last_name='User',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
    create_default_subscription_plans()
    db.session.commit()
def create_default_subscription_plans():
    """Create default subscription plans"""
    default_plans = [
        {
            'name': 'Basic Plan',
            'description': 'Perfect for students who need access to essential materials',
            'price': 15000,
            'duration_days': 30,
            'max_materials': 50,
            'features': 'Access to 50 materials\nBasic support\nMobile access',
            'is_active': True,
            'is_popular': False,
            'sort_order': 1
        },
        {
            'name': 'Premium Plan',
            'description': 'Most popular choice with comprehensive access to all materials',
            'price': 25000,
            'duration_days': 30,
            'max_materials': 200,
            'features': 'Access to 200 materials\nPriority support\nVideo streaming\nDownload offline\nMobile & desktop access',
            'is_active': True,
            'is_popular': True,
            'sort_order': 2
        },
        {
            'name': 'Pro Plan',
            'description': 'For serious learners who need unlimited access',
            'price': 40000,
            'duration_days': 30,
            'max_materials': 500,
            'features': 'Unlimited materials\n24/7 support\nHD video streaming\nOffline downloads\nAll device access\nEarly access to new content',
            'is_active': True,
            'is_popular': False,
            'sort_order': 3
        },
        {
            'name': 'Annual Premium',
            'description': 'Best value with 12 months of premium access',
            'price': 200000,
            'duration_days': 365,
            'max_materials': 200,
            'features': '12 months access\nAll premium features\n2 months free\nPriority support\nExclusive content',
            'is_active': True,
            'is_popular': False,
            'sort_order': 4
        }
    ]
    for plan_data in default_plans:
        existing_plan = SubscriptionPlan.query.filter_by(name=plan_data['name']).first()
        if not existing_plan:
            plan = SubscriptionPlan(**plan_data)
            db.session.add(plan)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
def save_file(file, folder):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        ext_lower = ext.lower()
        
        # Check if it's an image file
        is_image = ext_lower in {'.png', '.jpg', '.jpeg', '.gif'}
        
        filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        target_dir = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        try:
            os.makedirs(target_dir, exist_ok=True)
            file_path = os.path.join(target_dir, filename)
            file.save(file_path)
            
            # Optimize image to WebP if it's an image file and optimization is available
            if is_image and IMAGE_OPTIMIZATION_AVAILABLE:
                try:
                    webp_filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webp"
                    webp_path = os.path.join(target_dir, webp_filename)
                    
                    # Convert to WebP with HD quality for clean, crisp images
                    convert_to_webp(
                        file_path,
                        webp_path,
                        quality=WEBP_QUALITY,  # HD quality (92) for clean images
                        preserve_original=True,  # Keep original as fallback
                        sharpen=True,  # Apply sharpening for crisp HD images
                        maintain_hd=True  # Ensure HD quality standards
                    )
                    
                    # Return WebP filename but keep original as fallback
                    return webp_filename
                except Exception as e:
                    try:
                        app.logger.error(f"Error optimizing image to WebP: {e}")
                    except:
                        print(f"Error optimizing image to WebP: {e}")
                    # Return original filename if optimization fails
                    return filename
            
            return filename
        except Exception as e:
            current_app.logger.error(f"Upload save error: {e}")
            return None
    return None
def get_file_format(filename):
    """Extract file format from filename"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return 'unknown'
def is_video_file(filename):
    """Check if file is a video based on extension"""
    video_extensions = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v', '3gp'}
    return get_file_format(filename) in video_extensions
def log_admin_action(action, table_name=None, record_id=None, details=None):
    if current_user.is_authenticated and current_user.is_admin:
        log = AdminLog(
            admin_id=current_user.id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
@app.route('/sitemap.xml', strict_slashes=False, endpoint='sitemap_xml', methods=['GET'])
@app.route('/sitemap', strict_slashes=False, endpoint='sitemap', methods=['GET'])
@app.route('/sitemap/', strict_slashes=False, endpoint='sitemap_slash', methods=['GET'])
def sitemap():
    """Generate dynamic sitemap.xml for SEO"""
    try:
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom
        base_url = request.url_root.rstrip('/')
        urlset = Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        urlset.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        urlset.set('xsi:schemaLocation', 'http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd')
        static_pages = [
            ('/', 1.0, 'daily'),
            ('/search', 0.8, 'daily'),
            ('/news', 0.8, 'daily'),
            ('/terms-of-service', 0.5, 'monthly'),
            ('/top-10-users', 0.6, 'weekly'),
        ]
        for path, priority, changefreq in static_pages:
            url_elem = SubElement(urlset, 'url')
            SubElement(url_elem, 'loc').text = f"{base_url}{path}"
            SubElement(url_elem, 'changefreq').text = changefreq
            SubElement(url_elem, 'priority').text = str(priority)
            SubElement(url_elem, 'lastmod').text = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        try:
            materials = Material.query.filter_by(is_active=True).order_by(Material.updated_at.desc()).limit(1000).all()
            for material in materials:
                url_elem = SubElement(urlset, 'url')
                SubElement(url_elem, 'loc').text = f"{base_url}/material/{material.id}"
                SubElement(url_elem, 'changefreq').text = 'weekly'
                SubElement(url_elem, 'priority').text = '0.7'
                lastmod = material.updated_at if material.updated_at else material.created_at
                SubElement(url_elem, 'lastmod').text = lastmod.strftime('%Y-%m-%d')
        except Exception as e:
            app.logger.error(f"Error adding materials to sitemap: {e}")
        try:
            news_articles = News.query.filter_by(is_published=True).order_by(News.updated_at.desc()).limit(500).all()
            for article in news_articles:
                url_elem = SubElement(urlset, 'url')
                SubElement(url_elem, 'loc').text = f"{base_url}/news/{article.id}"
                SubElement(url_elem, 'changefreq').text = 'monthly'
                SubElement(url_elem, 'priority').text = '0.6'
                lastmod = article.updated_at if article.updated_at else article.created_at
                SubElement(url_elem, 'lastmod').text = lastmod.strftime('%Y-%m-%d')
        except Exception as e:
            app.logger.error(f"Error adding news to sitemap: {e}")
        xml_bytes = minidom.parseString(tostring(urlset)).toprettyxml(indent="  ", encoding='UTF-8')
        xml_str = xml_bytes.decode('utf-8') if isinstance(xml_bytes, bytes) else xml_bytes
        response = Response(xml_str, mimetype='application/xml', status=200)
        response.headers['Content-Type'] = 'application/xml; charset=utf-8'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
    except Exception as e:
        app.logger.error(f"Error generating sitemap: {e}")
        traceback.print_exc()
        minimal_sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{request.url_root.rstrip('/')}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
        response = Response(minimal_sitemap, mimetype='application/xml', status=200)
        response.headers['Content-Type'] = 'application/xml; charset=utf-8'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    materials_query = Material.query.options(
        db.joinedload(Material.category)
    ).filter_by(is_active=True).order_by(Material.created_at.desc())
    materials = materials_query.paginate(
        page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False
    )
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    return render_template('index.html',
                         materials=materials,
                         categories=categories)
@app.route('/material/<int:material_id>')
def material_detail(material_id):
    material = Material.query.options(
        db.joinedload(Material.category)
    ).get_or_404(material_id)
    view_count = 0
    can_view_free = False
    has_access = False
    if current_user.is_authenticated:
        if current_user.is_admin:
            has_access = True
            can_view_free = True
        elif current_user.has_active_access():
            has_access = True
            can_view_free = True
        else:
            can_view_free = current_user.can_view_material_free(material_id)
            view_count = current_user.get_material_view_count(material_id)
            has_access = False
    else:
        can_view_free = False
        has_access = False
    return render_template('material_detail.html',
                         material=material,
                         has_access=has_access,
                         can_view_free=can_view_free,
                         view_count=view_count)
@app.route('/api/subscriptions/<int:plan_id>/mpesa-click-to-pay', methods=['POST'])
@login_required
def mpesa_click_to_pay_subscription(plan_id):
    """Initiate a click-to-pay MPesa transaction for a subscription plan."""
    if app.config.get('DEBUG'):
        app.logger.info(f'MPesa subscription payment request - plan_id: {plan_id}, user: {current_user.id}')
    try:
        if not check_rate_limit(user_id=current_user.id, ip_address=request.remote_addr):
            return jsonify({
                'success': False,
                'message': 'Too many payment requests. Please wait before trying again.'
            }), 429
        cleanup_expired_payments()
        plan = SubscriptionPlan.query.get_or_404(plan_id)
        if not plan.is_active:
            return jsonify({
                'success': False,
                'message': 'This subscription plan is not available.'
            }), 400
        existing_active = current_user.subscriptions.filter(
            Subscription.is_active == True,
            Subscription.payment_status == 'paid',
            Subscription.end_date > datetime.now(timezone.utc)
        ).first()
        if existing_active:
            return jsonify({
                'success': False,
                'message': f'You already have an active subscription that expires on {existing_active.end_date.strftime("%Y-%m-%d")}.'
            }), 400
        try:
            if request.is_json:
                payload = request.get_json(silent=False) or {}
            else:
                payload = request.form.to_dict() if request.form else {}
            msisdn_input = payload.get('msisdn', '').strip() if payload.get('msisdn') else ''
            if not msisdn_input and current_user.phone:
                msisdn_input = current_user.phone.strip()
            if not msisdn_input:
                return jsonify({
                    'success': False,
                    'message': 'Phone number is required. Please enter your Vodacom M-Pesa number.'
                }), 400
            msisdn = normalize_msisdn(msisdn_input)
        except ValueError as exc:
            return jsonify({'success': False, 'message': str(exc)}), 400
        except Exception as exc:
            current_app.logger.error(f'Error parsing request payload: {exc}')
            return jsonify({
                'success': False,
                'message': 'Invalid request format. Please try again.'
            }), 400
        amount_decimal = plan.price if plan.price is not None else Decimal('0.00')
        amount_str = f"{Decimal(amount_decimal):.2f}"
        conversation_id = generate_conversation_id()
        reference = f"SUB{plan_id}{uuid.uuid4().hex[:6].upper()}"
        subscription = Subscription(
            user_id=current_user.id,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=plan.duration_days),
            max_materials=plan.max_materials,
            payment_status='pending'
        )
        db.session.add(subscription)
        db.session.flush()
        transaction = MpesaTransaction(
            user_id=current_user.id,
            material_id=None,
            msisdn=msisdn,
            amount=amount_decimal,
            currency=current_app.config.get('MPESA_CURRENCY', 'TZS'),
            conversation_id=conversation_id,
            transaction_reference=reference,
            status='pending'
        )
        db.session.add(transaction)
        db.session.commit()
        client = None
        try:
            client = MpesaClient(current_app.config, logger=current_app.logger)
            metadata = {}
            callback_url = current_app.config.get('MPESA_CALLBACK_URL')
            if callback_url:
                metadata['input_CallbackURL'] = f"{callback_url}?subscription_id={subscription.id}"
            result = client.pay_single_stage(
                amount=amount_str,
                msisdn=msisdn,
                conversation_id=conversation_id,
                transaction_reference=reference,
                description=f"Subscription: {plan.name[:100]}",
                metadata=metadata or None
            )
            transaction.status = 'submitted'
            transaction.response_payload = result
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'M-Pesa payment request sent. Please approve the prompt on your phone to complete the subscription.',
                'transaction_id': transaction.id,
                'subscription_id': subscription.id
            }), 200
        except MpesaConfigError as e:
            current_app.logger.error(f'MPesa configuration error for subscription: {e}')
            transaction.status = 'failed'
            subscription.payment_status = 'failed'
            db.session.commit()
            return jsonify({
                'success': False,
                'message': f'Payment configuration error: {str(e)}. Please contact support.'
            }), 500
        except MpesaRequestError as e:
            current_app.logger.error(f'MPesa request error for subscription: {e}')
            transaction.status = 'failed'
            subscription.payment_status = 'failed'
            db.session.commit()
            return jsonify({
                'success': False,
                'message': f'Payment request failed: {str(e)}. Please try again or contact support.'
            }), 400
        except Exception as e:
            current_app.logger.error(f'Unexpected error in subscription MPesa payment: {e}')
            transaction.status = 'failed'
            subscription.payment_status = 'failed'
            db.session.commit()
            return jsonify({
                'success': False,
                'message': 'An unexpected error occurred. Please try again or contact support.'
            }), 500
    except Exception as e:
        current_app.logger.error(f'Error in mpesa_click_to_pay_subscription: {e}')
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred processing your request. Please try again.'
        }), 500
@app.route('/api/subscriptions/<int:plan_id>/mobile-payment/<int:method_id>/click-to-pay', methods=['POST'])
@login_required
def mpesa_click_to_pay_subscription_via_method(plan_id, method_id):
    """Initiate a click-to-pay MPesa transaction for a subscription via a specific mobile payment method."""
    try:
        if not check_rate_limit(user_id=current_user.id, ip_address=request.remote_addr):
            return jsonify({
                'success': False,
                'message': 'Too many payment requests. Please wait before trying again.'
            }), 429
        cleanup_expired_payments()
        
        # Verify the payment method exists and supports click to pay
        payment_method = MobilePaymentMethod.query.get_or_404(method_id)
        if not payment_method.is_active:
            return jsonify({
                'success': False,
                'message': 'This payment method is not available.'
            }), 400
        if not payment_method.supports_click_to_pay:
            return jsonify({
                'success': False,
                'message': 'This payment method does not support Click to Pay.'
            }), 400
        
        plan = SubscriptionPlan.query.get_or_404(plan_id)
        if not plan.is_active:
            return jsonify({
                'success': False,
                'message': 'This subscription plan is not available.'
            }), 400
        
        existing_active = current_user.subscriptions.filter(
            Subscription.is_active == True,
            Subscription.payment_status == 'paid',
            Subscription.end_date > datetime.now(timezone.utc)
        ).first()
        if existing_active:
            return jsonify({
                'success': False,
                'message': f'You already have an active subscription that expires on {existing_active.end_date.strftime("%Y-%m-%d")}.'
            }), 400
        
        try:
            if request.is_json:
                payload = request.get_json(silent=False) or {}
            else:
                payload = request.form.to_dict() if request.form else {}
            msisdn_input = payload.get('msisdn', '').strip() if payload.get('msisdn') else ''
            if not msisdn_input and current_user.phone:
                msisdn_input = current_user.phone.strip()
            if not msisdn_input:
                return jsonify({
                    'success': False,
                    'message': 'Phone number is required. Please enter your Vodacom M-Pesa number.'
                }), 400
            msisdn = normalize_msisdn(msisdn_input)
        except ValueError as exc:
            return jsonify({'success': False, 'message': str(exc)}), 400
        except Exception as exc:
            current_app.logger.error(f'Error parsing request payload: {exc}')
            return jsonify({
                'success': False,
                'message': 'Invalid request format. Please try again.'
            }), 400
        
        amount_decimal = plan.price if plan.price is not None else Decimal('0.00')
        amount_str = f"{Decimal(amount_decimal):.2f}"
        conversation_id = generate_conversation_id()
        reference = f"SUB{plan_id}M{method_id}{uuid.uuid4().hex[:6].upper()}"
        
        subscription = Subscription(
            user_id=current_user.id,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=plan.duration_days),
            max_materials=plan.max_materials,
            payment_status='pending'
        )
        db.session.add(subscription)
        db.session.flush()
        
        transaction = MpesaTransaction(
            user_id=current_user.id,
            material_id=None,
            msisdn=msisdn,
            amount=amount_decimal,
            currency=current_app.config.get('MPESA_CURRENCY', 'TZS'),
            conversation_id=conversation_id,
            transaction_reference=reference,
            status='pending'
        )
        db.session.add(transaction)
        db.session.commit()
        
        try:
            client = MpesaClient(current_app.config, logger=current_app.logger)
            metadata = {}
            callback_url = current_app.config.get('MPESA_CALLBACK_URL')
            if callback_url:
                metadata['input_CallbackURL'] = f"{callback_url}?subscription_id={subscription.id}&method_id={method_id}"
            result = client.pay_single_stage(
                amount=amount_str,
                msisdn=msisdn,
                conversation_id=conversation_id,
                transaction_reference=reference,
                description=f"Subscription: {plan.name[:100]} via {payment_method.display_name}",
                metadata=metadata or None
            )
            transaction.status = 'submitted'
            transaction.response_payload = result
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'M-Pesa payment request sent via {payment_method.display_name}. Please approve the prompt on your phone to complete the subscription.',
                'transaction_id': transaction.id,
                'subscription_id': subscription.id
            }), 200
        except MpesaConfigError as e:
            current_app.logger.error(f'MPesa configuration error: {e}')
            transaction.status = 'failed'
            subscription.payment_status = 'failed'
            db.session.commit()
            return jsonify({
                'success': False,
                'message': f'Payment configuration error: {str(e)}. Please contact support.'
            }), 500
        except MpesaRequestError as e:
            current_app.logger.error(f'MPesa request error: {e}')
            transaction.status = 'failed'
            subscription.payment_status = 'failed'
            db.session.commit()
            return jsonify({
                'success': False,
                'message': f'Payment request failed: {str(e)}. Please try again or contact support.'
            }), 400
        except Exception as e:
            current_app.logger.error(f'Unexpected error: {e}')
            transaction.status = 'failed'
            subscription.payment_status = 'failed'
            db.session.commit()
            return jsonify({
                'success': False,
                'message': 'An unexpected error occurred. Please try again or contact support.'
            }), 500
    except Exception as e:
        current_app.logger.error(f'Error in mpesa_click_to_pay_subscription_via_method: {e}')
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred processing your request. Please try again.'
        }), 500
@app.route('/api/materials/<int:material_id>/mpesa-click-to-pay', methods=['POST'])
@login_required
def mpesa_click_to_pay(material_id):
    """Initiate a click-to-pay MPesa transaction for a material."""
    try:
        if not check_rate_limit(user_id=current_user.id, ip_address=request.remote_addr):
            return jsonify({
                'success': False,
                'message': 'Too many payment requests. Please wait before trying again.'
            }), 429
        cleanup_expired_payments()
        material = Material.query.get_or_404(material_id)
        if not material.is_active:
            return jsonify({
                'success': False,
                'message': 'This material is currently not available for purchase.'
            }), 400
        if material.is_free:
            return jsonify({
                'success': False,
                'message': 'This material is free to access. No payment required.'
            }), 400
        if material.price is None or material.price <= 0:
            return jsonify({
                'success': False,
                'message': 'This material has no price set. Please contact support.'
            }), 400
        try:
            if request.is_json:
                payload = request.get_json(silent=False) or {}
            else:
                payload = request.form.to_dict() if request.form else {}
            msisdn_input = payload.get('msisdn', '').strip() if payload.get('msisdn') else ''
            if not msisdn_input and current_user.phone:
                msisdn_input = current_user.phone.strip()
            if not msisdn_input:
                return jsonify({
                    'success': False,
                    'message': 'Phone number is required. Please enter your Vodacom M-Pesa number.'
                }), 400
            msisdn = normalize_msisdn(msisdn_input)
        except ValueError as exc:
            return jsonify({'success': False, 'message': str(exc)}), 400
        except Exception as exc:
            current_app.logger.error(f'Error parsing request payload: {exc}')
            return jsonify({
                'success': False,
                'message': 'Invalid request format. Please try again.'
            }), 400
        amount_decimal = material.price if material.price is not None else Decimal('0.00')
        amount_str = f"{Decimal(amount_decimal):.2f}"
        conversation_id = generate_conversation_id()
        reference = generate_transaction_reference(material.id)
        transaction = MpesaTransaction(
            user_id=current_user.id,
            material_id=material.id,
            msisdn=msisdn,
            amount=amount_decimal,
            currency=current_app.config.get('MPESA_CURRENCY', 'TZS'),
            conversation_id=conversation_id,
            transaction_reference=reference,
            status='pending'
        )
        db.session.add(transaction)
        db.session.commit()
        client = None
        try:
            client = MpesaClient(current_app.config, logger=current_app.logger)
            metadata = {}
            callback_url = current_app.config.get('MPESA_CALLBACK_URL')
            if callback_url:
                metadata['input_CallbackURL'] = callback_url
            result = client.pay_single_stage(
                amount=amount_str,
                msisdn=msisdn,
                conversation_id=conversation_id,
                transaction_reference=reference,
                description=f"{material.title[:100]}",
                metadata=metadata or None
            )
            transaction.status = 'submitted'
            transaction.response_payload = result
            db.session.commit()
            log_admin_action(
                'mpesa_payment_initiated',
                'mpesa_transactions',
                transaction.id,
                f"Material: {material.title} ({material.id}) | MSISDN: {msisdn}"
            )
            return jsonify({
                'success': True,
                'status': 'submitted',
                'message': 'Payment request sent. Approve the prompt on your phone to complete the purchase.',
                'reference': reference,
                'conversationId': conversation_id
            })
        except MpesaConfigError as exc:
            transaction.status = 'failed'
            transaction.error_message = str(exc)
            db.session.commit()
            return jsonify({'success': False, 'message': str(exc)}), 500
        except MpesaRequestError as exc:
            transaction.status = 'failed'
            transaction.error_message = str(exc)
            db.session.commit()
            current_app.logger.error(f'MPesa request error for material {material_id}: {exc}')
            return jsonify({'success': False, 'message': str(exc)}), 400
        except Exception as exc:
            current_app.logger.exception('MPesa payment initiation failed: %s', exc)
            if 'transaction' in locals():
                transaction.status = 'failed'
                transaction.error_message = 'Unexpected error during MPesa call.'
                db.session.commit()
            return jsonify({'success': False, 'message': 'Unexpected error initiating payment. Please try again.'}), 500
    except Exception as e:
        current_app.logger.error(f'Error in mpesa_click_to_pay: {e}')
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred processing your request. Please try again.'
        }), 500
@app.route('/api/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """
    MPesa webhook callback handler for payment verification.
    This endpoint receives payment status updates from MPesa.
    """
    try:
        callback_data = request.get_json(silent=True) or request.form.to_dict()
        current_app.logger.info(f"MPesa callback received: {callback_data}")
        conversation_id = callback_data.get('output_ConversationID') or callback_data.get('ConversationID')
        transaction_ref = callback_data.get('output_TransactionReference') or callback_data.get('TransactionReference')
        response_code = callback_data.get('output_ResponseCode') or callback_data.get('ResponseCode')
        response_desc = callback_data.get('output_ResponseDesc') or callback_data.get('ResponseDesc', '')
        transaction_id = callback_data.get('output_TransactionID') or callback_data.get('TransactionID')
        transaction = None
        if conversation_id:
            transaction = MpesaTransaction.query.filter_by(conversation_id=conversation_id).first()
        if not transaction and transaction_ref:
            transaction = MpesaTransaction.query.filter_by(transaction_reference=transaction_ref).first()
        if not transaction:
            current_app.logger.warning(f"MPesa callback: Transaction not found. ConversationID: {conversation_id}, Ref: {transaction_ref}")
            return jsonify({'status': 'error', 'message': 'Transaction not found'}), 404
        transaction.response_payload = callback_data
        if response_code == "INS-0" or response_code == "0" or (isinstance(response_code, str) and "success" in response_desc.lower()):
            transaction.status = 'completed'
            transaction.error_message = None
            subscription_id = request.args.get('subscription_id') or None
            if not subscription_id and transaction_ref and transaction_ref.startswith('SUB'):
                try:
                    match = re.match(r'SUB(\d+)', transaction_ref)
                    if match:
                        subscription_id = match.group(1)
                except (ValueError, AttributeError):
                    pass
            if subscription_id:
                try:
                    subscription = Subscription.query.get(int(subscription_id))
                    if subscription and subscription.payment_status == 'pending':
                        subscription.payment_status = 'paid'
                        subscription.is_active = True
                        db.session.commit()
                        log_admin_action(
                            'subscription_auto_activated',
                            'subscriptions',
                            subscription.id,
                            f"Auto-activated via MPesa payment | TransactionID: {transaction_id}"
                        )
                except (ValueError, AttributeError) as e:
                    current_app.logger.error(f"Error activating subscription {subscription_id}: {e}")
            if transaction.material_id:
                material = Material.query.get(transaction.material_id)
                if material:
                    download_record = DownloadRecord.query.filter_by(
                        user_id=transaction.user_id,
                        material_id=transaction.material_id
                    ).first()
                    if not download_record:
                        download_record = DownloadRecord(
                            user_id=transaction.user_id,
                            material_id=transaction.material_id,
                            download_type='purchase'
                        )
                        db.session.add(download_record)
                    log_admin_action(
                        'mpesa_payment_completed',
                        'mpesa_transactions',
                        transaction.id,
                        f"Material: {material.title} | TransactionID: {transaction_id}"
                    )
        else:
            transaction.status = 'failed'
            transaction.error_message = f"MPesa Error: {response_desc} (Code: {response_code})"
            log_admin_action(
                'mpesa_payment_failed',
                'mpesa_transactions',
                transaction.id,
                f"Error: {response_desc} (Code: {response_code})"
            )
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Callback processed'
        }), 200
    except Exception as e:
        current_app.logger.exception(f"Error processing MPesa callback: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 200
@app.route('/stream/<int:material_id>')
@login_required
def stream_video(material_id):
    """Stream video content"""
    material = Material.query.get_or_404(material_id)
    if current_user.is_admin or current_user.has_active_access():
        active_subscription = current_user.subscriptions.filter(
            Subscription.is_active == True,
            Subscription.payment_status == 'paid',
            Subscription.end_date > datetime.now(timezone.utc)
        ).first()
        if active_subscription and not active_subscription.can_access_material():
            flash(f'You have reached your limit of {active_subscription.max_materials} materials for this subscription period.', 'error')
            return redirect(url_for('material_detail', material_id=material_id))
        if active_subscription:
            active_subscription.increment_access()
            db.session.commit()
        access_type = "subscription" if current_user.has_active_access() else "limited"
        log_admin_action(f'{access_type}_video_view', 'materials', material_id, f'{access_type.title()} video view: {material.title}')
    elif not current_user.can_view_material_free(material_id):
        flash('You have already viewed this video. Please pay to view again.', 'error')
        return redirect(url_for('material_detail', material_id=material_id))
    else:
        view_count = current_user.get_material_view_count(material_id)
        if view_count == 0:
            material_view = MaterialView(
                user_id=current_user.id,
                material_id=material_id,
                view_count=1
            )
            db.session.add(material_view)
            db.session.commit()
    return render_template('video_player.html', material=material)
def _guess_video_mime(ext):
    mapping = {
        'mp4': 'video/mp4',
        'webm': 'video/webm',
        'ogg': 'video/ogg',
        'ogv': 'video/ogg',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime',
        'wmv': 'video/x-ms-wmv',
        'flv': 'video/x-flv',
        'mkv': 'video/x-matroska',
        'm4v': 'video/x-m4v',
        '3gp': 'video/3gpp'
    }
    return mapping.get(ext.lower(), 'application/octet-stream')
@app.route('/video/<int:material_id>')
@login_required
def video_content(material_id):
    """Serve video bytes with HTTP Range support for streaming."""
    material = Material.query.get_or_404(material_id)
    if not material.file_path:
        return jsonify({'success': False, 'message': 'File not found'}), 404
    file_path = material.file_path
    if not file_path or '..' in file_path or file_path.startswith('/'):
        return jsonify({'success': False, 'message': 'Invalid file path'}), 400
    full_path = os.path.join(app.static_folder, file_path)
    full_path = os.path.abspath(full_path)
    static_folder = os.path.abspath(app.static_folder)
    if not full_path.startswith(static_folder):
        return jsonify({'success': False, 'message': 'Invalid file path'}), 400
    if not os.path.exists(full_path):
        return jsonify({'success': False, 'message': 'File not found'}), 404
    file_size = os.path.getsize(full_path)
    range_header = request.headers.get('Range', None)
    ext = get_file_format(os.path.basename(full_path))
    mime = _guess_video_mime(ext)
    def generate(start_byte: int, end_byte: int, chunk_size: int = 1024 * 1024):
        with open(full_path, 'rb') as f:
            f.seek(start_byte)
            bytes_left = end_byte - start_byte + 1
            while bytes_left > 0:
                read_len = min(chunk_size, bytes_left)
                data = f.read(read_len)
                if not data:
                    break
                bytes_left -= len(data)
                yield data
    if range_header:
        try:
            units, range_spec = range_header.split('=')
            if units.strip().lower() != 'bytes':
                raise ValueError('Unsupported units')
            start_str, end_str = range_spec.split('-')
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
            start = max(0, start)
            end = min(end, file_size - 1)
            if start > end:
                start, end = 0, file_size - 1
            resp = Response(
                generate(start, end),
                status=206,
                mimetype=mime,
                direct_passthrough=True
            )
            resp.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
            resp.headers.add('Accept-Ranges', 'bytes')
            resp.headers.add('Content-Length', str(end - start + 1))
            return resp
        except Exception:
            pass
    resp = Response(
        generate(0, file_size - 1),
        mimetype=mime,
        direct_passthrough=True
    )
    resp.headers.add('Content-Length', str(file_size))
    resp.headers.add('Accept-Ranges', 'bytes')
    return resp
@app.route('/track_video_progress', methods=['POST'])
@login_required
def track_video_progress():
    try:
        data = request.get_json(force=True) or {}
        material_id = data.get('material_id')
        progress = float(data.get('progress', 0))
        log_admin_action('video_progress', 'materials', material_id, f'Progress: {progress:.2f}%')
        return jsonify({'success': True})
    except Exception:
        return jsonify({'success': False}), 400
@app.route('/track_video_completion', methods=['POST'])
@login_required
def track_video_completion():
    try:
        data = request.get_json(force=True) or {}
        material_id = data.get('material_id')
        completed = bool(data.get('completed'))
        if completed:
            log_admin_action('video_completed', 'materials', material_id, 'Video completed')
        return jsonify({'success': True})
    except Exception:
        return jsonify({'success': False}), 400
@app.route('/read/<int:material_id>')
@login_required
def read_material(material_id):
    """Online reading/viewing of materials"""
    app.logger.info(f"read_material called with material_id: {material_id}")
    try:
        material = Material.query.get_or_404(material_id)
    except Exception as e:
        app.logger.error(f"Error loading material {material_id}: {e}")
        flash('Material not found.', 'error')
        return redirect(url_for('index'))
    if material.is_video:
        flash('Videos can be watched in the video player.', 'info')
        return redirect(url_for('stream_video', material_id=material_id))
    try:
        access_status = current_user.get_access_status()
    except Exception:
        access_status = "limited"
    if current_user.is_admin or current_user.has_active_access():
        pass
    elif not current_user.can_view_material_free(material_id):
        flash('You have already viewed this material. Please pay to view again.', 'error')
        return redirect(url_for('material_detail', material_id=material_id))
    else:
        view_count = current_user.get_material_view_count(material_id)
        if view_count == 0:
            material_view = MaterialView(
                user_id=current_user.id,
                material_id=material_id,
                view_count=1
            )
            db.session.add(material_view)
            db.session.commit()
        access_status = "limited"
    if not material.file_path:
        flash('File not found.', 'error')
        return redirect(url_for('material_detail', material_id=material_id))
    file_path = material.file_path
    if not file_path or '..' in file_path or file_path.startswith('/'):
        flash('Invalid file path.', 'error')
        return redirect(url_for('material_detail', material_id=material_id))
    full_file_path = os.path.join(app.static_folder, file_path)
    full_file_path = os.path.abspath(full_file_path)
    static_folder = os.path.abspath(app.static_folder)
    if not full_file_path.startswith(static_folder):
        flash('Invalid file path.', 'error')
        return redirect(url_for('material_detail', material_id=material_id))
    if not os.path.exists(full_file_path):
        flash('File not found.', 'error')
        return redirect(url_for('material_detail', material_id=material_id))
    file_format = material.file_format.lower() if material.file_format else ''
    actual_extension = get_file_format(os.path.basename(full_file_path)).lower()
    viewable_formats = ['pdf', 'docx', 'doc']
    can_view_online = actual_extension in viewable_formats or file_format in viewable_formats
    if access_status != "limited":
        access_type = "subscription" if current_user.has_active_access() else "limited"
        log_admin_action(f'{access_type}_material_view', 'materials', material_id, f'{access_type.title()} material view: {material.title}')
    file_url = url_for('static', filename=material.file_path)
    return render_template('read_material.html',
                         material=material,
                         file_url=file_url,
                         file_format=actual_extension,
                         can_view_online=can_view_online)
@app.route('/download/<int:material_id>')
@login_required
def download_material(material_id):
    """Download material based on trial/subscription access, optionally in different format"""
    material = Material.query.get_or_404(material_id)
    access_status = current_user.get_access_status()
    if current_user.is_admin or current_user.has_active_access():
        pass
    elif not current_user.can_view_material_free(material_id):
        flash('You have already viewed this material. Please pay to download again.', 'error')
        return redirect(url_for('material_detail', material_id=material_id))
    else:
        view_count = current_user.get_material_view_count(material_id)
        if view_count == 0:
            material_view = MaterialView(
                user_id=current_user.id,
                material_id=material_id,
                view_count=1
            )
            db.session.add(material_view)
            db.session.commit()
        access_status = "limited"
    if access_status == "limited":
        can_download, message = current_user.can_download_limited(material)
        if not can_download:
            flash(f'{message}. Subscribe to access unlimited materials!', 'error')
            return redirect(url_for('material_detail', material_id=material_id))
    if not material.file_path:
        flash('File not found.', 'error')
        return redirect(url_for('material_detail', material_id=material_id))
    file_path = material.file_path
    if not file_path or '..' in file_path or file_path.startswith('/'):
        flash('Invalid file path.', 'error')
        return redirect(url_for('material_detail', material_id=material_id))
    full_file_path = os.path.join(app.static_folder, file_path)
    full_file_path = os.path.abspath(full_file_path)
    static_folder = os.path.abspath(app.static_folder)
    if not full_file_path.startswith(static_folder):
        flash('Invalid file path.', 'error')
        return redirect(url_for('material_detail', material_id=material_id))
    if not os.path.exists(full_file_path):
        flash('File not found.', 'error')
        return redirect(url_for('material_detail', material_id=material_id))
    actual_extension = get_file_format(os.path.basename(full_file_path))
    file_to_download = full_file_path
    download_name = f"{material.title}.{actual_extension}"
    if access_status == "limited":
        download_type = "video" if material.is_video else "document"
        limited_download = LimitedAccessDownload(
            user_id=current_user.id,
            material_id=material_id,
            download_type=download_type
        )
        db.session.add(limited_download)
        db.session.commit()
        log_admin_action('limited_download', 'materials', material_id, f'Limited access download: {material.title}')
    else:
        active_subscription = current_user.subscriptions.filter(
            Subscription.is_active == True,
            Subscription.payment_status == 'paid',
            Subscription.end_date > datetime.now(timezone.utc)
        ).first()
        if active_subscription and not active_subscription.can_access_material():
            flash(f'You have reached your limit of {active_subscription.max_materials} materials for this subscription period.', 'error')
            return redirect(url_for('material_detail', material_id=material_id))
        if active_subscription:
            active_subscription.increment_access()
            db.session.commit()
        access_type = "subscription" if current_user.has_active_access() else "limited"
        if actual_extension and isinstance(actual_extension, str) and actual_extension.strip():
            format_note = f" as {actual_extension.upper()}"
        else:
            format_note = ""
        log_admin_action(f'{access_type}_download', 'materials', material_id, f'{access_type.title()} download: {material.title}{format_note}')
    return send_from_directory(
        os.path.dirname(file_to_download),
        os.path.basename(file_to_download),
        as_attachment=True,
        download_name=download_name
    )
@app.route('/search')
def search():
    query = request.args.get('q', '')
    category_id = request.args.get('category', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    page = request.args.get('page', 1, type=int)
    materials_query = Material.query.options(
        db.joinedload(Material.category)
    ).filter_by(is_active=True)
    if query:
        materials_query = materials_query.filter(
            Material.title.contains(query) |
            Material.description.contains(query)
        )
    if category_id:
        materials_query = materials_query.filter_by(category_id=category_id)
    materials = materials_query.order_by(Material.created_at.desc()).paginate(
        page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False
    )
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    return render_template('search_results.html',
                         materials=materials,
                         query=query,
                         categories=categories,
                         selected_category=category_id,
                         min_price=min_price,
                         max_price=max_price)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html', form=form)
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            return redirect(next_page)
        else:
            flash('Invalid email or password.', 'error')
    return render_template('auth/login.html', form=form)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in. Each material offers one free first view.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html', form=form)
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
                flash('Email service is not configured. Please contact the administrator.', 'error')
                return redirect(url_for('forgot_password'))
            token = str(uuid.uuid4())
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({'used': True})
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            db.session.add(reset_token)
            db.session.commit()
            try:
                send_password_reset_email(user, token)
                flash('Password reset instructions have been sent to your email address.', 'success')
            except Exception as e:
                flash('There was an error sending the email. Please try again later.', 'error')
                print(f"Email error: {e}")
        else:
            flash('If an account with that email exists, password reset instructions have been sent.', 'info')
        return redirect(url_for('login'))
    return render_template('auth/forgot_password.html', form=form)
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not reset_token or not reset_token.is_valid():
        flash('Invalid or expired password reset link.', 'error')
        return redirect(url_for('forgot_password'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = reset_token.user
        user.set_password(form.password.data)
        reset_token.used = True
        db.session.commit()
        flash('Your password has been reset successfully. You can now log in with your new password.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/reset_password.html', form=form, token=token)
def send_password_reset_email(user, token):
    """Send password reset email to user"""
    reset_url = url_for('reset_password', token=token, _external=True)
    if app.config.get('PREFERRED_URL_SCHEME') == 'https' and reset_url.startswith('http://'):
        reset_url = reset_url.replace('http://', 'https://', 1)
    msg = Message(
        subject='Password Reset Request - Pcmlegacy',
        recipients=[user.email],
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    msg.html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color:
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color:
            <p>Hello {user.first_name},</p>
            <p>You recently requested to reset your password for your Pcmlegacy account. Click the button below to reset your password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background-color:
                    Reset Password
                </a>
            </div>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color:
            <p><strong>Important:</strong></p>
            <ul>
                <li>This link will expire in 1 hour</li>
                <li>If you didn't request this password reset, please ignore this email</li>
                <li>For security reasons, this link can only be used once</li>
            </ul>
            <p>If you have any questions, please contact our support team.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid
            <p style="font-size: 12px; color:
                This email was sent from Pcmlegacy. If you didn't request this password reset, please ignore this email.
            </p>
        </div>
    </body>
    </html>
    """
    mail.send(msg)
@app.route('/profile')
@login_required
def profile():
    access_status = current_user.get_access_status()
    active_subscription = None
    if access_status.startswith("subscription_"):
        active_subscription = current_user.subscriptions.filter(
            Subscription.is_active == True,
            Subscription.payment_status == 'paid',
            Subscription.end_date > datetime.now(timezone.utc)
        ).first()
    help_requests = current_user.help_requests.order_by(HelpRequest.created_at.desc()).all()
    return render_template('user/profile.html',
                         access_status=access_status,
                         active_subscription=active_subscription,
                         help_requests=help_requests)
@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    return render_template('user/edit_profile.html', form=form)
@app.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        try:
            if not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect.', 'danger')
                return render_template('user/change_password.html', form=form)
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while changing your password. Please try again.', 'danger')
            print(f"Error changing password: {e}")
            traceback.print_exc()
    return render_template('user/change_password.html', form=form)
@app.route('/admin')
@login_required
def admin_dashboard():
    try:
        try:
            db.session.execute(text('SELECT 1'))
        except Exception as db_error:
            print(f"Database connection error: {db_error}")
            traceback.print_exc()
            flash('Database connection error. Please contact the administrator.', 'error')
            return redirect(url_for('index'))
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('index'))
        try:
            total_users = User.query.count()
        except Exception as e:
            print(f"Error getting total_users: {e}")
            total_users = 0
        try:
            total_materials = Material.query.count()
        except Exception as e:
            print(f"Error getting total_materials: {e}")
            total_materials = 0
        try:
            total_categories = Category.query.count()
        except Exception as e:
            print(f"Error getting total_categories: {e}")
            total_categories = 0
        try:
            total_downloads = DownloadRecord.query.count()
        except Exception as e:
            print(f"Error getting total_downloads: {e}")
            total_downloads = 0
        try:
            total_subscriptions = Subscription.query.count()
            active_subscriptions = Subscription.query.filter(Subscription.is_active == True).count()
        except Exception as e:
            print(f"Error getting subscription stats: {e}")
            total_subscriptions = 0
            active_subscriptions = 0
        try:
            total_plans = SubscriptionPlan.query.count()
        except Exception as e:
            print(f"Error getting total_plans: {e}")
            total_plans = 0
        try:
            total_visitors = VisitorRecord.query.count()
        except Exception as e:
            print(f"Error getting total_visitors: {e}")
            total_visitors = 0
        try:
            unique_visitors = db.session.query(func.count(func.distinct(VisitorRecord.ip_address))).scalar() or 0
        except Exception as e:
            print(f"Error getting unique_visitors: {e}")
            traceback.print_exc()
            unique_visitors = 0
        try:
            total_page_views = PageView.query.count()
        except Exception as e:
            print(f"Error getting total_page_views: {e}")
            total_page_views = 0
        try:
            recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        except Exception as e:
            print(f"Error getting recent_users: {e}")
            recent_users = []
        try:
            recent_materials = Material.query.options(
                db.joinedload(Material.category)
            ).order_by(Material.created_at.desc()).limit(5).all()
        except Exception as e:
            print(f"Error getting recent_materials: {e}")
            traceback.print_exc()
            recent_materials = []
        try:
            recent_subscriptions = Subscription.query.options(
                db.joinedload(Subscription.user)
            ).order_by(Subscription.created_at.desc()).limit(5).all()
        except Exception as e:
            print(f"Error getting recent_subscriptions: {e}")
            recent_subscriptions = []
        return render_template('admin/dashboard.html',
                             total_users=total_users,
                             total_materials=total_materials,
                             total_categories=total_categories,
                             total_downloads=total_downloads,
                             total_subscriptions=total_subscriptions,
                             active_subscriptions=active_subscriptions,
                             total_plans=total_plans,
                             total_visitors=total_visitors,
                             unique_visitors=unique_visitors,
                             total_page_views=total_page_views,
                             recent_users=recent_users,
                             recent_materials=recent_materials,
                             recent_subscriptions=recent_subscriptions)
    except Exception as e:
        print("=" * 80)
        print("ERROR IN admin_dashboard:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        traceback.print_exc()
        print("=" * 80)
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))
@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(
        page=page, per_page=app.config['ADMIN_ITEMS_PER_PAGE'], error_out=False
    )
    return render_template('admin/users.html', users=users)
@app.route('/admin/users/<int:user_id>/details')
@login_required
def admin_user_details(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    user = User.query.get_or_404(user_id)
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': user.phone,
            'is_admin': user.is_admin,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
    })
@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    if form.validate_on_submit():
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.email = form.email.data
        user.phone = form.phone.data
        user.is_active = form.is_active.data
        if user.id != current_user.id:
            user.is_admin = form.is_admin.data
        db.session.commit()
        log_admin_action('Updated user', 'users', user.id, f"Email: {user.email}")
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_users'))
    return render_template('admin/edit_user.html',
                         form=form,
                         user=user)
@app.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def admin_toggle_user_status(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'You cannot deactivate yourself'}), 400
    data = request.get_json()
    user.is_active = data.get('is_active', not user.is_active)
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    log_admin_action(f'User {status}', 'users', user.id, f"Email: {user.email}")
    return jsonify({'success': True, 'message': f'User {status} successfully'})
@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'You cannot delete yourself'}), 400
    if user.is_admin:
        return jsonify({'success': False, 'message': 'Cannot delete admin users'}), 400
    email = user.email
    try:
        DownloadRecord.query.filter_by(user_id=user_id).delete()
        VisitorRecord.query.filter_by(user_id=user_id).delete()
        PageView.query.filter_by(user_id=user_id).delete()
        Subscription.query.filter_by(user_id=user_id).delete()
        PasswordResetToken.query.filter_by(user_id=user_id).delete()
        LimitedAccessDownload.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()
        log_admin_action('Deleted user', 'users', user_id, f"Email: {email}")
        return jsonify({'success': True, 'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        log_admin_action('Failed to delete user', 'users', user_id, f"Error: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to delete user: {str(e)}'}), 500
@app.route('/admin/users/<int:user_id>/reset-material-views', methods=['POST'])
@login_required
def admin_reset_material_views(user_id):
    """Reset user's material views - gives fresh first views on all materials"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    user = User.query.get_or_404(user_id)
    try:
        MaterialView.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        log_admin_action('Reset material views', 'users', user_id, f"Reset material views for {user.email} - fresh first views available")
        return jsonify({
            'success': True,
            'message': f'Material views reset successfully. {user.get_full_name()} can now get free first view on all materials again.'
        })
    except Exception as e:
        db.session.rollback()
        log_admin_action('Failed to reset material views', 'users', user_id, f"Error: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to reset material views: {str(e)}'}), 500
@app.route('/admin/materials')
@login_required
def admin_materials():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    materials = Material.query.options(db.joinedload(Material.category)).paginate(
        page=page, per_page=app.config['ADMIN_ITEMS_PER_PAGE'], error_out=False
    )
    return render_template('admin/materials.html', materials=materials)
@app.route('/admin/materials/add', methods=['GET', 'POST'])
@login_required
def admin_add_material():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    form = MaterialForm()
    if form.validate_on_submit():
        print(f"DEBUG - Form pages data: {form.pages.data}")
        print(f"DEBUG - Form pages data type: {type(form.pages.data)}")
        material = Material(
            title=form.title.data,
            description=form.description.data,
            price=0,
            category_id=form.category_id.data,
            file_size=form.file_size.data,
            file_format=form.file_format.data,
            pages=form.pages.data if form.pages.data else 0,
            stock_quantity=0,
            is_digital=form.is_digital.data,
            is_active=form.is_active.data,
            is_free=True,
            is_video=form.is_video.data,
            video_duration=form.video_duration.data,
            video_quality=form.video_quality.data
        )
        if form.file.data:
            filename = save_file(form.file.data, 'materials')
            if filename:
                material.file_path = f"uploads/materials/{filename}"
                material.file_format = get_file_format(filename)
                if is_video_file(filename):
                    material.is_video = True
                    file_size = os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], 'materials', filename))
                    if file_size > 100 * 1024 * 1024:
                        material.video_quality = 'HD'
                    elif file_size > 50 * 1024 * 1024:
                        material.video_quality = 'SD'
                    else:
                        material.video_quality = 'Low'
            else:
                flash('Failed to save uploaded file. Please try again.', 'error')
                return render_template('admin/material_form.html', form=form, title='Add Material', action='add')
        else:
            if form.is_video.data:
                flash('Please upload a video file for Video Material.', 'error')
                return render_template('admin/material_form.html', form=form, title='Add Material', action='add')
        if form.image.data:
            filename = save_file(form.image.data, 'images')
            if filename:
                material.image_path = f"uploads/images/{filename}"
        if form.video_thumbnail.data:
            filename = save_file(form.video_thumbnail.data, 'images')
            if filename:
                material.video_thumbnail = f"uploads/images/{filename}"
        db.session.add(material)
        db.session.commit()
        log_admin_action('Added material', 'materials', material.id, f"Title: {material.title}")
        flash('Material added successfully!', 'success')
        return redirect(url_for('admin_materials'))
    return render_template('admin/material_form.html', form=form, title='Add Material', action='add')
@app.route('/admin/subscriptions')
@login_required
def admin_subscriptions():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    subscriptions = Subscription.query.options(
        db.joinedload(Subscription.user)
    ).paginate(
        page=page, per_page=app.config['ADMIN_ITEMS_PER_PAGE'], error_out=False
    )
    return render_template('admin/subscriptions.html', subscriptions=subscriptions)
@app.route('/admin/subscriptions/add', methods=['GET', 'POST'])
@login_required
def admin_add_subscription():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    form = SubscriptionForm()
    if form.validate_on_submit():
        subscription = Subscription(
            user_id=form.user_id.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            max_materials=form.max_materials.data
        )
        db.session.add(subscription)
        db.session.commit()
        log_admin_action('Added subscription', 'subscriptions', subscription.id, f"User: {subscription.user.email}")
        flash('Subscription added successfully!', 'success')
        return redirect(url_for('admin_subscriptions'))
    return render_template('admin/subscription_form.html', form=form, title='Add Subscription', action='add')
@app.route('/admin/subscriptions/edit/<int:subscription_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_subscription(subscription_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    subscription = Subscription.query.get_or_404(subscription_id)
    form = SubscriptionForm(obj=subscription)
    if form.validate_on_submit():
        subscription.user_id = form.user_id.data
        subscription.start_date = form.start_date.data
        subscription.end_date = form.end_date.data
        subscription.max_materials = form.max_materials.data
        subscription.notes = form.notes.data
        db.session.commit()
        log_admin_action('Updated subscription', 'subscriptions', subscription.id, f"User: {subscription.user.email}")
        flash('Subscription updated successfully!', 'success')
        return redirect(url_for('admin_subscriptions'))
    return render_template('admin/subscription_form.html', form=form, title='Edit Subscription', action='edit')
@app.route('/admin/subscriptions/delete/<int:subscription_id>')
@login_required
def admin_delete_subscription(subscription_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    subscription = Subscription.query.get_or_404(subscription_id)
    user_email = subscription.user.email
    db.session.delete(subscription)
    db.session.commit()
    log_admin_action('Deleted subscription', 'subscriptions', subscription_id, f"User: {user_email}")
    flash('Subscription deleted successfully!', 'success')
    return redirect(url_for('admin_subscriptions'))
@app.route('/admin/subscription-plans')
@login_required
def admin_subscription_plans():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    plans = SubscriptionPlan.query.order_by(SubscriptionPlan.sort_order, SubscriptionPlan.name).all()
    return render_template('admin/subscription_plans.html', plans=plans)
@app.route('/admin/subscription-plans/add', methods=['GET', 'POST'])
@login_required
def admin_add_subscription_plan():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    form = SubscriptionPlanForm()
    if form.validate_on_submit():
        plan = SubscriptionPlan(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            duration_days=form.duration_days.data,
            max_materials=form.max_materials.data,
            features=form.features.data,
            is_active=form.is_active.data,
            is_popular=form.is_popular.data,
            sort_order=form.sort_order.data
        )
        db.session.add(plan)
        db.session.commit()
        log_admin_action('Added subscription plan', 'subscription_plans', plan.id, f"Plan: {plan.name}")
        flash('Subscription plan added successfully!', 'success')
        return redirect(url_for('admin_subscription_plans'))
    return render_template('admin/subscription_plan_form.html', form=form, title='Add Subscription Plan', action='add')
@app.route('/admin/subscription-plans/edit/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_subscription_plan(plan_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    form = SubscriptionPlanForm(obj=plan)
    if form.validate_on_submit():
        plan.name = form.name.data
        plan.description = form.description.data
        plan.price = form.price.data
        plan.duration_days = form.duration_days.data
        plan.max_materials = form.max_materials.data
        plan.features = form.features.data
        plan.is_active = form.is_active.data
        plan.is_popular = form.is_popular.data
        plan.sort_order = form.sort_order.data
        db.session.commit()
        log_admin_action('Updated subscription plan', 'subscription_plans', plan.id, f"Plan: {plan.name}")
        flash('Subscription plan updated successfully!', 'success')
        return redirect(url_for('admin_subscription_plans'))
    return render_template('admin/subscription_plan_form.html', form=form, title='Edit Subscription Plan', action='edit')
@app.route('/admin/subscription-plans/delete/<int:plan_id>', methods=['POST'])
@login_required
def admin_delete_subscription_plan(plan_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    plan_name = plan.name
    active_subscriptions = plan.subscriptions.filter(Subscription.is_active == True).count()
    if active_subscriptions > 0:
        flash(f'Cannot delete plan "{plan_name}" - it has {active_subscriptions} active subscriptions.', 'error')
        return redirect(url_for('admin_subscription_plans'))
    db.session.delete(plan)
    db.session.commit()
    log_admin_action('Deleted subscription plan', 'subscription_plans', plan_id, f"Plan: {plan_name}")
    flash('Subscription plan deleted successfully!', 'success')
    return redirect(url_for('admin_subscription_plans'))
@app.route('/admin/subscription-plans/toggle/<int:plan_id>', methods=['POST'])
@login_required
def admin_toggle_subscription_plan(plan_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    plan.is_active = not plan.is_active
    db.session.commit()
    status = 'activated' if plan.is_active else 'deactivated'
    log_admin_action(f'Toggled subscription plan ({status})', 'subscription_plans', plan.id, f"Plan: {plan.name}")
    flash(f'Subscription plan {status} successfully!', 'success')
    return redirect(url_for('admin_subscription_plans'))
@app.route('/subscriptions')
@login_required
def subscriptions():
    """Display available subscription plans for users"""
    if current_user.is_admin:
        flash('Admin users have full access to all materials. No subscription needed.', 'info')
        return redirect(url_for('admin_dashboard'))
    material_id = request.args.get('material_id', type=int)
    material = None
    if material_id:
        material = Material.query.get(material_id)
    plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.sort_order, SubscriptionPlan.name).all()
    return render_template('subscriptions.html', plans=plans, material=material, material_id=material_id)
@app.route('/subscription/purchase/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def purchase_subscription(plan_id):
    """Purchase a subscription plan with payment validation and duplicate prevention"""
    material_id = request.args.get('material_id', type=int)
    redirect_url = url_for('dashboard')
    if material_id:
        redirect_url = url_for('material_detail', material_id=material_id)
    if request.method == 'POST':
        if not check_rate_limit(user_id=current_user.id, ip_address=request.remote_addr):
            flash('Too many payment requests. Please wait before trying again.', 'error')
            if material_id:
                return redirect(url_for('subscriptions', material_id=material_id))
            return redirect(url_for('subscriptions'))
        cleanup_expired_payments()
    if current_user.is_admin:
        flash('Admin users have full access to all materials. No subscription needed.', 'info')
        return redirect(url_for('admin_dashboard'))
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    if not plan.is_active:
        flash('This subscription plan is not available.', 'error')
        if material_id:
            return redirect(url_for('subscriptions', material_id=material_id))
        return redirect(url_for('subscriptions'))
    existing_active = current_user.subscriptions.filter(
        Subscription.is_active == True,
        Subscription.payment_status == 'paid',
        Subscription.end_date > datetime.now(timezone.utc)
    ).first()
    if existing_active:
        flash(f'You already have an active subscription that expires on {existing_active.end_date.strftime("%Y-%m-%d")}.', 'info')
        return redirect(url_for('dashboard'))
    pending_subscription = current_user.subscriptions.filter(
        Subscription.payment_status == 'pending',
        Subscription.is_active == True
    ).order_by(Subscription.created_at.desc()).first()
    if pending_subscription:
        time_since_creation = datetime.now(timezone.utc) - pending_subscription.created_at
        if time_since_creation < timedelta(hours=1):
            flash('You have a pending subscription payment. Please complete the payment or wait for it to expire.', 'warning')
            return redirect(url_for('dashboard'))
        else:
            pending_subscription.is_active = False
            pending_subscription.payment_status = 'failed'
            db.session.commit()
    form = SubscriptionPaymentForm()
    form.plan_id.data = plan_id
    if form.validate_on_submit():
        payment_method = form.payment_method.data
        mobile_payment_method_id = form.mobile_payment_method.data
        if payment_method == 'mobile_payment' and not mobile_payment_method_id:
            flash('Please select a mobile payment method.', 'error')
            mobile_payment_methods = MobilePaymentMethod.query.filter_by(is_active=True).all()
            return render_template('purchase_subscription.html', plan=plan, form=form, material_id=material_id, mobile_payment_methods=mobile_payment_methods)
        if payment_method == 'bank_transfer' and not form.payment_reference.data:
            flash('Please provide a payment reference number for bank transfer.', 'error')
            mobile_payment_methods = MobilePaymentMethod.query.filter_by(is_active=True).all()
            return render_template('purchase_subscription.html', plan=plan, form=form, material_id=material_id, mobile_payment_methods=mobile_payment_methods)
        subscription = Subscription(
            user_id=current_user.id,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=plan.duration_days),
            max_materials=plan.max_materials,
            payment_status='pending'
        )
        db.session.add(subscription)
        db.session.commit()
        payment_details = {
            'payment_method': payment_method,
            'mobile_payment_method_id': mobile_payment_method_id,
            'payment_reference': form.payment_reference.data,
            'notes': form.notes.data,
            'plan_price': str(plan.price),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        if payment_method == 'mobile_payment' and mobile_payment_method_id:
            mobile_payment = MobilePaymentMethod.query.get(mobile_payment_method_id)
            if mobile_payment and current_user.phone:
                try:
                    msisdn_input = current_user.phone.strip()
                    msisdn = normalize_msisdn(msisdn_input)
                    amount_str = f"{Decimal(plan.price):.2f}"
                    conversation_id = generate_conversation_id()
                    reference = f"SUB{subscription.id}{uuid.uuid4().hex[:6].upper()}"
                    mpesa_transaction = MpesaTransaction(
                        user_id=current_user.id,
                        material_id=None,
                        msisdn=msisdn,
                        amount=plan.price,
                        currency=current_app.config.get('MPESA_CURRENCY', 'TZS'),
                        conversation_id=conversation_id,
                        transaction_reference=reference,
                        status='pending'
                    )
                    db.session.add(mpesa_transaction)
                    db.session.commit()
                    client = MpesaClient(current_app.config, logger=current_app.logger)
                    metadata = {}
                    callback_url = current_app.config.get('MPESA_CALLBACK_URL')
                    if callback_url:
                        metadata['input_CallbackURL'] = f"{callback_url}?subscription_id={subscription.id}"
                    result = client.pay_single_stage(
                        amount=amount_str,
                        msisdn=msisdn,
                        conversation_id=conversation_id,
                        transaction_reference=reference,
                        description=f"Subscription: {plan.name}",
                        metadata=metadata or None
                    )
                    mpesa_transaction.status = 'submitted'
                    mpesa_transaction.response_payload = result
                    db.session.commit()
                    flash('MPesa payment request sent. Please approve the prompt on your phone to complete the subscription.', 'success')
                    return redirect(redirect_url)
                except (MpesaConfigError, MpesaRequestError, ValueError) as e:
                    current_app.logger.error(f"MPesa payment failed for subscription: {e}")
                    flash(f'MPesa payment could not be processed: {str(e)}. Please use manual payment method or contact support.', 'warning')
        flash('Subscription request submitted successfully! Please complete payment to activate your subscription. An admin will verify and activate your subscription once payment is confirmed.', 'success')
        return redirect(redirect_url)
    mobile_payment_methods = MobilePaymentMethod.query.filter_by(is_active=True).all()
    return render_template('purchase_subscription.html', plan=plan, form=form, material_id=material_id, mobile_payment_methods=mobile_payment_methods)
@app.route('/admin/subscriptions/activate/<int:subscription_id>', methods=['POST'])
@login_required
def admin_activate_subscription(subscription_id):
    """Activate a subscription (admin only)"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    subscription = Subscription.query.get_or_404(subscription_id)
    if subscription.end_date < datetime.now(timezone.utc):
        flash('This subscription has expired. Please create a new subscription or extend the end date.', 'error')
        return redirect(url_for('admin_subscriptions'))
    subscription.payment_status = 'paid'
    subscription.is_active = True
    db.session.commit()
    log_admin_action('Activated subscription', 'subscriptions', subscription.id, f"User: {subscription.user.email}")
    flash('Subscription activated successfully!', 'success')
    return redirect(url_for('admin_subscriptions'))
@app.route('/admin/subscriptions/deactivate/<int:subscription_id>', methods=['POST'])
@login_required
def admin_deactivate_subscription(subscription_id):
    """Deactivate a subscription (admin only)"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    subscription = Subscription.query.get_or_404(subscription_id)
    subscription.is_active = False
    db.session.commit()
    log_admin_action('Deactivated subscription', 'subscriptions', subscription.id, f"User: {subscription.user.email}")
    flash('Subscription deactivated successfully!', 'success')
    return redirect(url_for('admin_subscriptions'))
@app.route('/admin/payments/cleanup', methods=['POST'])
@login_required
def admin_cleanup_payments():
    """Manually trigger cleanup of expired payments (admin only)"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    cleaned_count = cleanup_expired_payments()
    flash(f'Cleaned up {cleaned_count} expired payment(s).', 'success')
    return redirect(url_for('admin_dashboard'))
@app.route('/admin/mobile-payments')
@login_required
def admin_mobile_payments():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    mobile_payment_methods = MobilePaymentMethod.query.all()
    return render_template('admin/mobile_payments.html', mobile_payment_methods=mobile_payment_methods)
@app.route('/admin/mobile-payments/add', methods=['GET', 'POST'])
@login_required
def admin_add_mobile_payment():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    form = MobilePaymentMethodForm()
    if form.validate_on_submit():
        payment_method = MobilePaymentMethod(
            name=form.name.data,
            display_name=form.display_name.data,
            phone_number=form.phone_number.data,
            account_name=form.account_name.data,
            instructions=form.instructions.data,
            icon=form.icon.data,
            is_active=form.is_active.data,
            supports_click_to_pay=form.supports_click_to_pay.data
        )
        db.session.add(payment_method)
        db.session.commit()
        log_admin_action('Created payment method', 'mobile_payment_methods', payment_method.id, f"Name: {payment_method.name}")
        flash('Payment method added successfully!', 'success')
        return redirect(url_for('admin_mobile_payments'))
    return render_template('admin/mobile_payment_form.html', form=form, title='Add Payment Method', action='add')
@app.route('/admin/mobile-payments/edit/<int:method_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_mobile_payment(method_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    payment_method = MobilePaymentMethod.query.get_or_404(method_id)
    form = MobilePaymentMethodForm(obj=payment_method)
    if form.validate_on_submit():
        payment_method.name = form.name.data
        payment_method.display_name = form.display_name.data
        payment_method.phone_number = form.phone_number.data
        payment_method.account_name = form.account_name.data
        payment_method.instructions = form.instructions.data
        payment_method.icon = form.icon.data
        payment_method.is_active = form.is_active.data
        payment_method.supports_click_to_pay = form.supports_click_to_pay.data
        db.session.commit()
        log_admin_action('Updated payment method', 'mobile_payment_methods', payment_method.id, f"Name: {payment_method.name}")
        flash('Payment method updated successfully!', 'success')
        return redirect(url_for('admin_mobile_payments'))
    return render_template('admin/mobile_payment_form.html', form=form, title='Edit Payment Method', action='edit')
@app.route('/admin/mobile-payments/toggle/<int:method_id>', methods=['POST'])
@login_required
def admin_toggle_mobile_payment(method_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    payment_method = MobilePaymentMethod.query.get_or_404(method_id)
    payment_method.is_active = not payment_method.is_active
    db.session.commit()
    status = 'activated' if payment_method.is_active else 'deactivated'
    log_admin_action(f'Toggled payment method ({status})', 'mobile_payment_methods', payment_method.id, f"Name: {payment_method.name}")
    flash(f'Payment method {status} successfully!', 'success')
    return redirect(url_for('admin_mobile_payments'))
@app.route('/admin/mobile-payments/delete/<int:method_id>', methods=['POST'])
@login_required
def admin_delete_mobile_payment(method_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    payment_method = MobilePaymentMethod.query.get_or_404(method_id)
    name = payment_method.name
    db.session.delete(payment_method)
    db.session.commit()
    log_admin_action('Deleted payment method', 'mobile_payment_methods', method_id, f"Name: {name}")
    flash('Payment method deleted successfully!', 'success')
    return redirect(url_for('admin_mobile_payments'))
@app.route('/admin/visitor-stats')
@login_required
def admin_visitor_stats():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    visitors = VisitorRecord.query.order_by(VisitorRecord.last_visit.desc()).limit(100).all()
    page_views = PageView.query.order_by(PageView.last_viewed.desc()).limit(100).all()
    total_visitors = VisitorRecord.query.count()
    unique_visitors = db.session.query(func.count(func.distinct(VisitorRecord.ip_address))).scalar() or 0
    total_page_views = PageView.query.count()
    return render_template('admin/visitor_stats.html',
                         visitors=visitors,
                         page_views=page_views,
                         total_visitors=total_visitors,
                         unique_visitors=unique_visitors,
                         total_page_views=total_page_views)
@app.route('/admin/database')
@login_required
def admin_database():
    """Database backup, restore, and volume management"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    if not DB_BACKUP_AVAILABLE:
        flash('Database backup functionality is not available.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        db_info = get_database_info()
        db_stats = get_database_statistics()
        backups = list_backups()
        
        # Calculate total backup size
        total_backup_size = sum(b['size'] for b in backups)
        
        return render_template('admin/database.html',
                             db_info=db_info,
                             db_stats=db_stats,
                             backups=backups,
                             total_backup_size=total_backup_size,
                             backup_count=len(backups))
    except Exception as e:
        current_app.logger.error(f"Error loading database page: {e}")
        flash(f'Error loading database information: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))
@app.route('/admin/database/backup', methods=['POST'])
@login_required
def admin_backup_database():
    """Create a database backup"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    if not DB_BACKUP_AVAILABLE:
        return jsonify({'success': False, 'message': 'Backup functionality not available'}), 500
    
    try:
        backup_result = backup_database()
        log_admin_action('Created database backup', 'database', None, 
                        f"Backup: {backup_result['backup_filename']}")
        return jsonify({
            'success': True,
            'message': f"Backup created successfully: {backup_result['backup_filename']}",
            'backup': backup_result
        })
    except Exception as e:
        current_app.logger.error(f"Error creating backup: {e}")
        return jsonify({'success': False, 'message': f'Failed to create backup: {str(e)}'}), 500
@app.route('/admin/database/restore', methods=['POST'])
@login_required
def admin_restore_database():
    """Restore database from backup"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    if not DB_BACKUP_AVAILABLE:
        return jsonify({'success': False, 'message': 'Restore functionality not available'}), 500
    
    backup_filename = request.form.get('backup_filename')
    if not backup_filename:
        return jsonify({'success': False, 'message': 'Backup filename required'}), 400
    
    try:
        restore_result = restore_database(backup_filename, create_backup=True)
        log_admin_action('Restored database from backup', 'database', None,
                        f"Restored from: {backup_filename}")
        return jsonify({
            'success': True,
            'message': f"Database restored successfully from {backup_filename}. Please reload the application.",
            'restore': restore_result
        })
    except Exception as e:
        current_app.logger.error(f"Error restoring database: {e}")
        return jsonify({'success': False, 'message': f'Failed to restore database: {str(e)}'}), 500
@app.route('/admin/database/backup/<filename>/delete', methods=['POST'])
@login_required
def admin_delete_backup(filename):
    """Delete a backup file"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    if not DB_BACKUP_AVAILABLE:
        return jsonify({'success': False, 'message': 'Backup functionality not available'}), 500
    
    try:
        delete_result = delete_backup(filename)
        log_admin_action('Deleted database backup', 'database', None, f"Deleted: {filename}")
        return jsonify({
            'success': True,
            'message': f"Backup {filename} deleted successfully"
        })
    except Exception as e:
        current_app.logger.error(f"Error deleting backup: {e}")
        return jsonify({'success': False, 'message': f'Failed to delete backup: {str(e)}'}), 500
@app.route('/admin/database/download/<filename>')
@login_required
def admin_download_backup(filename):
    """Download a backup file"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    if not DB_BACKUP_AVAILABLE:
        flash('Backup functionality not available.', 'error')
        return redirect(url_for('admin_database'))
    
    try:
        from pathlib import Path
        backup_dir = Path(app.instance_path) / 'backups'
        backup_path = backup_dir / filename
        
        if not backup_path.exists() or not filename.startswith('pcm_store_backup_'):
            flash('Backup file not found or invalid.', 'error')
            return redirect(url_for('admin_database'))
        
        return send_from_directory(
            str(backup_dir),
            filename,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        current_app.logger.error(f"Error downloading backup: {e}")
        flash(f'Error downloading backup: {str(e)}', 'error')
        return redirect(url_for('admin_database'))
@app.route('/admin/news')
@login_required
def admin_news():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    news_articles = News.query.order_by(News.created_at.desc()).paginate(
        page=page, per_page=app.config['ADMIN_ITEMS_PER_PAGE'], error_out=False
    )
    return render_template('admin/news.html', news_articles=news_articles)
@app.route('/admin/news/add', methods=['GET', 'POST'])
@login_required
def admin_add_news():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        excerpt = (request.form.get('summary') or request.form.get('excerpt', '')).strip()
        if not title or len(title) > 200:
            flash('Title is required and must be less than 200 characters.', 'error')
            return redirect(url_for('admin_add_news'))
        if not content:
            flash('Content is required.', 'error')
            return redirect(url_for('admin_add_news'))
        news = News(
            title=title,
            content=content,
            excerpt=excerpt[:500] if excerpt else None,
            author_id=current_user.id,
            is_published=request.form.get('is_published') == 'on'
        )
        db.session.add(news)
        db.session.commit()
        log_admin_action('Created news', 'news', news.id, f"Title: {news.title}")
        flash('News article created successfully!', 'success')
        return redirect(url_for('admin_news'))
    return render_template('admin/add_news.html')
@app.route('/privacy-policy', endpoint='privacy_policy')
def privacy_policy():
    """Privacy Policy page"""
    return render_template('privacy_policy.html')

@app.route('/cookie-preferences', endpoint='cookie_preferences')
def cookie_preferences():
    """Cookie Preferences page"""
    return render_template('cookie_preferences.html')

@app.route('/api-documentation', endpoint='api_documentation')
def api_documentation():
    """API Documentation page"""
    return render_template('api_documentation.html')

@app.route('/admin/terms-of-service', methods=['GET', 'POST'])
@login_required
def admin_terms_of_service():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    try:
        terms = TermsOfService.query.order_by(TermsOfService.updated_at.desc()).first()
        form = TermsOfServiceForm()
        if form.validate_on_submit():
            if terms:
                terms.content = form.content.data
                terms.updated_by = current_user.id
                terms.updated_at = datetime.now(timezone.utc)
                action = 'updated'
            else:
                terms = TermsOfService(
                    content=form.content.data,
                    updated_by=current_user.id
                )
                db.session.add(terms)
                action = 'created'
            db.session.commit()
            log_admin_action(f'Terms of Service {action}', 'terms_of_service', terms.id, f'Terms {action}')
            flash(f'Terms of Service {action} successfully!', 'success')
            return redirect('/admin/terms-of-service')
        if terms:
            form.content.data = terms.content
        return render_template('admin/terms_of_service.html', form=form, terms=terms)
    except Exception as e:
        flash(f'Error loading Terms of Service: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))
@app.route('/admin/terms-of-service/delete', methods=['POST'], endpoint='admin_delete_terms')
@login_required
def admin_delete_terms():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    terms = TermsOfService.query.order_by(TermsOfService.updated_at.desc()).first()
    if terms:
        terms_id = terms.id
        db.session.delete(terms)
        db.session.commit()
        log_admin_action('Deleted Terms of Service', 'terms_of_service', terms_id, 'Terms deleted')
        flash('Terms of Service deleted successfully!', 'success')
    else:
        flash('No Terms of Service found to delete.', 'error')
    return redirect('/admin/terms-of-service')
@app.route('/help-request', methods=['GET', 'POST'])
@login_required
def help_request():
    """User submits help request"""
    from forms import HelpRequestForm
    form = HelpRequestForm()
    if form.validate_on_submit():
        help_request = HelpRequest(
            user_id=current_user.id,
            subject=form.subject.data,
            message=form.message.data,
            status='pending'
        )
        db.session.add(help_request)
        db.session.commit()
        flash('Your help request has been submitted successfully! Admin will respond soon.', 'success')
        return redirect(url_for('profile'))
    return render_template('help_request.html', form=form)
@app.route('/admin/help-requests')
@login_required
def admin_help_requests():
    """Admin view all help requests"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    help_requests = HelpRequest.query.order_by(HelpRequest.created_at.desc()).all()
    pending_count = HelpRequest.query.filter_by(status='pending').count()
    responded_count = HelpRequest.query.filter_by(status='responded').count()
    resolved_count = HelpRequest.query.filter_by(status='resolved').count()
    return render_template('admin/help_requests.html',
                         help_requests=help_requests,
                         pending_count=pending_count,
                         responded_count=responded_count,
                         resolved_count=resolved_count)
@app.route('/admin/help-requests/<int:request_id>/respond', methods=['GET', 'POST'])
@login_required
def admin_respond_help(request_id):
    """Admin responds to help request"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    from forms import AdminResponseForm
    help_request = HelpRequest.query.get_or_404(request_id)
    form = AdminResponseForm()
    if form.validate_on_submit():
        help_request.admin_response = form.admin_response.data
        help_request.status = form.status.data
        help_request.responded_by = current_user.id
        help_request.responded_at = datetime.now(timezone.utc)
        db.session.commit()
        log_admin_action('Responded to help request', 'help_requests', request_id,
                        f'Responded to {help_request.user.email}')
        flash('Response sent successfully!', 'success')
        return redirect(url_for('admin_help_requests'))
    if help_request.admin_response:
        form.admin_response.data = help_request.admin_response
        form.status.data = help_request.status
    return render_template('admin/respond_help.html', form=form, help_request=help_request)
def calculate_top_users():
    """Automatically calculate top 10 users based on:
    1. Unique visit days (number of days user visited the website)
    2. Total downloads (DownloadRecord + LimitedAccessDownload)
    3. Visit frequency (based on last_login activity)
    """
    now = datetime.now(timezone.utc)
    users_with_scores = []
    users = User.query.filter_by(is_active=True, is_admin=False).all()
    for user in users:
        unique_visit_days = db.session.query(func.count(func.distinct(UserVisit.visit_date))).filter(UserVisit.user_id == user.id).scalar() or 0
        download_count = DownloadRecord.query.filter_by(user_id=user.id).count()
        limited_download_count = LimitedAccessDownload.query.filter_by(user_id=user.id).count()
        total_downloads = download_count + limited_download_count
        visit_score = 0
        if user.last_login:
            last_login = user._normalize_datetime(user.last_login) if hasattr(user, '_normalize_datetime') else user.last_login
            if last_login:
                days_since_login = (now - last_login).days
                visit_score = max(0, 100 - days_since_login)
            else:
                visit_score = 0
        visit_days_score = min(unique_visit_days * 2, 730) * 0.4
        download_score = min(total_downloads * 10, 500) * 0.5
        activity_score = visit_score * 0.1
        total_score = visit_days_score + download_score + activity_score
        days_or_months = f"{unique_visit_days} day{'s' if unique_visit_days != 1 else ''}"
        if unique_visit_days >= 30:
            months = unique_visit_days // 30
            days = unique_visit_days % 30
            if days == 0:
                days_or_months = f"{months} month{'s' if months > 1 else ''}"
            else:
                days_or_months = f"{months} month{'s' if months > 1 else ''}, {days} day{'s' if days > 1 else ''}"
        users_with_scores.append({
            'user': user,
            'score': total_score,
            'unique_visit_days': unique_visit_days,
            'total_downloads': total_downloads,
            'days_or_months': days_or_months,
            'visit_score': visit_score
        })
    users_with_scores.sort(key=lambda x: x['score'], reverse=True)
    top_10 = users_with_scores[:10]
    for idx, user_data in enumerate(top_10, 1):
        user_data['serial_number'] = idx
    return top_10
@app.route('/top-10-users')
@login_required
def top_users():
    """Top 10 users leaderboard - only visible to registered users - automatically calculated"""
    calculated_top_users = calculate_top_users()
    top_user_gifts = {}
    for top_user_entry in TopUser.query.filter_by(is_visible=True, status='active').all():
        top_user_gifts[top_user_entry.user_id] = {
            'admin_gift': top_user_entry.admin_gift,
            'status': top_user_entry.status
        }
    visible_top_users = []
    for user_data in calculated_top_users:
        user_id = user_data['user'].id
        if user_id in top_user_gifts:
            user_data['admin_gift'] = top_user_gifts[user_id]['admin_gift']
            user_data['status'] = top_user_gifts[user_id]['status']
        else:
            user_data['admin_gift'] = 0
            user_data['status'] = 'active'
        visible_top_users.append(user_data)
    return render_template('top_users.html', top_users=visible_top_users)
@app.route('/admin/top-users')
@login_required
def admin_top_users():
    """Admin view and manage top 10 users - automatically calculated with admin gift management"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    calculated_top_users = calculate_top_users()
    top_user_gifts = {}
    for top_user_entry in TopUser.query.all():
        top_user_gifts[top_user_entry.user_id] = {
            'admin_gift': top_user_entry.admin_gift,
            'status': top_user_entry.status,
            'is_visible': top_user_entry.is_visible,
            'id': top_user_entry.id
        }
    for user_data in calculated_top_users:
        user_id = user_data['user'].id
        if user_id in top_user_gifts:
            user_data['admin_gift'] = top_user_gifts[user_id]['admin_gift']
            user_data['status'] = top_user_gifts[user_id]['status']
            user_data['is_visible'] = top_user_gifts[user_id]['is_visible']
            user_data['top_user_id'] = top_user_gifts[user_id]['id']
        else:
            user_data['admin_gift'] = 0
            user_data['status'] = 'active'
            user_data['is_visible'] = True
            user_data['top_user_id'] = None
    return render_template('admin/top_users.html', top_users=calculated_top_users)
@app.route('/admin/top-users/add', methods=['GET', 'POST'])
@login_required
def admin_add_top_user():
    """Admin add new top user"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    from forms import TopUserForm
    form = TopUserForm()
    if form.validate_on_submit():
        existing = TopUser.query.filter_by(serial_number=form.serial_number.data).first()
        if existing:
            flash(f'Serial number {form.serial_number.data} is already assigned to another user.', 'error')
            return render_template('admin/add_top_user.html', form=form)
        existing_user = TopUser.query.filter_by(user_id=form.user_id.data).first()
        if existing_user:
            flash('This user is already in the top users list.', 'error')
            return render_template('admin/add_top_user.html', form=form)
        top_user = TopUser(
            user_id=form.user_id.data,
            serial_number=form.serial_number.data,
            days_or_months=form.days_or_months.data,
            admin_gift=form.admin_gift.data or 0,
            status=form.status.data,
            is_visible=form.is_visible.data
        )
        db.session.add(top_user)
        db.session.commit()
        log_admin_action('Added top user', 'top_users', top_user.id, f'Added {top_user.user.email} at position {top_user.serial_number}')
        flash('Top user added successfully!', 'success')
        return redirect(url_for('admin_top_users'))
    return render_template('admin/add_top_user.html', form=form)
@app.route('/admin/top-users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_top_user(user_id):
    """Admin edit top user - set admin gift and status (ranking is automatic)"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    top_user = TopUser.query.filter_by(user_id=user_id).first()
    if not top_user:
        top_user = TopUser(
            user_id=user_id,
            serial_number=1,
            admin_gift=0,
            status='active',
            is_visible=True
        )
        db.session.add(top_user)
        db.session.commit()
    unique_visit_days = db.session.query(func.count(func.distinct(UserVisit.visit_date))).filter(UserVisit.user_id == user.id).scalar() or 0
    download_count = DownloadRecord.query.filter_by(user_id=user.id).count()
    limited_download_count = LimitedAccessDownload.query.filter_by(user_id=user.id).count()
    total_downloads = download_count + limited_download_count
    days_or_months = f"{unique_visit_days} day{'s' if unique_visit_days != 1 else ''}"
    if unique_visit_days >= 30:
        months = unique_visit_days // 30
        days = unique_visit_days % 30
        if days == 0:
            days_or_months = f"{months} month{'s' if months > 1 else ''}"
        else:
            days_or_months = f"{months} month{'s' if months > 1 else ''}, {days} day{'s' if days > 1 else ''}"
    from forms import TopUserForm
    form = TopUserForm()
    form.user_id.data = user_id
    form.days_or_months.data = days_or_months
    form.admin_gift.data = top_user.admin_gift
    form.status.data = top_user.status
    form.is_visible.data = top_user.is_visible
    if form.validate_on_submit():
        top_user.admin_gift = form.admin_gift.data or 0
        top_user.status = form.status.data
        top_user.is_visible = form.is_visible.data
        top_user.days_or_months = days_or_months
        db.session.commit()
        log_admin_action('Updated top user', 'top_users', top_user.id, f'Updated gift for {user.email}')
        flash('Top user updated successfully!', 'success')
        return redirect(url_for('admin_top_users'))
    return render_template('admin/edit_top_user.html', form=form, top_user=top_user, user=user, days_or_months=days_or_months, total_downloads=total_downloads)
@app.route('/admin/top-users/<int:top_user_id>/delete', methods=['POST'])
@login_required
def admin_delete_top_user(top_user_id):
    """Admin delete top user"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    top_user = TopUser.query.get_or_404(top_user_id)
    user_email = top_user.user.email
    db.session.delete(top_user)
    db.session.commit()
    log_admin_action('Deleted top user', 'top_users', top_user_id, f'Deleted {user_email}')
    return jsonify({'success': True, 'message': 'Top user deleted successfully'})
@app.route('/admin/materials/edit/<int:material_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_material(material_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    material = Material.query.get_or_404(material_id)
    form = MaterialForm(obj=material)
    if form.validate_on_submit():
        print(f"DEBUG EDIT - Form pages data: {form.pages.data}")
        print(f"DEBUG EDIT - Form pages data type: {type(form.pages.data)}")
        material.title = form.title.data
        material.description = form.description.data
        material.price = 0
        material.category_id = form.category_id.data
        material.file_size = form.file_size.data
        material.pages = form.pages.data if form.pages.data else 0
        material.is_digital = form.is_digital.data
        material.is_active = form.is_active.data
        material.is_free = True
        material.is_video = form.is_video.data
        material.video_duration = form.video_duration.data
        material.video_quality = form.video_quality.data
        if form.file.data:
            filename = save_file(form.file.data, 'materials')
            if filename:
                material.file_path = f"uploads/materials/{filename}"
                material.file_format = get_file_format(filename)
                if is_video_file(filename):
                    material.is_video = True
                    file_size = os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], 'materials', filename))
                    if file_size > 100 * 1024 * 1024:
                        material.video_quality = 'HD'
                    elif file_size > 50 * 1024 * 1024:
                        material.video_quality = 'SD'
                    else:
                        material.video_quality = 'Low'
            else:
                flash('Failed to save uploaded file. Please try again.', 'error')
                return render_template('admin/edit_material.html', material=material, form=form)
        else:
            if form.is_video.data and not material.file_path:
                flash('Please upload a video file for Video Material.', 'error')
                return render_template('admin/edit_material.html', material=material, form=form)
        if form.image.data:
            filename = save_file(form.image.data, 'images')
            if filename:
                material.image_path = f"uploads/images/{filename}"
        if form.video_thumbnail.data:
            filename = save_file(form.video_thumbnail.data, 'images')
            if filename:
                material.video_thumbnail = f"uploads/images/{filename}"
        db.session.commit()
        log_admin_action('Updated material', 'materials', material.id, f"Title: {material.title}")
        flash('Material updated successfully!', 'success')
        return redirect(url_for('admin_materials'))
    return render_template('admin/edit_material.html', material=material, form=form)
@app.route('/admin/materials/<int:material_id>/delete-file', methods=['POST'])
@login_required
def admin_delete_material_file(material_id):
    """Delete a specific file (file, video, image, or thumbnail) from a material"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    file_type = request.form.get('file_type')
    if not file_type:
        flash('File type not specified.', 'error')
        return redirect(url_for('admin_edit_material', material_id=material_id))
    material = Material.query.get_or_404(material_id)
    file_deleted = False
    file_path_to_delete = None
    try:
        if file_type == 'file':
            if material.file_path:
                file_path_to_delete = os.path.join(app.static_folder, material.file_path)
                if os.path.exists(file_path_to_delete):
                    os.remove(file_path_to_delete)
                    file_deleted = True
                material.file_path = None
                material.file_size = None
                material.file_format = None
                if material.is_video:
                    material.video_duration = None
                    material.video_quality = None
        elif file_type == 'video':
            if material.file_path and material.is_video:
                file_path_to_delete = os.path.join(app.static_folder, material.file_path)
                if os.path.exists(file_path_to_delete):
                    os.remove(file_path_to_delete)
                    file_deleted = True
                material.file_path = None
                material.file_size = None
                material.file_format = None
                material.video_duration = None
                material.video_quality = None
        elif file_type == 'image':
            if material.image_path:
                file_path_to_delete = os.path.join(app.static_folder, material.image_path)
                if os.path.exists(file_path_to_delete):
                    os.remove(file_path_to_delete)
                    file_deleted = True
                material.image_path = None
        elif file_type == 'thumbnail':
            if material.video_thumbnail:
                file_path_to_delete = os.path.join(app.static_folder, material.video_thumbnail)
                if os.path.exists(file_path_to_delete):
                    os.remove(file_path_to_delete)
                    file_deleted = True
                material.video_thumbnail = None
        if file_deleted:
            db.session.commit()
            log_admin_action(f'Deleted {file_type} from material', 'materials', material_id, f"Material: {material.title}")
            flash(f'{file_type.capitalize()} deleted successfully!', 'success')
        else:
            if file_path_to_delete or (file_type in ['file', 'video'] and material.file_path) or \
               (file_type == 'image' and material.image_path) or (file_type == 'thumbnail' and material.video_thumbnail):
                db.session.commit()
                flash(f'{file_type.capitalize()} reference removed from database (file not found on disk).', 'info')
            else:
                flash(f'No {file_type} found to delete.', 'info')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting {file_type}: {e}")
        flash(f'Error deleting {file_type}: {str(e)}', 'error')
    return redirect(url_for('admin_edit_material', material_id=material_id))
@app.route('/admin/materials/delete/<int:material_id>', methods=['POST'])
@login_required
def admin_delete_material(material_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    material = Material.query.get_or_404(material_id)
    title = material.title
    db.session.delete(material)
    db.session.commit()
    log_admin_action('Deleted material', 'materials', material_id, f"Title: {title}")
    flash('Material deleted successfully!', 'success')
    return redirect(url_for('admin_materials'))
@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing downloads and subscription status"""
    try:
        # Get downloads with error handling
        downloads = []
        try:
            downloads = DownloadRecord.query.filter_by(user_id=current_user.id).order_by(DownloadRecord.last_downloaded.desc()).all()
        except Exception as e:
            app.logger.error(f"Error querying downloads: {e}")
            downloads = []
        
        subscription_downloads = downloads
        materials_accessed_count = 0
        active_subscription = None
        
        # Get active subscription with error handling
        try:
            active_subscription = current_user.subscriptions.filter(
                Subscription.is_active == True,
                Subscription.payment_status == 'paid',
                Subscription.end_date > datetime.now(timezone.utc)
            ).first()
            if active_subscription:
                try:
                    materials_accessed_count = active_subscription.materials_accessed
                except AttributeError:
                    materials_accessed_count = 0
        except Exception as e:
            app.logger.error(f"Error getting subscription: {e}")
            active_subscription = None
        
        return render_template('user/dashboard.html',
                             downloads=downloads,
                             subscription_downloads=subscription_downloads,
                             Subscription=Subscription,
                             materials_accessed_count=materials_accessed_count,
                             active_subscription=active_subscription)
    except Exception as e:
        app.logger.error(f"Error in dashboard route: {e}")
        traceback.print_exc()
        flash('An error occurred loading your dashboard. Please try again.', 'error')
        return redirect(url_for('index'))
@app.route('/news')
def news():
    page = request.args.get('page', 1, type=int)
    news_articles = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('news.html', news_articles=news_articles)
@app.route('/robots.txt', endpoint='robots_txt', methods=['GET'])
def robots():
    """Generate robots.txt for SEO"""
    base_url = request.url_root.rstrip('/')
    robots_content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /profile/
Disallow: /dashboard/
Disallow: /download/
Disallow: /stream/
Disallow: /read/
Disallow: /video/
Disallow: /subscription/
Disallow: /reset-password/
Disallow: /track_video_progress
Disallow: /track_video_completion
Sitemap: {base_url}/sitemap.xml
"""
    response = Response(robots_content, mimetype='text/plain', status=200)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response
@app.route('/news/<int:news_id>')
def news_detail(news_id):
    article = News.query.get_or_404(news_id)
    related_news = News.query.filter(News.id != news_id, News.is_published == True).order_by(News.created_at.desc()).limit(3).all()
    return render_template('news_detail.html', news=article, related_news=related_news)
@app.errorhandler(404)
def not_found_error(error):
    if app.config.get('DEBUG'):
        app.logger.debug(f"404 - Path: {request.path}, URL: {request.url}")
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'message': 'Endpoint not found',
            'path': request.path
        }), 404
    return render_template('errors/404.html'), 404
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    print("=" * 80)
    print("500 INTERNAL SERVER ERROR")
    print("=" * 80)
    print(f"Error Type: {type(error).__name__}")
    print(f"Error Message: {str(error)}")
    print("\nTraceback:")
    traceback.print_exc()
    print("=" * 80)
    return render_template('errors/500.html'), 500
if __name__ == '__main__':
    with app.app_context():
        add_missing_columns()
    init_db()
    if app.config.get('DEBUG'):
        print("\nSEO Routes Registered:")
        for rule in app.url_map.iter_rules():
            if 'sitemap' in rule.rule.lower() or 'robots' in rule.rule.lower():
                print(f"  ✓ {rule.rule} -> {rule.endpoint}")
        print()
    import socket
    port = 8000
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    if result == 0:
        port = 8001
        print(f"Port 8000 is in use, using port {port} instead")
    sock.close()
    app.run(debug=True, host='127.0.0.1', port=port, use_reloader=False)
