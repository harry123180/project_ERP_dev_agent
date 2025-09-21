#!/usr/bin/env python
"""
Reset procurement user password to proc123
"""
import sqlite3
from werkzeug.security import generate_password_hash

# Connect to database
conn = sqlite3.connect('erp_development.db')
cursor = conn.cursor()

# Hash the password
password_hash = generate_password_hash('proc123')

# Update the password for procurement user
cursor.execute("""
    UPDATE users
    SET password = ?
    WHERE username = 'procurement'
""", (password_hash,))

# Commit the change
conn.commit()

# Verify the update
cursor.execute("SELECT username, role, is_active FROM users WHERE username = 'procurement'")
result = cursor.fetchone()
if result:
    print(f"✓ Password reset successful for user: {result[0]} (role: {result[1]})")
else:
    print("✗ User 'procurement' not found")

conn.close()