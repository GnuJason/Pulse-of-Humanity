# Flask Environment Variables - Complete Guide

This guide demonstrates best practices for managing environment variables in Flask applications, with specific examples for your Pulse of Humanity project.

## 📁 Files Created

1. **`config.py`** - Advanced configuration management classes
2. **`flask_config_example.py`** - Application factory pattern example  
3. **`security_audit.py`** - Security audit tool for your current setup
4. **`environment_demo.py`** - Comprehensive demonstration of env var patterns
5. **`flask_env_improvements.py`** - Ready-to-use code for your app.py
6. **`setup_env.py`** - Interactive tool to create .env files
7. **`.env.secure`** - Template with generated secret key
8. **`PRODUCTION_CHECKLIST.md`** - Deployment checklist
9. **`env_validation_snippet.py`** - Validation code snippet

## 🚀 Quick Start

### 1. For Development

```bash
# Create a secure .env file interactively
python setup_env.py

# Or copy the template and edit manually
cp .env.secure .env
# Edit .env with your actual credentials

# Test your configuration
python environment_demo.py
```

### 2. Improve Your Existing app.py

Copy the functions from `flask_env_improvements.py` into your `app.py`:

```python
# Add these imports
import os
import sys
import secrets
from typing import Optional

# Add the utility functions (from flask_env_improvements.py)
def load_dotenv_if_exists():
    # ... (copy function)

def validate_environment():
    # ... (copy function)

# Replace your Flask configuration with:
def configure_flask_from_env(app):
    # ... (copy function)

# Update your main startup:
def main():
    # ... (copy function)

if __name__ == "__main__":
    main()
```

### 3. Run Security Audit

```bash
python security_audit.py
```

## 🔐 Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_SECRET_KEY` | Flask session signing key (64+ chars) | `ca79b2f6f6dd827d...` |
| `SMTP_USERNAME` | Email account for sending | `your-email@domain.com` |
| `SMTP_PASSWORD` | App-specific password | `your-app-password` |
| `RECIPIENT_EMAIL` | Contact form recipient | `contact@yourdomain.com` |
| `ADMIN_REANCHOR_TOKEN` | Token for `POST /admin/reanchor` | `long-random-token` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | Environment mode |
| `FLASK_DEBUG` | `0` | Debug mode (1/0) |
| `PORT` | `5000` | Server port |
| `DOMAIN` | `localhost:5000` | Your domain |
| `SMTP_SERVER` | `smtp.mailfence.com` | SMTP server |
| `SMTP_PORT` | `587` | SMTP port |
| `POP_CACHE_TTL` | `60` | Cache timeout |
| `RUN_UPDATER` | `0` | Run annual anchor checker (1/0) |
| `POP_ANCHOR_MONTH` | `1` | Annual anchor month |
| `POP_ANCHOR_DAY` | `1` | Annual anchor day |
| `WPP_DATA_DIR` | repo root | Directory containing the three UN WPP CSV files |

## 🛡️ Security Best Practices

### ✅ Do This

- **Generate strong secret keys**: Use `python -c "import secrets; print(secrets.token_hex(32))"`
- **Validate on startup**: Check all required variables are set
- **Use app-specific passwords**: For SMTP, use app passwords not main passwords
- **Mask secrets in logs**: Never log full secret values
- **Use .env for development**: Keep local secrets out of code
- **Set environment directly in production**: Don't use .env files on servers

### ❌ Don't Do This

- **Commit .env files**: Add `.env` to `.gitignore`
- **Use weak secrets**: Avoid short or predictable keys
- **Log secret values**: Use masking functions for logs
- **Use same secrets everywhere**: Generate unique keys per environment
- **Ignore validation errors**: Fix config issues before deployment

## 🔧 Current Usage in Your App

Your app already uses environment variables in these ways:

```python
# Current patterns in your app.py:
CACHE_TTL = int(os.getenv("POP_CACHE_TTL", "60"))
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-in-production')
DEBUG = os.getenv("FLASK_DEBUG") == "1"
PORT = int(os.getenv("PORT", "5000"))
anchor_month = int(os.getenv("POP_ANCHOR_MONTH", "1"))
anchor_day = int(os.getenv("POP_ANCHOR_DAY", "1"))
wpp_data_dir = os.getenv("WPP_DATA_DIR")

# SMTP configuration:
smtp_server = os.getenv('SMTP_SERVER', 'smtp.mailfence.com')
smtp_port = int(os.getenv('SMTP_PORT', '587'))
smtp_username = os.getenv('SMTP_USERNAME')
smtp_password = os.getenv('SMTP_PASSWORD')
recipient_email = os.getenv('RECIPIENT_EMAIL')

# Domain configuration:
domain = os.getenv('DOMAIN', 'your-domain.com')
```

## 📋 Production Deployment

### Heroku
```bash
heroku config:set FLASK_SECRET_KEY=your-64-char-secret-key
heroku config:set FLASK_ENV=production
heroku config:set FLASK_DEBUG=0
heroku config:set SMTP_USERNAME=your-email@domain.com
heroku config:set SMTP_PASSWORD=your-app-password
heroku config:set RECIPIENT_EMAIL=contact@yourdomain.com
heroku config:set POP_ANCHOR_MONTH=1
heroku config:set POP_ANCHOR_DAY=1
heroku config:set WPP_DATA_DIR=/app/wpp
heroku config:set ADMIN_REANCHOR_TOKEN=your-admin-token
heroku config:set DOMAIN=yourdomain.com
```

### Docker
```yaml
# docker-compose.yml
environment:
  - FLASK_SECRET_KEY=${FLASK_SECRET_KEY}
  - FLASK_ENV=production
  - FLASK_DEBUG=0
  - SMTP_USERNAME=${SMTP_USERNAME}
  - SMTP_PASSWORD=${SMTP_PASSWORD}
  - RECIPIENT_EMAIL=${RECIPIENT_EMAIL}
    - POP_ANCHOR_MONTH=${POP_ANCHOR_MONTH}
    - POP_ANCHOR_DAY=${POP_ANCHOR_DAY}
    - WPP_DATA_DIR=${WPP_DATA_DIR}
    - ADMIN_REANCHOR_TOKEN=${ADMIN_REANCHOR_TOKEN}
  - DOMAIN=${DOMAIN}
```

### Linux Server
```bash
# /etc/systemd/system/pulse-of-humanity.service
[Service]
Environment=FLASK_SECRET_KEY=your-secret-key
Environment=FLASK_ENV=production
Environment=FLASK_DEBUG=0
EnvironmentFile=/etc/pulse-of-humanity/environment
```

## 🔍 Validation Patterns

### Type Conversion
```python
# Boolean variables
debug = os.getenv('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes', 'on')

# Integer variables with validation
port = int(os.getenv('PORT', '5000'))
if not (1 <= port <= 65535):
    raise ValueError(f"Invalid port: {port}")

# Required variables
secret_key = os.environ['FLASK_SECRET_KEY']  # Raises KeyError if not set
```

### Safe Logging
```python
def mask_secret(secret, visible_chars=4):
    """Mask secret for logging."""
    if not secret:
        return "<not set>"
    if len(secret) <= visible_chars:
        return "*" * len(secret)
    return "*" * (len(secret) - visible_chars) + secret[-visible_chars:]

# Usage
print(f"Secret key: {mask_secret(secret_key)}")  # "Secret key: ****5910"
```

## 🚨 Common Issues

1. **Weak Secret Keys**: Use 64+ character random strings
2. **Debug Mode in Production**: Set `FLASK_DEBUG=0` for production
3. **Missing Required Variables**: Validate on startup
4. **Committed Secrets**: Add `.env` to `.gitignore`
5. **SMTP Authentication**: Use app-specific passwords

## 📖 Additional Resources

- [Flask Configuration Documentation](https://flask.palletsprojects.com/en/2.3.x/config/)
- [12-Factor App Configuration](https://12factor.net/config)
- [OWASP Configuration Management](https://owasp.org/www-community/vulnerabilities/Configuration_Management)

## 🎯 Next Steps

1. **Review generated files**: Check `.env.secure` and other created files
2. **Update your app.py**: Integrate the improvement functions
3. **Test locally**: Verify everything works with your .env file
4. **Deploy safely**: Use environment variables (not .env) in production
5. **Monitor and rotate**: Regularly update secrets and monitor access

Remember: Environment variables are a fundamental security boundary. Handle them with care!