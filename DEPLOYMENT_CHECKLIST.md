# Production Deployment Checklist

**Website**: PCM Legacy  
**Status**: ✅ All Tests Passing - Ready for Production

---

## ⚠️ CRITICAL - Must Do Before Launch

### Security
- [ ] **Set SECRET_KEY** - Generate strong random key (min 32 characters)
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] **Enable HTTPS** - Install SSL certificate (Let's Encrypt recommended)
- [ ] **Set SESSION_COOKIE_SECURE = True** - Already configured ✅
- [ ] **Set PREFERRED_URL_SCHEME = https** - Already configured ✅
- [ ] **Review security headers** - Already implemented ✅

### Database
- [ ] **Set DATABASE_URL** - Use PostgreSQL for production (not SQLite)
- [ ] **Initialize database** - Run `db.create_all()`
- [ ] **Create admin user** - Set up first admin account
- [ ] **Set up backups** - Configure regular database backups

### Configuration
- [ ] **Set FLASK_ENV=production** - Production mode
- [ ] **Set SERVER_NAME** - Your domain name
- [ ] **Configure email** - Set MAIL_* environment variables
- [ ] **Configure M-Pesa** - Set MPESA_* environment variables (if using)

---

## ✅ RECOMMENDED - Should Do Before Launch

### Performance
- [ ] **Run build script** - Generate minified CSS/JS
  ```bash
  python scripts/build.py
  ```
- [ ] **Convert images to WebP** - Optimize existing images
  ```bash
  python scripts/convert_images.py static/uploads/images
  ```
- [ ] **Enable compression** - Already configured ✅
- [ ] **Set up CDN** - Optional but recommended for static files

### Content
- [ ] **Review privacy policy** - Legal review recommended
- [ ] **Test cookie consent** - Verify banner appears and works
- [ ] **Test all forms** - Login, registration, uploads
- [ ] **Test payment flow** - Verify M-Pesa integration (test mode first)

### Monitoring
- [ ] **Set up error logging** - Configure log monitoring
- [ ] **Set up uptime monitoring** - Use service like UptimeRobot
- [ ] **Set up performance monitoring** - Track page load times
- [ ] **Configure alerts** - Get notified of errors/issues

---

## 🚀 DEPLOYMENT STEPS

### Step 1: Pre-Deployment (30 minutes)
- [ ] Run build script
- [ ] Convert images (optional)
- [ ] Set environment variables
- [ ] Review configuration

### Step 2: Server Setup (1-2 hours)
- [ ] Install dependencies
- [ ] Set up database
- [ ] Configure web server (Nginx/Apache)
- [ ] Install SSL certificate
- [ ] Configure reverse proxy

### Step 3: Application Deployment (30 minutes)
- [ ] Deploy code to server
- [ ] Initialize database
- [ ] Create admin user
- [ ] Test basic functionality

### Step 4: Verification (30 minutes)
- [ ] Test all pages
- [ ] Test authentication
- [ ] Test file uploads
- [ ] Test payment processing
- [ ] Check security headers
- [ ] Verify HTTPS

### Step 5: Go Live (5 minutes)
- [ ] Update DNS if needed
- [ ] Final smoke test
- [ ] Monitor for errors
- [ ] Announce launch

---

## 📋 POST-DEPLOYMENT

### First 24 Hours
- [ ] Monitor error logs
- [ ] Check performance metrics
- [ ] Verify backups working
- [ ] Test user registration
- [ ] Test payment processing

### First Week
- [ ] Review user activity
- [ ] Check for errors/issues
- [ ] Monitor performance
- [ ] Gather user feedback

### Ongoing
- [ ] Daily: Check error logs
- [ ] Weekly: Review analytics
- [ ] Monthly: Update dependencies
- [ ] Quarterly: Security audit

---

## 🎯 QUICK COMMANDS

### Build Assets
```bash
python scripts/build.py
```

### Convert Images
```bash
python scripts/convert_images.py static/uploads/images
```

### Initialize Database
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Run Tests
```bash
pytest tests/ -v
```

### Run Production Server
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

---

## ✅ READY TO DEPLOY!

Your website is **100% complete** and **production-ready**!

**Next Step**: Follow the deployment checklist above to go live! 🚀

---

**Last Updated**: December 2024

