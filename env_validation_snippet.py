
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
