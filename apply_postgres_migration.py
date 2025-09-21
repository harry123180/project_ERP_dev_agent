#!/usr/bin/env python
"""
Apply PostgreSQL migration
"""
import os
import sys
import subprocess

# Set PostgreSQL environment variables
os.environ['USE_POSTGRESQL'] = 'true'
os.environ['POSTGRES_USER'] = 'erp_user'
os.environ['POSTGRES_PASSWORD'] = '271828'
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_DB'] = 'erp_database'

# Change to backend directory
os.chdir('backend')

def run_command(cmd):
    """Run a command and print output"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Info:", result.stderr)
    return result.returncode

print("="*50)
print("PostgreSQL Migration Application")
print("="*50)

# Step 1: Stamp the database as current
print("\nStep 1: Stamping database with current migration...")
code = run_command("python -m flask db stamp head")
if code != 0:
    print("Warning: Stamp might have failed, continuing...")

# Step 2: Apply migration
print("\nStep 2: Applying migration to PostgreSQL...")
code = run_command("python -m flask db upgrade")
if code == 0:
    print("\n" + "="*50)
    print("Migration applied successfully!")
    print("Database: erp_database")
    print("User: erp_user")
    print("="*50)
else:
    print("Migration upgrade might have issues, check the output above.")