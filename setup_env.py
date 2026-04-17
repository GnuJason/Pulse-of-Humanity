#!/usr/bin/env python3
"""
Interactive .env file generator for Pulse of Humanity

This script helps you create a secure .env file with proper validation.
"""

import os
import secrets
import re


def generate_secret_key():
    """Generate a cryptographically secure secret key."""
    return secrets.token_hex(32)


def validate_email(email):
    """Basic email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_port(port_str):
    """Validate port number."""
    try:
        port = int(port_str)
        return 1 <= port <= 65535
    except ValueError:
        return False


def get_user_input(prompt, default=None, validator=None, required=True):
    """Get user input with validation."""
    while True:
        if default:
            full_prompt = f"{prompt} [{default}]: "
        else:
            full_prompt = f"{prompt}: "
        
        value = input(full_prompt).strip()
        
        # Use default if no input provided
        if not value and default:
            value = default
        
        # Check if required
        if required and not value:
            print("This field is required. Please enter a value.")
            continue
        
        # Apply validator if provided
        if validator and value:
            if not validator(value):
                print("Invalid value. Please try again.")
                continue
        
        return value


def create_env_file():
    """Interactive .env file creation."""
    print("PULSE OF HUMANITY - ENVIRONMENT CONFIGURATION SETUP")
    print("=" * 55)
    print()
    print("This script will help you create a secure .env file for development.")
    print("For production, set these variables directly in your server environment.")
    print()
    
    # Check if .env already exists
    if os.path.exists('.env'):
        overwrite = input(".env file already exists. Overwrite? (y/N): ").lower()
        if overwrite != 'y':
            print("Aborted.")
            return
    
    print("\\nFlask Configuration:")
    print("-" * 20)
    
    # Generate or get secret key
    generate_key = input("Generate a new secret key? (Y/n): ").lower()
    if generate_key != 'n':
        secret_key = generate_secret_key()
        print(f"Generated secret key: {secret_key}")
    else:
        secret_key = get_user_input("Enter Flask secret key", validator=lambda x: len(x) >= 32)
    
    # Flask environment
    flask_env = get_user_input("Flask environment", "development")
    flask_debug = get_user_input("Enable debug mode? (y/N)", "1" if flask_env == "development" else "0")
    flask_debug = "1" if flask_debug.lower() in ('y', 'yes', '1') else "0"
    
    # Port
    port = get_user_input("Port", "8080", validator=validate_port)
    
    # Domain
    domain_default = f"localhost:{port}" if flask_env == "development" else "yourdomain.com"
    domain = get_user_input("Domain", domain_default)
    
    print("\\nSMTP Configuration:")
    print("-" * 18)
    
    smtp_server = get_user_input("SMTP server", "smtp.mailfence.com")
    smtp_port = get_user_input("SMTP port", "587", validator=validate_port)
    smtp_username = get_user_input("SMTP username (email)", validator=validate_email)
    smtp_password = get_user_input("SMTP password (app-specific password recommended)")
    recipient_email = get_user_input("Recipient email (for contact form)", validator=validate_email)
    
    print("\\nApplication Settings:")
    print("-" * 20)
    
    cache_ttl = get_user_input("Cache TTL (seconds)", "60", validator=lambda x: x.isdigit())
    run_updater = get_user_input("Run updater? (y/N)", "0")
    run_updater = "1" if run_updater.lower() in ('y', 'yes', '1') else "0"
    anchor_month = get_user_input("Anchor month", "1", validator=lambda x: x.isdigit() and 1 <= int(x) <= 12)
    anchor_day = get_user_input("Anchor day", "1", validator=lambda x: x.isdigit() and 1 <= int(x) <= 31)
    admin_reanchor_token = get_user_input("Admin re-anchor token", secrets.token_hex(16), required=False)
    
    # Create .env content
    env_content = f"""# Flask Configuration
FLASK_SECRET_KEY={secret_key}
FLASK_ENV={flask_env}
FLASK_DEBUG={flask_debug}
PORT={port}

# Domain Configuration
DOMAIN={domain}

# SMTP Configuration
SMTP_SERVER={smtp_server}
SMTP_PORT={smtp_port}
SMTP_USERNAME={smtp_username}
SMTP_PASSWORD={smtp_password}
RECIPIENT_EMAIL={recipient_email}

# Application Settings
POP_CACHE_TTL={cache_ttl}
RUN_UPDATER={run_updater}
POP_ANCHOR_MONTH={anchor_month}
POP_ANCHOR_DAY={anchor_day}
ADMIN_REANCHOR_TOKEN={admin_reanchor_token}

# Generated on {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Remember: Never commit this file to version control!
"""
    
    # Write .env file
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("\\n✓ .env file created successfully!")
    print()
    print("NEXT STEPS:")
    print("1. Test your configuration: python app.py")
    print("2. Make sure .env is in your .gitignore file")
    print("3. For production, set these variables in your server environment")
    print()
    print("SECURITY REMINDERS:")
    print("- Never commit .env files to version control")
    print("- Use app-specific passwords for SMTP (not your main email password)")
    print("- Rotate secrets regularly")
    print("- Use strong, unique secret keys")


def show_current_config():
    """Show current environment configuration (safely)."""
    print("CURRENT ENVIRONMENT CONFIGURATION")
    print("=" * 35)
    
    vars_to_check = [
        ('FLASK_SECRET_KEY', True),  # True = mask secret
        ('FLASK_ENV', False),
        ('FLASK_DEBUG', False),
        ('PORT', False),
        ('DOMAIN', False),
        ('SMTP_SERVER', False),
        ('SMTP_PORT', False),
        ('SMTP_USERNAME', False),
        ('SMTP_PASSWORD', True),
        ('RECIPIENT_EMAIL', False),
        ('POP_CACHE_TTL', False),
        ('RUN_UPDATER', False),
        ('POP_ANCHOR_MONTH', False),
        ('POP_ANCHOR_DAY', False),
        ('ADMIN_REANCHOR_TOKEN', True),
    ]
    
    for var_name, is_secret in vars_to_check:
        value = os.getenv(var_name)
        if value:
            if is_secret:
                display_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "****"
            else:
                display_value = value
        else:
            display_value = "<not set>"
        
        print(f"{var_name:20}: {display_value}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        show_current_config()
    else:
        create_env_file()