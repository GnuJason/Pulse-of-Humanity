#!/usr/bin/env python3
"""
Environment Variable Security Audit and Improvement Script

This script analyzes your current Flask app and suggests improvements
for environment variable handling and security.
"""

import os
import re
import secrets
from pathlib import Path


def generate_secure_secret_key():
    """Generate a cryptographically secure secret key."""
    return secrets.token_hex(32)


def audit_current_config():
    """Audit the current environment variable usage in app.py."""
    print("ENVIRONMENT VARIABLE SECURITY AUDIT")
    print("=" * 50)
    
    # Check current .env.example
    env_example_path = "/home/gnujason/pulse-of-humanity/.env.example"
    if os.path.exists(env_example_path):
        print("✓ .env.example file exists")
        
        with open(env_example_path, 'r') as f:
            content = f.read()
            
        # Check for placeholder values that need changing
        issues = []
        if 'your-secret-key-change-in-production' in content:
            issues.append("✗ Default secret key placeholder found")
        if 'your-email@domain.com' in content:
            issues.append("✗ Email placeholder values found")
        if 'your-api-key' in content:
            issues.append("✗ API key placeholder found")
            
        if issues:
            print("\\n! Issues found in .env.example:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print("✓ .env.example looks good")
    
    # Check if actual .env file exists
    env_path = "/home/gnujason/pulse-of-humanity/.env"
    if os.path.exists(env_path):
        print("\\n✓ .env file exists (good for development)")
        print("   ! Make sure it's in .gitignore!")
    else:
        print("\\n? No .env file found (you may be using system environment variables)")
    
    # Check gitignore
    gitignore_path = "/home/gnujason/pulse-of-humanity/.gitignore"
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
        if '.env' in gitignore_content:
            print("✓ .env is in .gitignore")
        else:
            print("✗ .env should be added to .gitignore")
    else:
        print("✗ No .gitignore file found")


def create_secure_env_template():
    """Create a secure .env template with generated secrets."""
    print("\\nGENERATING SECURE CONFIGURATION")
    print("=" * 40)
    
    # Generate secure values
    secret_key = generate_secure_secret_key()
    
    secure_env_template = f"""# Flask Configuration
FLASK_SECRET_KEY={secret_key}
FLASK_ENV=development
FLASK_DEBUG=1
PORT=8080

# Domain Configuration
DOMAIN=localhost:8080

# SMTP Configuration (replace with your actual credentials)
SMTP_SERVER=smtp.mailfence.com
SMTP_PORT=587
SMTP_USERNAME=your-actual-email@yourdomain.com
SMTP_PASSWORD=your-actual-app-password
RECIPIENT_EMAIL=contact@yourdomain.com

# API Configuration (replace with your actual API key)
API_NINJAS_KEY=your-actual-api-ninjas-key

# Application Settings
POP_CACHE_TTL=60
RUN_UPDATER=0

# Additional security settings you might want to add:
# CSRF_SECRET_KEY={generate_secure_secret_key()}
# JWT_SECRET_KEY={generate_secure_secret_key()}
# DATABASE_URL=postgresql://user:pass@localhost/dbname
"""
    
    # Write to a secure template file
    with open("/home/gnujason/pulse-of-humanity/.env.secure", 'w') as f:
        f.write(secure_env_template)
    
    print("✓ Created .env.secure with generated secret key")
    print(f"   Secret key: {secret_key[:16]}...{secret_key[-8:]}")
    print("   Review and rename to .env after updating credentials")


def create_production_checklist():
    """Create a production deployment checklist."""
    checklist = """
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
"""
    
    with open("/home/gnujason/pulse-of-humanity/PRODUCTION_CHECKLIST.md", 'w') as f:
        f.write(checklist)
    
    print("\\nCreated PRODUCTION_CHECKLIST.md")


def suggest_improvements():
    """Suggest specific improvements for the current setup."""
    print("\\nSUGGESTED IMPROVEMENTS")
    print("=" * 30)
    
    improvements = [
        "1. Add environment variable validation on startup",
        "2. Use configuration classes for different environments",
        "3. Implement secure logging (mask secrets in logs)",
        "4. Add health check endpoint that validates configuration",
        "5. Use python-dotenv for better .env file handling",
        "6. Implement graceful degradation for optional features",
        "7. Add configuration caching to avoid repeated os.getenv calls",
        "8. Use type hints and validation for environment variables",
        "9. Implement secrets rotation strategy",
        "10. Add monitoring for configuration changes"
    ]
    
    for improvement in improvements:
        print(f"   {improvement}")


def create_env_validation_snippet():
    """Create a code snippet for validating environment variables."""
    validation_code = '''
# Add this to your app.py to validate environment variables on startup

def validate_environment():
    """Validate that all required environment variables are set."""
    required_vars = [
        'FLASK_SECRET_KEY',
        'SMTP_USERNAME', 
        'SMTP_PASSWORD',
        'RECIPIENT_EMAIL',
        'API_NINJAS_KEY'
    ]
    
    missing_vars = []
    weak_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif var == 'FLASK_SECRET_KEY' and len(value) < 32:
            weak_vars.append(f"{var} (too short: {len(value)} chars)")
    
    if missing_vars:
        print(f"✗ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    if weak_vars:
        print(f"! Weak configuration: {', '.join(weak_vars)}")
    
    print("✓ Environment validation passed")
    return True

# Call this before creating your Flask app
if __name__ == "__main__":
    if validate_environment():
        # Start your app
        app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
    else:
        print("Fix environment variables before starting the application")
        exit(1)
'''
    
    with open("/home/gnujason/pulse-of-humanity/env_validation_snippet.py", 'w') as f:
        f.write(validation_code)
    
    print("\\nCreated env_validation_snippet.py")
    print("   Copy this code into your app.py for better validation")


if __name__ == "__main__":
    print("FLASK ENVIRONMENT VARIABLE SECURITY TOOLKIT")
    print("=" * 60)
    
    # Run audit
    audit_current_config()
    
    # Create secure template
    create_secure_env_template()
    
    # Create production checklist
    create_production_checklist()
    
    # Create validation snippet
    create_env_validation_snippet()
    
    # Suggest improvements
    suggest_improvements()
    
    print("\\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Review the generated .env.secure file")
    print("2. Update placeholder values with real credentials")
    print("3. Rename .env.secure to .env")
    print("4. Add validation code to your app.py")
    print("5. Review production checklist before deployment")
    print("6. Test your configuration in a staging environment")
    print("\\nYour Flask app will be much more secure!")