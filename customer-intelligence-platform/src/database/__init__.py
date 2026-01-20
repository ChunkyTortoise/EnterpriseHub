"""Database module for Customer Intelligence Platform."""

from .models import *
from .service import DatabaseService, get_database_service
from .schema import init_database, create_tables

__all__ = [
    'DatabaseService',
    'get_database_service',
    'init_database',
    'create_tables'
]