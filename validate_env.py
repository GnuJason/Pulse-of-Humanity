#!/usr/bin/env python3
"""
Validate environment setup for Render deployment
"""
import os
import sys

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = {
        'PORT': 'Server port (default: 10000)',
        'FLASK_SECRET_KEY': 'Flask secret key for sessions',
    }
    
    optional_vars = {
        'FLASK_DEBUG': 'Debug mode (should be 0 in production)',
        'RUN_UPDATER': 'Enable background annual anchor checks (1 for yes)',
        'POP_ANCHOR_MONTH': 'Anchor month for authoritative yearly baseline (default: 1)',
        'POP_ANCHOR_DAY': 'Anchor day for authoritative yearly baseline (default: 1)',
        'WPP_DATA_DIR': 'Directory containing the three UN WPP CSV files',
        'ADMIN_REANCHOR_TOKEN': 'Optional admin token for POST /admin/reanchor',
    }
    
    print("🔍 Checking Render deployment environment...")
    print()
    
    # Check required variables
    missing_required = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value} ({description})")
        else:
            print(f"❌ {var}: Not set - {description}")
            missing_required.append(var)
    
    print()
    
    # Check optional variables
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value} ({description})")
        else:
            print(f"⚠️  {var}: Not set - {description}")
    
    print()
    
    # Check Flask app can be imported
    try:
        from app import app
        print("✅ Flask app imports successfully")
    except Exception as e:
        print(f"❌ Flask app import failed: {e}")
        return False
    
    # Test health endpoint
    try:
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint returned {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False
    
    if missing_required:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_required)}")
        return False
    
    print("\n🎉 Environment validation passed! Ready for Render deployment.")
    return True

if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)