"""
Services Package - Domain Service Modules

This package contains domain-specific service modules extracted from the
monolithic podio_service.py to improve maintainability and security auditing.

Modules:
    podio: Podio API integration services (oauth, items, fields, intelligence, tasks)
"""

# Re-export for backward compatibility
from services.podio import *