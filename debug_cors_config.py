#!/usr/bin/env python3

import sys
import os
sys.path.append('backend')
sys.path.append('backend/app')

# Change to backend directory
os.chdir('backend')

from dotenv import load_dotenv
load_dotenv()

# Test configuration loading
from config import config

def debug_cors_config():
    print("=== CORS Configuration Debug ===")
    
    # Check environment
    print(f"FLASK_ENV: {os.getenv('FLASK_ENV', 'not set')}")
    print(f"CORS_ORIGINS env var: {os.getenv('CORS_ORIGINS', 'not set')}")
    print()
    
    # Test config loading
    config_name = os.getenv('FLASK_ENV', 'default')
    config_obj = config[config_name]()
    
    print(f"Using config: {config_name}")
    print(f"Config class: {config_obj.__class__.__name__}")
    print(f"CORS_ORIGINS from config: {getattr(config_obj, 'CORS_ORIGINS', 'not found')}")
    print()
    
    # Test app creation
    try:
        from app import create_app
        app = create_app(config_name)
        print("App created successfully")
        print(f"App config CORS_ORIGINS: {app.config.get('CORS_ORIGINS', 'not found')}")
        
        # Test route registration
        print("\nRegistered routes:")
        for rule in app.url_map.iter_rules():
            if 'auth' in rule.rule:
                print(f"  {rule.rule} -> {rule.methods}")
                
        # Test CORS extension
        print(f"\nApp extensions: {list(app.extensions.keys())}")
        if 'cors' in app.extensions:
            print("CORS extension found!")
            cors_ext = app.extensions['cors']
            print(f"CORS extension: {cors_ext}")
        else:
            print("CORS extension NOT found!")
            
    except Exception as e:
        print(f"Error creating app: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_cors_config()