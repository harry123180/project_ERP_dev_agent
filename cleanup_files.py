#!/usr/bin/env python
"""
Clean up unnecessary files before GitHub upload
"""
import os
import glob

def cleanup_files():
    """Remove test files and other unnecessary files"""

    # Patterns for files to delete
    patterns_to_delete = [
        'test_*.py',           # Test files
        'check_*.py',          # Check scripts
        'debug_*.py',          # Debug scripts
        'fix_*.py',            # Fix scripts (keep core ones)
        'create_*.py',         # Creation scripts
        'add_*.py',            # Adding data scripts
        '*_test.py',           # Other test files
        '*_test_*.py',         # Test reports
        '*.json',              # JSON test reports (keep important ones)
        '*.log',               # Log files
        '*.db',                # SQLite databases
        'token*.txt',          # Token files
        'token*.json',         # Token JSON files
        '*.html',              # Test HTML files
        '*.xlsx',              # Excel files
        '*.pdf',               # PDF files
    ]

    # Files to keep (important for the system)
    files_to_keep = [
        'app.py',
        'run.py',
        'config.py',
        'requirements.txt',
        'package.json',
        'package-lock.json',
        'tsconfig.json',
        'vite.config.ts',
        'artifacts/*.json',  # Keep artifact JSONs
        '.env',
        '.env.example',
    ]

    deleted_files = []
    kept_files = []

    for pattern in patterns_to_delete:
        for file in glob.glob(pattern):
            # Check if file should be kept
            should_keep = False
            for keep_pattern in files_to_keep:
                if file.endswith(keep_pattern.split('/')[-1]) or 'artifacts' in file:
                    should_keep = True
                    break

            if not should_keep and os.path.isfile(file):
                try:
                    os.remove(file)
                    deleted_files.append(file)
                except Exception as e:
                    print(f"Could not delete {file}: {e}")
            elif should_keep:
                kept_files.append(file)

    # Remove empty directories
    empty_dirs = []
    for root, dirs, files in os.walk('.'):
        if not files and not dirs:
            if root not in ['.', './backend', './frontend', './docs', './artifacts']:
                try:
                    os.rmdir(root)
                    empty_dirs.append(root)
                except:
                    pass

    # Summary
    print(f"=== Cleanup Summary ===")
    print(f"Deleted {len(deleted_files)} files")
    print(f"Removed {len(empty_dirs)} empty directories")
    print(f"Kept {len(kept_files)} important files")

    # List some deleted files
    if deleted_files:
        print(f"\nDeleted files (showing first 20):")
        for f in deleted_files[:20]:
            print(f"  - {f}")
        if len(deleted_files) > 20:
            print(f"  ... and {len(deleted_files) - 20} more")

    return len(deleted_files), len(empty_dirs)

if __name__ == '__main__':
    deleted, dirs_removed = cleanup_files()
    print(f"\n✓ Cleanup complete! Ready for GitHub upload.")