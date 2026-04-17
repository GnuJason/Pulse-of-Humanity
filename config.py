"""
Flask Configuration Management with Environment Variables

This module demonstrates best practices for handling environment variables
in Flask applications, including secure secret management and validation.
"""

import os
from typing import Optional, Union


class Config:
    """Base configuration class that demonstrates environment variable best practices."""
    
    # Flask Core Configuration
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    DEBUG = os.environ.get('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes', 'on')
    PORT = int(os.environ.get('PORT', '5000'))
    
    # SMTP Configuration (sensitive credentials)
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.mailfence.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL')
    
    # Application Configuration
    CACHE_TTL = int(os.environ.get('POP_CACHE_TTL', '60'))
    DOMAIN = os.environ.get('DOMAIN', 'localhost:5000')
    RUN_UPDATER = os.environ.get('RUN_UPDATER', '0').lower() in ('1', 'true', 'yes')
    POP_ANCHOR_MONTH = int(os.environ.get('POP_ANCHOR_MONTH', '1'))
    POP_ANCHOR_DAY = int(os.environ.get('POP_ANCHOR_DAY', '1'))
    ADMIN_REANCHOR_TOKEN = os.environ.get('ADMIN_REANCHOR_TOKEN')
    
    @classmethod
    def validate_required_vars(cls) -> list[str]:
        """
        Validate that all required environment variables are set.
        Returns a list of missing required variables.
        """
        missing_vars = []
        
        # Required for production
        if not cls.SECRET_KEY:
            missing_vars.append('FLASK_SECRET_KEY')
        
        # Required for email functionality
        if not cls.SMTP_USERNAME:
            missing_vars.append('SMTP_USERNAME')
        if not cls.SMTP_PASSWORD:
            missing_vars.append('SMTP_PASSWORD')
        if not cls.RECIPIENT_EMAIL:
            missing_vars.append('RECIPIENT_EMAIL')
        
        return missing_vars
    
    @classmethod
    def get_config_summary(cls) -> dict:
        """Get a summary of configuration (safe for logging - no secrets)."""
        return {
            'debug': cls.DEBUG,
            'port': cls.PORT,
            'smtp_server': cls.SMTP_SERVER,
            'smtp_port': cls.SMTP_PORT,
            'domain': cls.DOMAIN,
            'cache_ttl': cls.CACHE_TTL,
            'run_updater': cls.RUN_UPDATER,
            'anchor_month': cls.POP_ANCHOR_MONTH,
            'anchor_day': cls.POP_ANCHOR_DAY,
            'has_secret_key': bool(cls.SECRET_KEY),
            'has_smtp_username': bool(cls.SMTP_USERNAME),
            'has_smtp_password': bool(cls.SMTP_PASSWORD),
            'has_recipient_email': bool(cls.RECIPIENT_EMAIL),
            'has_admin_reanchor_token': bool(cls.ADMIN_REANCHOR_TOKEN),
        }


class DevelopmentConfig(Config):
    """Development configuration with additional debug features."""
    DEBUG = True
    # Use a default secret key for development (never in production!)
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-not-for-production')


class ProductionConfig(Config):
    """Production configuration with strict security requirements."""
    DEBUG = False
    
    @classmethod
    def validate_required_vars(cls) -> list[str]:
        """Production requires all secrets to be properly set."""
        missing_vars = super().validate_required_vars()
        
        # In production, we must have a proper secret key
        if cls.SECRET_KEY == 'dev-secret-key-not-for-production':
            missing_vars.append('FLASK_SECRET_KEY (must not be dev default)')
        
        return missing_vars


def get_config() -> Config:
    """
    Get the appropriate configuration class based on environment.
    Returns the configuration instance to use.
    """
    env = os.environ.get('FLASK_ENV', 'development').lower()
    
    if env == 'production':
        return ProductionConfig()
    else:
        return DevelopmentConfig()


def load_environment_variables():
    """
    Load environment variables from .env file if it exists.
    This is useful for development environments.
    """
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"Loading environment variables from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value


# Utility functions for secure environment variable handling

def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Get a boolean environment variable with proper parsing.
    
    Args:
        key: Environment variable name
        default: Default value if not set
        
    Returns:
        Boolean value
    """
    value = os.environ.get(key, '').lower()
    if value in ('1', 'true', 'yes', 'on'):
        return True
    elif value in ('0', 'false', 'no', 'off', ''):
        return default
    else:
        raise ValueError(f"Invalid boolean value for {key}: {value}")


def get_env_int(key: str, default: int = 0, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
    """
    Get an integer environment variable with validation.
    
    Args:
        key: Environment variable name
        default: Default value if not set
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Integer value
        
    Raises:
        ValueError: If value is not a valid integer or outside bounds
    """
    value = os.environ.get(key)
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
            raise ValueError(f"Invalid integer value for {key}: {value}")
        raise


def get_env_required(key: str) -> str:
    """
    Get a required environment variable.
    
    Args:
        key: Environment variable name
        
    Returns:
        Environment variable value
        
    Raises:
        ValueError: If the environment variable is not set
    """
    value = os.environ.get(key)
    if value is None or value.strip() == '':
        raise ValueError(f"Required environment variable {key} is not set")
    return value


def mask_secret(secret: Optional[str], visible_chars: int = 4) -> str:
    """
    Mask a secret for safe logging/display.
    
    Args:
        secret: The secret to mask
        visible_chars: Number of characters to show at the end
        
    Returns:
        Masked string safe for logging
    """
    if not secret:
        return "<not set>"
    if len(secret) <= visible_chars:
        return "*" * len(secret)
    return "*" * (len(secret) - visible_chars) + secret[-visible_chars:]


# Example usage and testing
if __name__ == "__main__":
    # Load environment variables
    load_environment_variables()
    
    # Get configuration
    config = get_config()
    
    # Validate configuration
    missing_vars = config.validate_required_vars()
    if missing_vars:
        print("⚠️  Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
    else:
        print("✅ All required environment variables are set")
    
    # Show configuration summary (safe for logging)
    print("\n📋 Configuration Summary:")
    summary = config.get_config_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    # Example of masking secrets for logging
    print(f"\n🔐 Secret Key: {mask_secret(config.SECRET_KEY)}")
    print(f"🔐 SMTP Password: {mask_secret(config.SMTP_PASSWORD)}")
    print(f"🗓️ Anchor Date: {config.POP_ANCHOR_MONTH:02d}-{config.POP_ANCHOR_DAY:02d}")
    print(f"🔐 Admin Re-anchor Token: {mask_secret(config.ADMIN_REANCHOR_TOKEN)}")