"""
PMW Agents — Configuration package.
 
Usage:
    from config import settings
    from config.settings import settings   # also works
 
    dsn = settings.DATABASE_URL
"""
 
from config.settings import settings
 
__all__ = ["settings"]