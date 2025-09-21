#!/usr/bin/env python
"""
Run Flask-Migrate with PostgreSQL configuration
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
        print("Errors:", result.stderr)
    return result.returncode

print("="*50)
print("PostgreSQL Migration Tool")
print("="*50)

# Step 1: Create migration
print("\nStep 1: Creating migration...")
code = run_command("python -m flask db migrate -m \"Initial PostgreSQL migration\"")
if code != 0:
    print("Migration creation failed!")
    sys.exit(1)

# Step 2: Apply migration
print("\nStep 2: Applying migration to PostgreSQL...")
code = run_command("python -m flask db upgrade")
if code != 0:
    print("Migration upgrade failed!")
    sys.exit(1)

print("\n" + "="*50)
print("Migration completed successfully!")
print("Database: erp_database")
print("User: erp_user")
print("="*50)