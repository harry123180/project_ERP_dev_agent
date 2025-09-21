"""
Custom datetime type for SQLAlchemy to handle datetime parsing issues with SQLite
"""
from sqlalchemy.types import TypeDecorator, DateTime
from datetime import datetime
import re

class CustomDateTime(TypeDecorator):
    """A DateTime type that properly handles string datetime values from SQLite"""
    impl = DateTime
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        # If it's already a datetime, return it
        if isinstance(value, datetime):
            return value

        # If it's a string, parse it
        if isinstance(value, str):
            # Remove 'T' if present and replace with space
            value = value.replace('T', ' ')

            # Try different parsing methods
            try:
                # Try Python's fromisoformat (works in Python 3.7+)
                return datetime.fromisoformat(value)
            except (ValueError, AttributeError):
                pass

            # Try parsing with strptime for common formats
            formats = [
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue

            # If all else fails, return None
            print(f"Warning: Could not parse datetime value: {value}")
            return None

        return value

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, datetime):
            # Return the datetime object directly for SQLite
            return value
        return value