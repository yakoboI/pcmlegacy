# PCM Legacy Store

A comprehensive educational materials management system with subscription-based access, M-Pesa payment integration, and full admin dashboard functionality.

## Features

### User Features
- **Material Management**: Browse, search, and access educational materials (PDFs, videos, documents)
- **Subscription Plans**: Multiple subscription tiers with different access levels
- **M-Pesa Integration**: Seamless payment processing via Vodacom M-Pesa
- **User Dashboard**: Track downloads, subscriptions, and viewing history
- **Material Categories**: Organized by subjects (Physics, Mathematics, Chemistry) and education levels
- **Video Streaming**: Built-in video player with progress tracking
- **News System**: Stay updated with educational news and announcements
- **Top Users Leaderboard**: Gamification with user rankings
- **Limited Free Access**: Trial access to materials for new users

### Admin Features
- **Comprehensive Dashboard**: Analytics, statistics, and overview
- **Material Management**: Upload, edit, delete materials with multiple file formats
- **User Management**: User accounts, status control, and activity tracking
- **Subscription Management**: Create and manage subscription plans
- **Payment Management**: Mobile payment methods and transaction tracking
- **News Management**: Publish and manage news articles
- **Visitor Statistics**: Track page views and visitor analytics
- **Help Request System**: Respond to user inquiries
- **Activity Logging**: Complete audit trail of admin actions

### Technical Features
- **SEO Optimized**: Sitemap.xml and robots.txt for search engines
- **Responsive Design**: Mobile-friendly interface
- **File Upload**: Support for multiple file formats (PDF, video, documents, images)
- **Password Reset**: Email-based password recovery
- **Rate Limiting**: Protection against abuse
- **Session Management**: Secure user sessions
- **Database Migrations**: Automatic schema updates

## Requirements

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (default) or PostgreSQL/MySQL for production

## Installation

### 1. Clone or Download the Repository

```bash
cd pcm
```

### 2. Create a Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-in-production

# Database (Optional - defaults to SQLite)
DATABASE_URL=sqlite:///pcm_store.db

# Email Configuration (Required for password reset)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@pcmlegacy.store

# M-Pesa Configuration (Required for payments)
MPESA_API_KEY=your-mpesa-api-key
MPESA_PUBLIC_KEY=your-mpesa-public-key
MPESA_SERVICE_PROVIDER_CODE=your-service-provider-code
MPESA_COUNTRY=TZN
MPESA_CURRENCY=TZS
MPESA_ENV=sandbox
MPESA_IPG_ADDRESS=openapi.m-pesa.com
MPESA_IPG_PORT=443
MPESA_IPG_ORIGIN=*
MPESA_SESSION_PATH=/your/session/path
MPESA_C2B_SINGLE_STAGE_PATH=/your/c2b/path
MPESA_CALLBACK_URL=https://yourdomain.com/api/mpesa/callback

# Production Settings (Optional)
SERVER_NAME=pcmlegacy.store
PREFERRED_URL_SCHEME=https
REDIS_URL=memory://
```

**Note:** For Gmail, you'll need to create an [App Password](https://support.google.com/accounts/answer/185833) instead of using your regular password.

### 5. Initialize the Database

The database will be automatically created when you first run the application. Default categories, subscription plans, and an admin user will be created.

### 6. Run the Application

```bash
python app.py
```

The application will start on `http://127.0.0.1:8000` (or port 8001 if 8000 is in use).

## Default Admin Credentials

On first run, a default admin user is created:

- **Email:** `admin@pcmlegacy.store`
- **Password:** `admin123`

**⚠️ IMPORTANT:** Change the default admin password immediately after first login!

## Project Structure

```
pcm/
├── app.py                 # Main application file
├── config.py              # Configuration settings
├── models.py              # Database models
├── forms.py               # WTForms form definitions
├── wsgi.py                # WSGI configuration for deployment
├── requirements.txt       # Python dependencies
├── instance/              # Database files (SQLite)
├── static/                # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── uploads/           # User uploaded files
├── templates/             # Jinja2 templates
│   ├── admin/             # Admin panel templates
│   ├── auth/              # Authentication templates
│   ├── errors/            # Error pages
│   └── user/              # User dashboard templates
├── services/              # Service modules
│   └── mpesa_client.py    # M-Pesa integration
└── portal-sdk/            # M-Pesa Portal SDK
```

## Configuration

### Development Mode

The application runs in development mode by default with:
- Debug mode enabled
- SQLite database (`pcm_store_dev.db`)
- Detailed error pages

### Production Mode

Set the `FLASK_ENV` environment variable to `production`:

```env
FLASK_ENV=production
SECRET_KEY=your-strong-secret-key-here
```

**Production Requirements:**
- Set a strong `SECRET_KEY`
- Configure proper database (PostgreSQL recommended)
- Enable HTTPS (`SESSION_COOKIE_SECURE=True`)
- Configure proper `SERVER_NAME`
- Set up proper M-Pesa production credentials

## Deployment

### PythonAnywhere

1. Upload your code to PythonAnywhere
2. Update `wsgi.py` with your actual path:
   ```python
   path = '/home/yourusername/pcmlegacy'  # Update this
   ```
3. Configure environment variables in the web app settings
4. Point your web app to `wsgi.py`

### Other Platforms

The application is compatible with:
- Heroku
- DigitalOcean App Platform
- AWS Elastic Beanstalk
- Any WSGI-compatible hosting service

## Supported File Types

- **Documents:** PDF, DOC, DOCX, TXT, PPT, PPTX, XLS, XLSX
- **Videos:** MP4, AVI, MOV, WMV, FLV, WEBM, MKV, M4V, 3GP
- **Images:** PNG, JPG, JPEG, GIF
- **Archives:** ZIP, RAR, 7Z

Maximum file size: 512 MB

## API Endpoints

### Public Endpoints
- `GET /` - Home page
- `GET /search` - Search materials
- `GET /news` - News articles
- `GET /material/<id>` - Material details
- `GET /sitemap.xml` - SEO sitemap
- `GET /robots.txt` - SEO robots.txt

### User Endpoints (Requires Login)
- `GET /dashboard` - User dashboard
- `GET /profile` - User profile
- `GET /download/<id>` - Download material
- `GET /read/<id>` - Read material online
- `GET /stream/<id>` - Stream video
- `POST /api/materials/<id>/mpesa-click-to-pay` - M-Pesa payment

### Admin Endpoints (Requires Admin)
- `/admin/*` - Admin dashboard and management

## Troubleshooting

### Database Issues
- Delete the database file in `instance/` folder and restart the app to recreate
- Check file permissions on the `instance/` directory

### Email Not Working
- Verify SMTP credentials in `.env`
- For Gmail, use App Password instead of regular password
- Check firewall/network restrictions

### M-Pesa Integration Issues
- Verify all M-Pesa credentials in `.env`
- Ensure callback URL is publicly accessible
- Check M-Pesa sandbox/production environment settings

### File Upload Issues
- Check `static/uploads/` directory permissions
- Verify file size is under 512 MB
- Ensure file extension is in allowed list

## Security Notes

- Always use a strong `SECRET_KEY` in production
- Enable HTTPS in production
- Regularly update dependencies
- Keep sensitive credentials in `.env` file (never commit to version control)
- Review and adjust rate limiting settings as needed

## License

[Add your license here]

## Support

For issues, questions, or contributions, please contact the development team.

## Changelog

### Version 1.0
- Initial release
- Core material management
- M-Pesa payment integration
- Subscription system
- Admin dashboard
- User management
- SEO features

