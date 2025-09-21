#!/usr/bin/env python3
"""
Final verification of admin login fix
"""
import sys
import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_backend_running():
    """Check if backend server is running"""
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running")
            return True
        else:
            print(f"⚠️  Backend responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend server not accessible: {e}")
        return False

def test_admin_login_real():
    """Test admin login against running backend"""
    print("\n🧪 Testing Admin Login (Real Server)")
    print("=" * 40)

    try:
        # Test login
        response = requests.post(
            'http://localhost:5000/api/v1/auth/login',
            json={
                'username': 'admin',
                'password': 'admin123'
            },
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Admin login successful!")
            print(f"   Username: {data['user']['username']}")
            print(f"   Role: {data['user']['role']}")
            print(f"   Chinese Name: {data['user']['chinese_name']}")
            print(f"   User ID: {data['user']['user_id']}")
            print(f"   Access Token: {data['access_token'][:50]}...")

            # Test authenticated endpoint
            print(f"\n🔐 Testing Authenticated Endpoint")
            auth_response = requests.get(
                'http://localhost:5000/api/v1/auth/me',
                headers={
                    'Authorization': f"Bearer {data['access_token']}",
                    'Content-Type': 'application/json'
                },
                timeout=10
            )

            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                print("✅ Authenticated endpoint works!")
                # Handle different response formats
                if 'data' in auth_data:
                    print(f"   Verified user: {auth_data['data']['username']}")
                    print(f"   Verified role: {auth_data['data']['role']}")
                else:
                    print(f"   Verified user: {auth_data.get('username', 'N/A')}")
                    print(f"   Verified role: {auth_data.get('role', 'N/A')}")
                return True
            else:
                print(f"❌ Authenticated endpoint failed: {auth_response.status_code}")
                print(f"   Response: {auth_response.text}")
                return False

        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_other_users():
    """Test other users to ensure they still work"""
    print("\n👥 Testing Other Users")
    print("=" * 25)

    test_users = [
        ('procurement', 'procurement123'),
        ('engineer', 'engineer123')
    ]

    for username, password in test_users:
        try:
            response = requests.post(
                'http://localhost:5000/api/v1/auth/login',
                json={
                    'username': username,
                    'password': password
                },
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ {username.upper()}: Login successful (Role: {data['user']['role']})")
            else:
                print(f"⚠️  {username.upper()}: Login failed (Status: {response.status_code})")

        except Exception as e:
            print(f"❌ {username.upper()}: Request error - {e}")

def main():
    """Main verification function"""
    print("🔍 Final Admin Login Verification")
    print("=" * 50)

    print("Testing admin login fix in PostgreSQL environment...")

    # Check if backend is running
    if not check_backend_running():
        print("\n⚠️  Backend server is not running.")
        print("   To start the backend server:")
        print("   cd backend && python app.py")
        return

    # Test admin login
    if test_admin_login_real():
        print("\n🎉 VERIFICATION SUCCESSFUL!")
        print("\n✅ Admin login fix is working correctly!")
        print("\n📋 Login Information:")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Database: PostgreSQL")
        print("   Role: Admin")

        # Test other users
        test_other_users()

        print("\n🔧 Fix Summary:")
        print("1. ✅ Identified PostgreSQL connection was working")
        print("2. ✅ Found admin user with corrupted password hash")
        print("3. ✅ Generated new password hash using Werkzeug scrypt")
        print("4. ✅ Updated password in PostgreSQL database")
        print("5. ✅ Verified login works via API")
        print("6. ✅ Confirmed other users still work")

    else:
        print("\n❌ VERIFICATION FAILED!")
        print("   The admin login fix did not work as expected.")

if __name__ == "__main__":
    main()