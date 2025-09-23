
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
[ ] API keys are valid and have appropriate permissions

Environment Variables:
======================
[ ] FLASK_SECRET_KEY - Generated, unique, secure
[ ] SMTP_USERNAME - Real email account for sending
[ ] SMTP_PASSWORD - App-specific password (not account password)
[ ] RECIPIENT_EMAIL - Valid email for receiving contact forms
[ ] API_NINJAS_KEY - Valid API key with sufficient quota
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
