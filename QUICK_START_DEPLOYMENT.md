# Quick Start - Production Deployment

**Status**: ✅ Ready to Deploy

---

## 🚀 Quick Deployment Steps

### 1. Build Production Assets (5 minutes)
```bash
# Install build tools (optional but recommended)
pip install cssmin jsmin

# Build minified files
python scripts/build.py
```

### 2. Convert Images to WebP (10-30 minutes)
```bash
# Convert all existing images
python scripts/convert_images.py static/uploads/images
```

### 3. Set Environment Variables ⚠️ CRITICAL
```bash
# Windows PowerShell
$env:FLASK_ENV="production"
$env:SECRET_KEY="your-strong-secret-key-min-32-chars"
$env:DATABASE_URL="postgresql://user:pass@host/db"

# Linux/Mac
export FLASK_ENV=production
export SECRET_KEY="your-strong-secret-key-min-32-chars"
export DATABASE_URL="postgresql://user:pass@host/db"
```

### 4. Initialize Database
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 5. Create Admin User
```bash
python -c "
from app import app, db
from models import User
app.app_context().push()
admin = User(email='admin@yourdomain.com', first_name='Admin', last_name='User', is_admin=True, is_active=True)
admin.set_password('your-secure-password')
db.session.add(admin)
db.session.commit()
print('Admin created!')
"
```

### 6. Run Production Server
```bash
# Install Gunicorn
pip install gunicorn

# Run
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

---

## ✅ Pre-Launch Checklist

- [ ] SECRET_KEY set (strong random key)
- [ ] Database configured
- [ ] HTTPS enabled (SSL certificate)
- [ ] Admin user created
- [ ] Build script run
- [ ] Images converted (optional)
- [ ] Privacy policy reviewed
- [ ] Payment processing tested

---

## 🎯 You're Ready!

Follow the steps above and your website will be live! 🚀

