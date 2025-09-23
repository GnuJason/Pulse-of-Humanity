#!/usr/bin/env python3
"""
Demonstration: How to improve your existing Flask app with better environment variable handling

This script shows practical examples of using os.environ with validation, fallbacks, and security.
"""

import os
import sys
from typing import Optional, Union


# Example 1: Basic environment variable reading with secure fallbacks
def read_env_variables():
    """Demonstrate different ways to read environment variables."""
    
    print("ENVIRONMENT VARIABLE READING PATTERNS")
    print("=" * 45)
    
    # Method 1: Basic reading with fallback (what you currently use)
    secret_key = os.getenv('FLASK_SECRET_KEY', 'default-dev-key')
    print(f"1. Basic reading: SECRET_KEY = {secret_key[:16]}...")
    
    # Method 2: Required variables (fail if not set)
    try:
        api_key = os.environ['API_NINJAS_KEY']  # Will raise KeyError if not set
        print(f"2. Required variable: API_KEY = {api_key[:8]}...")
    except KeyError:
        print("2. Required variable: API_KEY not set (would fail in production)")
    
    # Method 3: Boolean environment variables with proper parsing
    debug_raw = os.getenv('FLASK_DEBUG', '0')
    debug = debug_raw.lower() in ('1', 'true', 'yes', 'on')
    print(f"3. Boolean parsing: DEBUG = {debug} (from '{debug_raw}')")
    
    # Method 4: Integer with validation
    try:
        port = int(os.getenv('PORT', '5000'))
        if port < 1 or port > 65535:
            raise ValueError(f"Port {port} is out of valid range")
        print(f"4. Integer with validation: PORT = {port}")
    except ValueError as e:
        print(f"4. Integer validation failed: {e}")
    
    # Method 5: Multiple fallbacks
    smtp_server = os.getenv('SMTP_SERVER') or os.getenv('MAIL_SERVER') or 'localhost'
    print(f"5. Multiple fallbacks: SMTP_SERVER = {smtp_server}")


# Example 2: Validation function for your app
def validate_production_config():
    """Validate environment variables for production deployment."""
    
    print("\\nPRODUCTION CONFIGURATION VALIDATION")
    print("=" * 40)
    
    errors = []
    warnings = []
    
    # Critical secrets that must be set
    required_secrets = {
        'FLASK_SECRET_KEY': 'Flask session signing',
        'SMTP_PASSWORD': 'Email sending',
        'API_NINJAS_KEY': 'API access'
    }
    
    for var, purpose in required_secrets.items():
        value = os.getenv(var)
        if not value:
            errors.append(f"{var} required for {purpose}")
        elif var == 'FLASK_SECRET_KEY':
            if len(value) < 32:
                warnings.append(f"{var} should be at least 32 characters (current: {len(value)})")
            if value == 'your-secret-key-change-in-production':
                errors.append(f"{var} is still using default placeholder value")
    
    # Check environment settings
    flask_env = os.getenv('FLASK_ENV', 'development')
    flask_debug = os.getenv('FLASK_DEBUG', '0').lower() in ('1', 'true')
    
    if flask_env == 'production' and flask_debug:
        warnings.append("FLASK_DEBUG should be False in production")
    
    # Print results
    if errors:
        print("ERRORS (must fix before production):")
        for error in errors:
            print(f"  ✗ {error}")
    
    if warnings:
        print("\\nWARNINGS (should fix):")
        for warning in warnings:
            print(f"  ! {warning}")
    
    if not errors and not warnings:
        print("✓ All validation checks passed!")
    
    return len(errors) == 0


# Example 3: Secure configuration loading for your app
class AppConfig:
    """Configuration class that demonstrates best practices."""
    
    def __init__(self):
        self.load_config()
        self.validate_config()
    
    def load_config(self):
        """Load configuration from environment variables."""
        
        # Flask core settings
        self.SECRET_KEY = self._get_required('FLASK_SECRET_KEY')
        self.DEBUG = self._get_bool('FLASK_DEBUG', False)
        self.PORT = self._get_int('PORT', 5000, min_val=1, max_val=65535)
        
        # SMTP settings
        self.SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.mailfence.com')
        self.SMTP_PORT = self._get_int('SMTP_PORT', 587, min_val=1, max_val=65535)
        self.SMTP_USERNAME = self._get_required('SMTP_USERNAME')
        self.SMTP_PASSWORD = self._get_required('SMTP_PASSWORD')
        self.RECIPIENT_EMAIL = self._get_required('RECIPIENT_EMAIL')
        
        # API settings
        self.API_NINJAS_KEY = self._get_required('API_NINJAS_KEY')
        
        # App settings
        self.DOMAIN = os.getenv('DOMAIN', 'localhost:5000')
        self.CACHE_TTL = self._get_int('POP_CACHE_TTL', 60, min_val=1)
        self.RUN_UPDATER = self._get_bool('RUN_UPDATER', False)
    
    def _get_required(self, key: str) -> str:
        """Get a required environment variable."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def _get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean environment variable."""
        value = os.getenv(key, '').lower()
        if value in ('1', 'true', 'yes', 'on'):
            return True
        elif value in ('0', 'false', 'no', 'off', ''):
            return default
        else:
            raise ValueError(f"Invalid boolean value for {key}: {value}")
    
    def _get_int(self, key: str, default: int, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
        """Get an integer environment variable with validation."""
        value = os.getenv(key)
        if value is None:
            return default
        
        try:
            int_value = int(value)
            if min_val is not None and int_value < min_val:
                raise ValueError(f"{key} must be >= {min_val}")
            if max_val is not None and int_value > max_val:
                raise ValueError(f"{key} must be <= {max_val}")
            return int_value
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(f"Invalid integer value for {key}: {value}")
            raise
    
    def validate_config(self):
        """Validate the loaded configuration."""
        if len(self.SECRET_KEY) < 32:
            print(f"WARNING: SECRET_KEY is only {len(self.SECRET_KEY)} characters (recommended: 64+)")
        
        if '@' not in self.RECIPIENT_EMAIL:
            raise ValueError("RECIPIENT_EMAIL must be a valid email address")
    
    def get_safe_summary(self) -> dict:
        """Get configuration summary safe for logging (no secrets)."""
        return {
            'debug': self.DEBUG,
            'port': self.PORT,
            'smtp_server': self.SMTP_SERVER,
            'smtp_port': self.SMTP_PORT,
            'domain': self.DOMAIN,
            'cache_ttl': self.CACHE_TTL,
            'run_updater': self.RUN_UPDATER,
            'has_secret_key': bool(self.SECRET_KEY),
            'has_smtp_credentials': bool(self.SMTP_USERNAME and self.SMTP_PASSWORD),
            'has_api_key': bool(self.API_NINJAS_KEY),
            'secret_key_length': len(self.SECRET_KEY) if self.SECRET_KEY else 0,
        }


# Example 4: How to integrate this into your existing app.py
def show_integration_example():
    """Show how to integrate this into your existing Flask app."""
    
    integration_code = '''
# Add this to the top of your app.py after imports:

# Load environment variables from .env file (development only)
def load_dotenv_if_exists():
    """Load .env file if it exists (for development)."""
    if os.path.exists('.env'):
        print("Loading environment variables from .env file")
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:  # Don't override existing env vars
                        os.environ[key] = value

# Validation function
def validate_environment():
    """Validate required environment variables are set."""
    required = ['FLASK_SECRET_KEY', 'SMTP_USERNAME', 'SMTP_PASSWORD', 'RECIPIENT_EMAIL', 'API_NINJAS_KEY']
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        print("Please set these variables before starting the application.")
        return False
    
    # Check for weak configurations
    secret_key = os.getenv('FLASK_SECRET_KEY')
    if len(secret_key) < 32:
        print(f"WARNING: FLASK_SECRET_KEY is weak ({len(secret_key)} chars). Use 64+ characters.")
    
    return True

# Add this before creating your Flask app:
if __name__ == "__main__":
    # Load environment variables
    load_dotenv_if_exists()
    
    # Validate configuration
    if not validate_environment():
        sys.exit(1)
    
    # Your existing Flask app creation and configuration
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
    
    # ... rest of your app setup ...
    
    # Start the app
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    PORT = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
'''
    
    print("\\nINTEGRATION EXAMPLE")
    print("=" * 20)
    print("Here's how to integrate environment variable validation into your existing app.py:")
    print(integration_code)


# Example 5: Production deployment patterns
def show_deployment_examples():
    """Show deployment examples for different platforms."""
    
    print("\\nDEPLOYMENT EXAMPLES")
    print("=" * 20)
    
    examples = {
        "Heroku": [
            "heroku config:set FLASK_SECRET_KEY=your-64-char-secret-key",
            "heroku config:set FLASK_ENV=production",
            "heroku config:set SMTP_USERNAME=your-email@domain.com",
            "heroku config:set SMTP_PASSWORD=your-app-password",
        ],
        "Docker": [
            "# In docker-compose.yml:",
            "environment:",
            "  - FLASK_SECRET_KEY=${FLASK_SECRET_KEY}",
            "  - SMTP_USERNAME=${SMTP_USERNAME}",
            "  - SMTP_PASSWORD=${SMTP_PASSWORD}",
        ],
        "Systemd Service": [
            "# In /etc/systemd/system/pulse-of-humanity.service:",
            "[Service]",
            "Environment=FLASK_SECRET_KEY=your-secret-key",
            "Environment=FLASK_ENV=production",
            "EnvironmentFile=/etc/pulse-of-humanity/environment",
        ]
    }
    
    for platform, commands in examples.items():
        print(f"\\n{platform}:")
        for cmd in commands:
            print(f"  {cmd}")


if __name__ == "__main__":
    print("FLASK ENVIRONMENT VARIABLES - PRACTICAL EXAMPLES")
    print("=" * 55)
    
    # Demonstrate environment variable reading
    read_env_variables()
    
    # Show configuration validation
    try:
        is_valid = validate_production_config()
    except Exception as e:
        print(f"Configuration error: {e}")
        is_valid = False
    
    # Demonstrate configuration class
    print("\\nCONFIGURATION CLASS EXAMPLE")
    print("=" * 30)
    try:
        config = AppConfig()
        summary = config.get_safe_summary()
        print("Configuration loaded successfully:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"Configuration failed: {e}")
    
    # Show integration examples
    show_integration_example()
    
    # Show deployment examples  
    show_deployment_examples()
    
    print("\\n" + "=" * 55)
    print("KEY TAKEAWAYS:")
    print("1. Always validate required environment variables on startup")
    print("2. Use proper type conversion (bool, int) with validation")
    print("3. Provide sensible defaults for non-critical settings")
    print("4. Never log or expose secret values")
    print("5. Use different configurations for development vs production")
    print("6. Validate secret strength (length, complexity)")
    print("7. Use environment-specific .env files for development")
    print("8. Document all required variables for deployment")