#!/usr/bin/env python
"""Test project creation with different status values"""
import requests
import json
from datetime import datetime

# API endpoint
base_url = "http://localhost:5000"
login_url = f"{base_url}/api/v1/auth/login"
project_url = f"{base_url}/api/v1/projects"

# Login first to get token
login_data = {
    "username": "harry123180",
    "password": "password123"  # Correct password from init_postgres_db.py
}

print("1. Logging in...")
login_response = requests.post(login_url, json=login_data)
print(f"   Login response status: {login_response.status_code}")
if login_response.status_code != 200:
    print(f"   Login failed: {login_response.text}")
    exit(1)

response_json = login_response.json()
if 'data' in response_json:
    token = response_json['data']['access_token']
else:
    # Handle different response structure
    token = response_json.get('access_token', response_json.get('token', None))
    if not token:
        print(f"   Unexpected response structure: {json.dumps(response_json, indent=2)}")
        exit(1)
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
print("✓ Login successful")

# Test 1: Create project with 'active' status (should fail)
print("\n2. Testing with 'active' status (should fail)...")
project_data = {
    "project_name": "Test Project 1",
    "project_code": "TEST001",
    "project_status": "active",  # Invalid
    "description": "Test project",
    "start_date": datetime.now().strftime("%Y-%m-%d")
}

response = requests.post(project_url, json=project_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code != 201:
    print(f"   Error: {json.dumps(response.json(), indent=2)}")

# Test 2: Create project with 'ongoing' status (should succeed)
print("\n3. Testing with 'ongoing' status (should succeed)...")
project_data = {
    "project_name": "Test Project 2",
    "project_code": "TEST002",
    "project_status": "ongoing",  # Valid
    "description": "Test project",
    "start_date": datetime.now().strftime("%Y-%m-%d")
}

response = requests.post(project_url, json=project_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    print("   ✓ Project created successfully!")
    print(f"   Project ID: {response.json()['data']['project_id']}")
else:
    print(f"   Error: {json.dumps(response.json(), indent=2)}")

# Test 3: Create project without status (should use default 'ongoing')
print("\n4. Testing without status (should use default 'ongoing')...")
project_data = {
    "project_name": "Test Project 3",
    "project_code": "TEST003",
    "description": "Test project",
    "start_date": datetime.now().strftime("%Y-%m-%d")
}

response = requests.post(project_url, json=project_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    print("   ✓ Project created successfully!")
    print(f"   Project status: {response.json()['data']['project_status']}")
else:
    print(f"   Error: {json.dumps(response.json(), indent=2)}")