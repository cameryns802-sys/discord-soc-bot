"""
PST Timezone Helper - Provides PST-aware datetime functions for all cogs
Use this instead of datetime.utcnow() throughout the bot
"""

from datetime import datetime, timezone
import pytz

# Define PST timezone
PST = pytz.timezone('America/Los_Angeles')
UTC = timezone.utc

def get_now_pst():
    """Get current time in PST timezone"""
    return PST.localize(datetime.now())

def get_now_utc():
    """Get current time in UTC timezone"""
    return datetime.now(UTC)

def utcnow():
    """Alias for datetime.utcnow() but PST-aware - returns PST localized datetime"""
    return PST.localize(datetime.now())

# For backward compatibility with existing code using datetime.utcnow()
class DateTimeHelper:
    """Helper class to provide PST-aware datetime functionality"""
    
    @staticmethod
    def utcnow():
        """Get current time (PST)"""
        return PST.localize(datetime.now())
    
    @staticmethod
    def now():
        """Get current time (PST)"""
        return PST.localize(datetime.now())
    
    @staticmethod
    def now_utc():
        """Get current time (UTC)"""
        return datetime.now(UTC)

# Export for easy importing
__all__ = ['PST', 'UTC', 'get_now_pst', 'get_now_utc', 'utcnow', 'DateTimeHelper']
