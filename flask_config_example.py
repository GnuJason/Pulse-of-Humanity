"""
Improved Flask App Configuration Example

This shows how to refactor your current app.py to use better
environment variable practices with validation and security.
"""

import os
import sys
from flask import Flask
from config import get_config, load_environment_variables, get_env_required, mask_secret


def create_app():
    """
    Application factory pattern with proper environment variable handling.
    """
    # Load environment variables from .env file (for development)
    load_environment_variables()
    
    # Get configuration
    config = get_config()
    
    # Validate required environment variables
    missing_vars = config.validate_required_vars()
    if missing_vars:
        print("❌ Missing required environment variables:", file=sys.stderr)
        for var in missing_vars:
            print(f"   - {var}", file=sys.stderr)
        
        # In production, exit if critical vars are missing
        if not config.DEBUG:
            print("Exiting due to missing required configuration.", file=sys.stderr)
            sys.exit(1)
        else:
            print("⚠️  Running in debug mode with missing variables.", file=sys.stderr)
    
    # Create Flask app
    app = Flask(__name__)
    
    # Configure Flask from environment variables
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['DEBUG'] = config.DEBUG
    
    # Log configuration (safely, without secrets)
    print("🚀 Starting Flask application")
    print(f"   Environment: {'production' if not config.DEBUG else 'development'}")
    print(f"   Port: {config.PORT}")
    print(f"   Domain: {config.DOMAIN}")
    print(f"   Secret Key: {mask_secret(config.SECRET_KEY)}")
    print(f"   SMTP Username: {mask_secret(config.SMTP_USERNAME)}")
    print(f"   API Key: {mask_secret(config.API_NINJAS_KEY)}")
    
    return app, config


def send_email_with_config(config, subject, body, recipient=None):
    """
    Example of using configuration for SMTP with proper error handling.
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        # Use configuration values
        smtp_server = config.SMTP_SERVER
        smtp_port = config.SMTP_PORT
        smtp_username = config.SMTP_USERNAME
        smtp_password = config.SMTP_PASSWORD
        recipient_email = recipient or config.RECIPIENT_EMAIL
        
        # Validate we have all required SMTP configuration
        if not all([smtp_username, smtp_password, recipient_email]):
            missing = []
            if not smtp_username: missing.append('SMTP_USERNAME')
            if not smtp_password: missing.append('SMTP_PASSWORD')
            if not recipient_email: missing.append('RECIPIENT_EMAIL')
            raise ValueError(f"Missing SMTP configuration: {', '.join(missing)}")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        print(f"✅ Email sent successfully to {mask_secret(recipient_email, 8)}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


# Example of environment-specific configuration
def configure_logging(config):
    """Configure logging based on environment."""
    import logging
    
    if config.DEBUG:
        # Development: verbose logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        # Production: minimal logging, no debug info
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )


# Deployment documentation
DEPLOYMENT_GUIDE = """
🚀 DEPLOYMENT ENVIRONMENT VARIABLES

Required Production Variables:
=============================

Flask Configuration:
-------------------
FLASK_SECRET_KEY=your-super-secret-random-key-here
FLASK_ENV=production
FLASK_DEBUG=0
PORT=5000

SMTP Configuration (for contact form):
-------------------------------------
SMTP_SERVER=your-smtp-server.com
SMTP_PORT=587
SMTP_USERNAME=your-email@domain.com
SMTP_PASSWORD=your-app-specific-password
RECIPIENT_EMAIL=contact@yourdomain.com

API Configuration:
------------------
API_NINJAS_KEY=your-api-ninjas-key

Application Configuration:
--------------------------
DOMAIN=yourdomain.com
POP_CACHE_TTL=60
RUN_UPDATER=0

Security Notes:
===============
1. Never commit .env files to version control
2. Use environment-specific configurations
3. Generate strong random SECRET_KEY: 
   python -c "import secrets; print(secrets.token_hex(32))"
4. Use app-specific passwords for SMTP
5. Rotate secrets regularly
6. Use a secrets management service in production

Example .env file for development:
=================================
FLASK_SECRET_KEY=dev-secret-key-not-for-production
FLASK_ENV=development
FLASK_DEBUG=1
PORT=8080
DOMAIN=localhost:8080
SMTP_SERVER=smtp.mailfence.com
SMTP_PORT=587
SMTP_USERNAME=your-dev-email@domain.com
SMTP_PASSWORD=your-dev-password
RECIPIENT_EMAIL=test@yourdomain.com
API_NINJAS_KEY=your-dev-api-key
POP_CACHE_TTL=30
RUN_UPDATER=0

Platform-Specific Deployment:
=============================

Heroku:
-------
heroku config:set FLASK_SECRET_KEY=your-secret-key
heroku config:set FLASK_ENV=production
# ... set all other variables

Docker:
-------
docker run -e FLASK_SECRET_KEY=your-secret-key \\
           -e FLASK_ENV=production \\
           # ... other environment variables
           your-app

DigitalOcean App Platform:
-------------------------
Set environment variables in the app spec or dashboard
Use encrypted environment variables for secrets

AWS/GCP/Azure:
--------------
Use platform-specific secrets management:
- AWS Secrets Manager
- Google Secret Manager  
- Azure Key Vault
"""


if __name__ == "__main__":
    print(DEPLOYMENT_GUIDE)
    
    # Test configuration loading
    app, config = create_app()
    configure_logging(config)
    
    print("\\n✅ Configuration loaded successfully!")
    print("\\n📖 See deployment guide above for production setup.")