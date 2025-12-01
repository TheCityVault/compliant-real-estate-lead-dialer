"""
Podio Services Package - API Integration Modules

This package contains modular service components for Podio API integration,
extracted from the monolithic podio_service.py for improved maintainability.

Modules:
    oauth: OAuth token refresh and credential management
    item_service: Item retrieval and CRUD operations (future)
    field_extraction: Field value extraction utilities (future)
    intelligence: Lead intelligence extraction (future)
    task_service: Task creation and management (future)

Business Justification:
    Pillar 1 (Compliance): OAuth logic isolation enables security audits
    Pillar 5 (Scalability): Foundation for subsequent Podio service extractions
"""

# Re-export OAuth functions for backward compatibility
from services.podio.oauth import (
    refresh_podio_token,
    get_token,
    _podio_token
)

# Public API
__all__ = [
    'refresh_podio_token',
    'get_token',
]