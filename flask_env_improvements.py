"""
Ready-to-use environment variable improvements for your Flask app

This file contains code snippets you can directly copy into your app.py
to improve environment variable handling and security.
"""

# =============================================================================
# 1. ADD THESE IMPORTS TO THE TOP OF YOUR app.py
# =============================================================================

import os
import sys
import secrets
from typing import Optional


# =============================================================================
# 2. ADD THESE FUNCTIONS AFTER YOUR IMPORTS
# =============================================================================

def load_dotenv_if_exists():
    """
    Load environment variables from .env file if it exists.
    Only loads variables that aren't already set in the environment.
    """
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"Loading environment variables from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Only set if not already in environment (system env vars take precedence)
                    if key not in os.environ:
                        os.environ[key] = value


def validate_environment():
    """
    Validate that all required environment variables are set and secure.
    Returns True if valid, False if there are critical issues.
    """
    print("Validating environment configuration...")
    
    # Required variables for the app to function
    required_vars = [
        'FLASK_SECRET_KEY',
        'SMTP_USERNAME', 
        'SMTP_PASSWORD',
        'RECIPIENT_EMAIL',
        'API_NINJAS_KEY'
    ]
    
    missing_vars = []
    weak_vars = []
    
    # Check for missing required variables
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif var == 'FLASK_SECRET_KEY':
            # Check secret key strength
            if len(value) < 32:
                weak_vars.append(f"{var} (only {len(value)} chars, recommend 64+)")
            if value in ('your-secret-key-change-in-production', 'dev-secret-key-not-for-production'):
                missing_vars.append(f"{var} (using placeholder value)")
    
    # Check environment consistency
    flask_env = os.getenv('FLASK_ENV', 'development')
    flask_debug = os.getenv('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes')
    
    if flask_env == 'production' and flask_debug:
        weak_vars.append("FLASK_DEBUG should be False in production")
    
    # Report results
    if missing_vars:
        print("✗ CRITICAL: Missing required environment variables:")
        for var in missing_vars:
            print(f"    {var}")
        print("\\nSet these variables before starting the application.")
        return False
    
    if weak_vars:
        print("! WARNINGS (should fix for production):")
        for var in weak_vars:
            print(f"    {var}")
    
    if not weak_vars and not missing_vars:
        print("✓ Environment validation passed!")
    
    return True


def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Get a boolean environment variable with proper parsing.
    Handles various boolean representations (1/0, true/false, yes/no, on/off).
    """
    value = os.getenv(key, '').lower().strip()
    if value in ('1', 'true', 'yes', 'on'):
        return True
    elif value in ('0', 'false', 'no', 'off', ''):
        return default
    else:
        raise ValueError(f"Invalid boolean value for {key}: '{value}'. Use 1/0, true/false, yes/no, or on/off.")


def get_env_int(key: str, default: int, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
    """
    Get an integer environment variable with validation.
    """
    value = os.getenv(key)
    if value is None:
        return default
    
    try:
        int_value = int(value)
        if min_val is not None and int_value < min_val:
            raise ValueError(f"{key} must be >= {min_val}, got {int_value}")
        if max_val is not None and int_value > max_val:
            raise ValueError(f"{key} must be <= {max_val}, got {int_value}")
        return int_value
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"Invalid integer value for {key}: '{value}'")
        raise


def mask_secret(secret: Optional[str], visible_chars: int = 4) -> str:
    """
    Mask a secret for safe logging/display.
    Shows only the last few characters.
    """
    if not secret:
        return "<not set>"
    if len(secret) <= visible_chars:
        return "*" * len(secret)
    return "*" * (len(secret) - visible_chars) + secret[-visible_chars:]


def generate_secret_key() -> str:
    """Generate a cryptographically secure secret key."""
    return secrets.token_hex(32)  # 64 character hex string


# =============================================================================
# 3. REPLACE YOUR CURRENT ENVIRONMENT VARIABLE LOADING
# =============================================================================

# Replace this section in your app.py:
# OLD CODE:
# app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-in-production')
# DEBUG = os.getenv("FLASK_DEBUG") == "1"
# PORT = int(os.getenv("PORT", "5000"))

# NEW CODE (add this where you currently configure Flask):
def configure_flask_from_env(app):
    """Configure Flask app from environment variables with validation."""
    
    # Get configuration with proper type conversion and validation
    try:
        secret_key = os.getenv('FLASK_SECRET_KEY')
        if not secret_key:
            print("WARNING: No FLASK_SECRET_KEY set, generating temporary key")
            secret_key = generate_secret_key()
            print(f"Generated key: {secret_key}")
            print("Save this key to your environment variables!")
        
        app.config['SECRET_KEY'] = secret_key
        
        # Boolean environment variables
        debug = get_env_bool('FLASK_DEBUG', False)
        app.config['DEBUG'] = debug
        
        # Integer environment variables with validation
        port = get_env_int('PORT', 5000, min_val=1, max_val=65535)
        cache_ttl = get_env_int('POP_CACHE_TTL', 60, min_val=1)
        
        # Log configuration (safely, without exposing secrets)
        print(f"Flask configuration loaded:")
        print(f"  Debug: {debug}")
        print(f"  Port: {port}")
        print(f"  Secret key: {mask_secret(secret_key)}")
        print(f"  Cache TTL: {cache_ttl} seconds")
        
        return port  # Return port for use in app.run()
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)


# =============================================================================
# 4. IMPROVE YOUR SMTP CONFIGURATION
# =============================================================================

# Replace your current send_email function with this improved version:
def send_email_improved(subject, body, recipient_email=None):
    """
    Send email with improved error handling and configuration validation.
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        # Get SMTP configuration from environment
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.mailfence.com')
        smtp_port = get_env_int('SMTP_PORT', 587, min_val=1, max_val=65535)
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        default_recipient = os.getenv('RECIPIENT_EMAIL')
        
        # Use provided recipient or default
        to_email = recipient_email or default_recipient
        
        # Validate we have all required SMTP settings
        if not smtp_username:
            raise ValueError("SMTP_USERNAME environment variable is required")
        if not smtp_password:
            raise ValueError("SMTP_PASSWORD environment variable is required")
        if not to_email:
            raise ValueError("RECIPIENT_EMAIL environment variable is required")
        
        # Create and send email
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        print(f"Sending email to {mask_secret(to_email, 8)} via {smtp_server}:{smtp_port}")
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        print("✓ Email sent successfully")
        return True
        
    except Exception as e:
        print(f"✗ Failed to send email: {e}")
        return False


# =============================================================================
# 5. UPDATE YOUR MAIN APPLICATION STARTUP
# =============================================================================

# Replace your if __name__ == "__main__": section with this:
def main():
    """Main application startup with proper environment handling."""
    
    print("Starting Pulse of Humanity Flask Application")
    print("=" * 50)
    
    # Load environment variables from .env file (development)
    load_dotenv_if_exists()
    
    # Validate environment configuration
    if not validate_environment():
        print("\\nCannot start application due to configuration errors.")
        print("Please fix the environment variables and try again.")
        sys.exit(1)
    
    # Create Flask app (your existing app creation code)
    # app = Flask(__name__)
    # ... your existing app setup ...
    
    # Configure Flask from environment
    port = configure_flask_from_env(app)
    
    # Get debug setting
    debug = get_env_bool('FLASK_DEBUG', False)
    
    # Start the application
    print(f"\\nStarting server on port {port} (debug={'on' if debug else 'off'})")
    app.run(host="0.0.0.0", port=port, debug=debug)


# =============================================================================
# 6. USAGE INSTRUCTIONS
# =============================================================================

USAGE_INSTRUCTIONS = """
HOW TO IMPLEMENT THESE IMPROVEMENTS:

1. Copy the functions above into your app.py after the imports

2. Replace your current Flask configuration section with:
   port = configure_flask_from_env(app)

3. Replace your email sending function with send_email_improved()

4. Replace your main startup code with the main() function

5. Create a .env file for development:
   cp .env.secure .env
   # Edit .env with your actual credentials

6. Update your .env.example file with the new template

7. Test your application:
   python app.py

8. For production, set environment variables directly (not .env file):
   export FLASK_SECRET_KEY=your-64-char-secret-key
   export FLASK_ENV=production
   export FLASK_DEBUG=0
   # ... other variables

EXAMPLE .env FILE STRUCTURE:
===========================
FLASK_SECRET_KEY=ca79b2f6f6dd827dd86f18d3456441f32ce578bb1c7e36b5639aeadda2235910
FLASK_ENV=development
FLASK_DEBUG=1
PORT=8080
DOMAIN=localhost:8080
SMTP_SERVER=smtp.mailfence.com
SMTP_PORT=587
SMTP_USERNAME=your-email@domain.com
SMTP_PASSWORD=your-app-password
RECIPIENT_EMAIL=contact@yourdomain.com
API_NINJAS_KEY=your-actual-api-key
POP_CACHE_TTL=60
RUN_UPDATER=0

SECURITY BEST PRACTICES:
========================
✓ Never commit .env files to version control
✓ Use strong, unique secret keys (64+ characters)
✓ Use app-specific passwords for SMTP (not your main password)
✓ Validate all environment variables on startup
✓ Use different configurations for development/production
✓ Rotate secrets regularly
✓ Log configuration status without exposing secret values
"""

if __name__ == "__main__":
    print(USAGE_INSTRUCTIONS)