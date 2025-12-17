from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import os
db = SQLAlchemy()
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    def _normalize_datetime(self, dt):
        """Normalize datetime to UTC-aware for comparison"""
        if dt is None:
            return None
        try:
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            else:
                return dt.astimezone(timezone.utc)
        except (AttributeError, TypeError):
            if isinstance(dt, datetime):
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt
            return None
    def has_active_access(self):
        """Check if user has active access (subscription only - no more 90-day trial)"""
        if self.is_admin:
            return True
        active_subscription = self.subscriptions.filter(
            Subscription.is_active == True,
            Subscription.payment_status == 'paid',
            Subscription.end_date > datetime.now(timezone.utc)
        ).first()
        return active_subscription is not None
    def get_access_status(self):
        """Get user's current access status"""
        if self.is_admin:
            return "admin"
        active_subscription = self.subscriptions.filter(
            Subscription.is_active == True,
            Subscription.payment_status == 'paid',
            Subscription.end_date > datetime.now(timezone.utc)
        ).first()
        if active_subscription:
            end_date = self._normalize_datetime(active_subscription.end_date)
            now = datetime.now(timezone.utc)
            if end_date:
                days_left = (end_date - now).days
                return f"subscription_{days_left}"
        return "limited"
    def can_download_limited(self, material):
        """Check if user can download with limited access (3 downloads per day, 1 video per day)"""
        if not self.get_access_status() == "limited":
            return False, "No limited access"
        today = datetime.now(timezone.utc).date()
        total_downloads_today = self.limited_downloads.filter(
            LimitedAccessDownload.download_date == today
        ).count()
        if total_downloads_today >= 3:
            return False, "Daily download limit reached (3 downloads per day)"
        if material.is_video:
            video_downloads_today = self.limited_downloads.filter(
                LimitedAccessDownload.download_date == today,
                LimitedAccessDownload.download_type == 'video'
            ).count()
            if video_downloads_today >= 1:
                return False, "Daily video limit reached (1 video per day)"
        return True, "Can download"
    def get_limited_downloads_today(self):
        """Get count of downloads today for limited access users"""
        today = datetime.now(timezone.utc).date()
        return self.limited_downloads.filter(
            LimitedAccessDownload.download_date == today
        ).count()
    def get_limited_video_downloads_today(self):
        """Get count of video downloads today for limited access users"""
        today = datetime.now(timezone.utc).date()
        return self.limited_downloads.filter(
            LimitedAccessDownload.download_date == today,
            LimitedAccessDownload.download_type == 'video'
        ).count()
    def has_viewed_material(self, material_id):
        """Check if user has viewed a material before (for trial: first view is free)"""
        if self.is_admin:
            return True
        material_view = self.material_views.filter_by(material_id=material_id).first()
        return material_view is not None and material_view.view_count > 0
    def get_material_view_count(self, material_id):
        """Get how many times user has viewed a material"""
        if self.is_admin:
            return 999
        material_view = self.material_views.filter_by(material_id=material_id).first()
        return material_view.view_count if material_view else 0
    def can_view_material_free(self, material_id):
        """Check if user can view material for free (first view only)"""
        if self.is_admin or self.has_active_access():
            return True
        view_count = self.get_material_view_count(material_id)
        return view_count == 0
    def __repr__(self):
        return f'<User {self.email}>'
class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(20))
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    level = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    materials = db.relationship('Material', backref='category', lazy='dynamic')
    parent = db.relationship('Category', remote_side=[id], backref='subcategories')
    def __repr__(self):
        return f'<Category {self.name}>'
    @property
    def full_name(self):
        """Get full category name including level"""
        if self.level and not self.name.endswith(f" - {self.level}"):
            return f"{self.name} - {self.level}"
        return self.name
class Material(db.Model):
    __tablename__ = 'materials'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True)
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)  # Size in bytes
    file_format = db.Column(db.String(10))
    pages = db.Column(db.Integer)
    image_path = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    stock_quantity = db.Column(db.Integer, default=0)
    is_digital = db.Column(db.Boolean, default=True)
    is_free = db.Column(db.Boolean, default=False)
    is_video = db.Column(db.Boolean, default=False)
    video_duration = db.Column(db.Integer)  # Duration in seconds
    video_quality = db.Column(db.String(20))
    video_thumbnail = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    def __repr__(self):
        return f'<Material {self.title}>'
class MobilePaymentMethod(db.Model):
    __tablename__ = 'mobile_payment_methods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    icon = db.Column(db.String(20))
    supports_click_to_pay = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    def __repr__(self):
        return f'<MobilePaymentMethod {self.name}>'
class MpesaTransaction(db.Model):
    __tablename__ = 'mpesa_transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=True)
    msisdn = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='TZS')
    conversation_id = db.Column(db.String(64), unique=True, nullable=False)
    transaction_reference = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(30), default='pending')
    response_payload = db.Column(db.JSON, nullable=True)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref='mpesa_transactions')
    material = db.relationship('Material', backref='mpesa_transactions')
    def __repr__(self):
        return f'<MpesaTransaction {self.transaction_reference} - {self.status}>'
class MaterialView(db.Model):
    """Track material views per user - first view is free, subsequent views require payment"""
    __tablename__ = 'material_views'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    view_count = db.Column(db.Integer, default=1)
    first_viewed = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_viewed = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref=db.backref('material_views', lazy='dynamic'))
    material = db.relationship('Material', backref='material_views')
    __table_args__ = (db.UniqueConstraint('user_id', 'material_id', name='unique_user_material_view'),)
    def __repr__(self):
        return f'<MaterialView user:{self.user_id} material:{self.material_id} views:{self.view_count}>'
class DownloadRecord(db.Model):
    __tablename__ = 'download_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    download_type = db.Column(db.String(20), default='purchase')
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    download_count = db.Column(db.Integer, default=1)
    last_downloaded = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref='downloads')
    material = db.relationship('Material', backref='downloads')
    __table_args__ = (db.UniqueConstraint('user_id', 'material_id', name='unique_user_material_download'),)
    def __repr__(self):
        return f'<DownloadRecord {self.material.title} by {self.user.email}>'
class AdminLog(db.Model):
    __tablename__ = 'admin_logs'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(50))
    record_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    def __repr__(self):
        return f'<AdminLog {self.action} by {self.admin_id}>'
class VisitorRecord(db.Model):
    """Track website visitors"""
    __tablename__ = 'visitor_records'
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.Text)
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    referrer = db.Column(db.String(500))
    first_visit = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_visit = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    visit_count = db.Column(db.Integer, default=1)
    is_unique = db.Column(db.Boolean, default=True)
    def __repr__(self):
        return f'<VisitorRecord {self.ip_address} - {self.visit_count} visits>'
class News(db.Model):
    """News articles for the website"""
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(500))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_published = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    published_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    author = db.relationship('User', backref='news_articles')
    def __repr__(self):
        return f'<News {self.title} by {self.author.email}>'
    @property
    def formatted_date(self):
        return self.created_at.strftime('%B %d, %Y')
    @property
    def short_excerpt(self):
        if self.excerpt:
            return self.excerpt
        return self.content[:200] + '...' if len(self.content) > 200 else self.content
class PageView(db.Model):
    """Track most visited pages"""
    __tablename__ = 'page_views'
    id = db.Column(db.Integer, primary_key=True)
    page_url = db.Column(db.String(500), nullable=False)
    page_title = db.Column(db.String(200))
    visitor_id = db.Column(db.Integer, db.ForeignKey('visitor_records.id'))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    referrer = db.Column(db.String(500))
    view_count = db.Column(db.Integer, default=1)
    last_viewed = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    visitor = db.relationship('VisitorRecord', backref='page_views')
    def __repr__(self):
        return f'<PageView {self.page_url} - {self.view_count} views>'
class WishlistItem(db.Model):
    """User wishlist items"""
    __tablename__ = 'wishlist_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref='wishlist_items')
    material = db.relationship('Material', backref='wishlist_items')
    __table_args__ = (db.UniqueConstraint('user_id', 'material_id', name='unique_user_material_wishlist'),)
    def __repr__(self):
        return f'<WishlistItem {self.user.email} - {self.material.title}>'
    @property
    def formatted_date(self):
        return self.added_at.strftime('%B %d, %Y')
class SubscriptionPlan(db.Model):
    """Subscription plans available for users"""
    __tablename__ = 'subscription_plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    max_materials = db.Column(db.Integer, default=100)
    features = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    is_popular = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    def __repr__(self):
        return f'<SubscriptionPlan {self.name}>'
    @property
    def formatted_price(self):
        return f"TZS {self.price:,.0f}"
    @property
    def duration_text(self):
        if self.duration_days == 30:
            return "1 Month"
        elif self.duration_days == 90:
            return "3 Months"
        elif self.duration_days == 180:
            return "6 Months"
        elif self.duration_days == 365:
            return "1 Year"
        else:
            return f"{self.duration_days} Days"
class Subscription(db.Model):
    """User subscription periods managed by admin"""
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id', ondelete='SET NULL'), nullable=True, index=True)
    start_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    end_date = db.Column(db.DateTime, nullable=False, index=True)
    max_materials = db.Column(db.Integer, nullable=False, default=100)
    materials_accessed = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True, index=True)
    payment_status = db.Column(db.String(20), default='pending', index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('subscriptions', lazy='dynamic'))
    plan = db.relationship('SubscriptionPlan', backref='subscriptions')
    def _normalize_datetime(self, dt):
        """Normalize datetime to UTC-aware for comparison"""
        if dt is None:
            return None
        try:
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            else:
                return dt.astimezone(timezone.utc)
        except (AttributeError, TypeError):
            if isinstance(dt, datetime):
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt
            return None
    def is_valid(self):
        """Check if subscription is still valid"""
        try:
            if not self.end_date:
                return False
            now = datetime.now(timezone.utc)
            end_date = self._normalize_datetime(self.end_date)
            if end_date is None:
                return False
            return self.is_active and self.payment_status == 'paid' and now < end_date
        except (TypeError, AttributeError, ValueError):
            return False
    def can_access_material(self):
        """Check if user can access more materials"""
        return self.is_valid() and self.materials_accessed < self.max_materials
    def increment_access(self):
        """Increment materials accessed counter atomically to prevent race conditions"""
        from sqlalchemy import func
        updated = db.session.query(Subscription).filter(
            Subscription.id == self.id,
            Subscription.is_active == True,
            Subscription.payment_status == 'paid',
            Subscription.end_date > datetime.now(timezone.utc),
            Subscription.materials_accessed < Subscription.max_materials
        ).update({
            Subscription.materials_accessed: Subscription.materials_accessed + 1
        }, synchronize_session=False)
        db.session.commit()
        if updated > 0:
            db.session.refresh(self)
            return True
        return False
    @property
    def days_remaining(self):
        """Get days remaining in subscription"""
        try:
            if not self.end_date:
                return 0
            now = datetime.now(timezone.utc)
            end_date = self._normalize_datetime(self.end_date)
            if end_date is None:
                return 0
            if now < end_date:
                return (end_date - now).days
            return 0
        except (TypeError, AttributeError, ValueError):
            return 0
    @property
    def status_text(self):
        """Get human-readable status"""
        try:
            if not self.is_active:
                return "Inactive"
            if not self.end_date:
                return "Unknown"
            now = datetime.now(timezone.utc)
            end_date = self._normalize_datetime(self.end_date)
            if end_date is None:
                return "Unknown"
            if now > end_date:
                return "Expired"
            elif self.payment_status == 'pending':
                return "Pending Payment"
            elif self.payment_status == 'paid':
                return "Active"
            else:
                return "Unknown"
        except (TypeError, AttributeError, ValueError) as e:
            if self.payment_status == 'paid':
                return "Active"
            elif self.payment_status == 'pending':
                return "Pending Payment"
            return "Unknown"
    def __repr__(self):
        return f'<Subscription {self.user.email} - {self.start_date} to {self.end_date}>'
class PasswordResetToken(db.Model):
    """Password reset tokens for forgot password functionality"""
    __tablename__ = 'password_reset_tokens'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref='password_reset_tokens')
    def is_valid(self):
        """Check if token is still valid and not used"""
        if self.used or not self.expires_at:
            return False
        try:
            now = datetime.now(timezone.utc)
            if self.expires_at.tzinfo is None:
                expires_at = self.expires_at.replace(tzinfo=timezone.utc)
            else:
                expires_at = self.expires_at.astimezone(timezone.utc)
            return now < expires_at
        except (AttributeError, TypeError, ValueError):
            return False
    def __repr__(self):
        return f'<PasswordResetToken {self.user.email} - {self.token[:10]}...>'
class LimitedAccessDownload(db.Model):
    """Track daily downloads for users with limited access"""
    __tablename__ = 'limited_access_downloads'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    download_date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    download_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref=db.backref('limited_downloads', lazy='dynamic'))
    material = db.relationship('Material', backref=db.backref('limited_downloads', lazy='dynamic'))
    def __repr__(self):
        return f'<LimitedAccessDownload {self.user.email} - {self.material.title} - {self.download_date}>'
class TermsOfService(db.Model):
    __tablename__ = 'terms_of_service'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updater = db.relationship('User', backref=db.backref('terms_updates', lazy='dynamic'))
    def __repr__(self):
        return f'<TermsOfService updated_at={self.updated_at}>'
class HelpRequest(db.Model):
    """User help requests and admin feedback system"""
    __tablename__ = 'help_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    admin_response = db.Column(db.Text, nullable=True)
    responded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    responded_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('help_requests', lazy='dynamic', order_by='desc(HelpRequest.created_at)'))
    responder = db.relationship('User', foreign_keys=[responded_by])
    def __repr__(self):
        return f'<HelpRequest {self.id} by {self.user.email} - {self.status}>'
    @property
    def formatted_date(self):
        return self.created_at.strftime('%B %d, %Y at %I:%M %p')
    @property
    def response_date(self):
        if self.responded_at:
            return self.responded_at.strftime('%B %d, %Y at %I:%M %p')
        return None
class UserVisit(db.Model):
    """Track user visits by day"""
    __tablename__ = 'user_visits'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    visit_date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    visit_count = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref=db.backref('visits', lazy='dynamic'))
    __table_args__ = (db.UniqueConstraint('user_id', 'visit_date', name='unique_user_visit_date'),)
    def __repr__(self):
        return f'<UserVisit {self.user.email} - {self.visit_date}>'
class TopUser(db.Model):
    """Top 10 Users leaderboard"""
    __tablename__ = 'top_users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    serial_number = db.Column(db.Integer, nullable=False, unique=True)
    days_or_months = db.Column(db.String(50), nullable=True)
    admin_gift = db.Column(db.Numeric(10, 2), default=0)
    status = db.Column(db.String(50), default='active')
    is_visible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref=db.backref('top_user_entry', uselist=False))
    def __repr__(self):
        return f'<TopUser #{self.serial_number} - {self.user.email}>'
    @property
    def formatted_gift(self):
        """Format admin gift amount"""
        if self.admin_gift:
            return f"TZS {self.admin_gift:,.0f}"
        return "TZS 0"
