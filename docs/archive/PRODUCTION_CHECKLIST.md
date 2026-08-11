
PRODUCTION DEPLOYMENT CHECKLIST

Security:
=========
[ ] Generated strong SECRET_KEY (64+ character random hex)
[ ] Set FLASK_ENV=production
[ ] Set FLASK_DEBUG=0
[ ] All placeholder values replaced with real credentials
[ ] .env file is NOT committed to version control
[ ] Using HTTPS in production
[ ] Database credentials are secure
[ ] Annual anchor configuration reviewed and correct for production

Environment Variables:
======================
[ ] FLASK_SECRET_KEY - Generated, unique, secure
[ ] SMTP_USERNAME - Real email account for sending
[ ] SMTP_PASSWORD - App-specific password (not account password)
[ ] RECIPIENT_EMAIL - Valid email for receiving contact forms
[ ] POP_ANCHOR_MONTH / POP_ANCHOR_DAY - Annual authoritative re-anchor date configured
[ ] ADMIN_REANCHOR_TOKEN - Strong token stored securely if admin route is enabled
[ ] DOMAIN - Production domain name (no http/https prefix)

Monitoring:
===========
[ ] Application logging configured
[ ] Error tracking set up (Sentry, etc.)
[ ] Health check endpoints working
[ ] SSL certificate valid and auto-renewing

Performance:
============
[ ] Database connection pooling configured
[ ] Static files served efficiently
[ ] Caching configured appropriately
[ ] Rate limiting in place

Backup:
=======
[ ] Database backups automated
[ ] Application secrets backed up securely
[ ] Deployment process documented
[ ] Rollback plan tested
