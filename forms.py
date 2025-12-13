from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, DecimalField, IntegerField, SelectField, FileField, EmailField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional, ValidationError
from wtforms.widgets import TextArea
from models import User, Category, Material, SubscriptionPlan
class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(min=10, max=20)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
class PasswordResetRequestForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')
class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    password2 = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')
class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    phone = StringField('Phone Number', validators=[Optional(), Length(min=10, max=20)])
    submit = SubmitField('Update Profile')
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    new_password2 = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')
class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(min=2, max=50)])
    description = TextAreaField('Description', validators=[Optional()], widget=TextArea())
    icon = StringField('Icon (Emoji)', validators=[Optional(), Length(max=20)])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Category')
    def validate_name(self, name):
        category = Category.query.filter_by(name=name.data).first()
        if category is not None:
            raise ValidationError('Please use a different category name.')
class MobilePaymentMethodForm(FlaskForm):
    name = StringField('Method Name', validators=[DataRequired(), Length(max=50)],
                      render_kw={'placeholder': 'e.g., mpesa_vodacom'})
    display_name = StringField('Display Name', validators=[DataRequired(), Length(max=100)],
                              render_kw={'placeholder': 'e.g., M-Pesa (Vodacom)'})
    phone_number = StringField('Payment Number', validators=[DataRequired(), Length(max=20)],
                              render_kw={'placeholder': 'e.g., +255 123 456 789'})
    account_name = StringField('Account Name', validators=[DataRequired(), Length(max=100)],
                              render_kw={'placeholder': 'e.g., Pcmlegacy Tanzania'})
    instructions = TextAreaField('Payment Instructions', validators=[Optional()],
                               render_kw={'placeholder': 'Step-by-step payment instructions', 'rows': 6})
    icon = StringField('Icon', validators=[Optional(), Length(max=20)],
                      render_kw={'placeholder': 'e.g., 📱'})
    is_active = BooleanField('Active', default=True)
    supports_click_to_pay = BooleanField('Supports Click to Pay (M-Pesa API)', default=False,
                                        description='Enable if this method supports instant M-Pesa Click to Pay')
    submit = SubmitField('Save Payment Method')
class MaterialForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=2, max=200)])
    description = TextAreaField('Description', validators=[DataRequired()], widget=TextArea())
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    file = FileField('Material File', validators=[Optional()])
    image = FileField('Cover Image', validators=[Optional()])
    file_size = StringField('File Size', validators=[Optional()], render_kw={'readonly': True, 'placeholder': 'Auto-detected from file'})
    file_format = StringField('File Format', validators=[Optional()], render_kw={'readonly': True, 'placeholder': 'Auto-detected from file'})
    pages = IntegerField('Pages', validators=[Optional(), NumberRange(min=0)])
    is_digital = BooleanField('Digital Material', default=True)
    is_video = BooleanField('Video Material', default=False)
    video_duration = StringField('Video Duration', validators=[Optional()], render_kw={'placeholder': 'e.g., 5:30'})
    video_quality = StringField('Video Quality', validators=[Optional()], render_kw={'placeholder': 'e.g., HD, 4K'})
    video_thumbnail = FileField('Video Thumbnail', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Material')
    def __init__(self, *args, **kwargs):
        super(MaterialForm, self).__init__(*args, **kwargs)
        categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
        choices = []
        main_categories = [c for c in categories if c.parent_id is None]
        subcategories = [c for c in categories if c.parent_id is not None]
        for main_cat in main_categories:
            choices.append((main_cat.id, main_cat.name))
            for sub_cat in subcategories:
                if sub_cat.parent_id == main_cat.id:
                    choices.append((sub_cat.id, f"  └─ {sub_cat.level}"))
        self.category_id.choices = choices
class UserForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(min=10, max=20)])
    is_admin = BooleanField('Admin User')
    is_active = BooleanField('Active User', default=True)
    submit = SubmitField('Update User')
class SubscriptionForm(FlaskForm):
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    max_materials = IntegerField('Max Materials', validators=[DataRequired(), NumberRange(min=1)], default=100)
    notes = TextAreaField('Notes', validators=[Optional()], widget=TextArea())
    submit = SubmitField('Create Subscription')
    def __init__(self, *args, **kwargs):
        super(SubscriptionForm, self).__init__(*args, **kwargs)
        self.user_id.choices = [(u.id, f"{u.first_name} {u.last_name} ({u.email})") for u in User.query.filter_by(is_active=True).all()]
class SubscriptionPlanForm(FlaskForm):
    name = StringField('Plan Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional()], widget=TextArea())
    price = DecimalField('Price (TZS)', validators=[DataRequired(), NumberRange(min=0)], places=2)
    duration_days = IntegerField('Duration (Days)', validators=[DataRequired(), NumberRange(min=1)])
    max_materials = IntegerField('Max Materials', validators=[DataRequired(), NumberRange(min=1)], default=100)
    features = TextAreaField('Features (one per line)', validators=[Optional()], widget=TextArea())
    is_active = BooleanField('Active', default=True)
    is_popular = BooleanField('Popular Plan', default=False)
    sort_order = IntegerField('Sort Order', validators=[Optional(), NumberRange(min=0)], default=0)
    submit = SubmitField('Save Plan')
class SubscriptionPaymentForm(FlaskForm):
    plan_id = SelectField('Select Plan', coerce=int, validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[
        ('mobile_payment', 'Mobile Payment'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash Payment')
    ], validators=[DataRequired()])
    mobile_payment_method = SelectField('Mobile Payment Method', coerce=int, validators=[Optional()])
    payment_reference = StringField('Payment Reference', validators=[Optional()])
    notes = TextAreaField('Additional Notes', validators=[Optional()], widget=TextArea())
    submit = SubmitField('Process Payment')
    def __init__(self, *args, **kwargs):
        super(SubscriptionPaymentForm, self).__init__(*args, **kwargs)
        self.plan_id.choices = [(p.id, f"{p.name} - {p.formatted_price}") for p in SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.sort_order).all()]
        from models import MobilePaymentMethod
        self.mobile_payment_method.choices = [(m.id, f"{m.display_name} ({m.phone_number})") for m in MobilePaymentMethod.query.filter_by(is_active=True).all()]
class NewsForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    excerpt = TextAreaField('Excerpt', validators=[Optional(), Length(max=500)],
                           widget=TextArea(), render_kw={'rows': 3})
    content = TextAreaField('Content', validators=[DataRequired()],
                           widget=TextArea(), render_kw={'rows': 10})
    is_published = BooleanField('Published', default=True)
    is_featured = BooleanField('Featured Article', default=False)
    submit = SubmitField('Save News Article')
class TermsOfServiceForm(FlaskForm):
    content = TextAreaField('Terms of Service Content', validators=[DataRequired()],
                           widget=TextArea(), render_kw={'rows': 20})
    submit = SubmitField('Update Terms of Service')
class HelpRequestForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired(), Length(min=5, max=200)],
                         render_kw={'placeholder': 'Brief description of your request or issue'})
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10)],
                           widget=TextArea(), render_kw={'rows': 8, 'placeholder': 'Describe what is missing, needs improvement, or not working well...'})
    submit = SubmitField('Submit Help Request')
class AdminResponseForm(FlaskForm):
    admin_response = TextAreaField('Admin Response', validators=[DataRequired()],
                                  widget=TextArea(), render_kw={'rows': 6, 'placeholder': 'Type your response to the user...'})
    status = SelectField('Status', choices=[('responded', 'Responded'), ('resolved', 'Resolved')],
                        validators=[DataRequired()])
    submit = SubmitField('Send Response')
class TopUserForm(FlaskForm):
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    serial_number = IntegerField('Serial Number (Position 1-10)', validators=[DataRequired(), NumberRange(min=1, max=10)])
    days_or_months = StringField('Days/Months', validators=[Optional()], render_kw={'placeholder': 'e.g., 90 days, 3 months'})
    admin_gift = DecimalField('Admin Gift Amount (TZS)', validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    status = SelectField('Status', choices=[('active', 'Active'), ('inactive', 'Inactive'), ('featured', 'Featured')],
                        validators=[DataRequired()], default='active')
    is_visible = BooleanField('Visible to Public', default=True)
    submit = SubmitField('Save Top User')
    def __init__(self, *args, **kwargs):
        super(TopUserForm, self).__init__(*args, **kwargs)
        self.user_id.choices = [(u.id, f"{u.first_name} {u.last_name} ({u.email})") for u in User.query.filter_by(is_active=True).all()]
