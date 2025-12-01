"""
Podio Services Package - API Integration Modules

This package contains modular service components for Podio API integration,
extracted from the monolithic podio_service.py for improved maintainability.

Modules:
    oauth: OAuth token refresh and credential management
    item_service: Item retrieval and CRUD operations for Podio items
    field_extraction: Field value extraction utilities (future)
    intelligence: Lead intelligence extraction (future)
    task_service: Task creation and management (future)

Business Justification:
    Pillar 1 (Compliance): OAuth logic isolation enables security audits
    Pillar 3 (Data Pipeline): Item CRUD isolation enables future batch operations
    Pillar 5 (Scalability): Foundation for subsequent Podio service extractions
"""

# Re-export OAuth functions for backward compatibility
from services.podio.oauth import (
    refresh_podio_token,
    get_token,
    _podio_token
)

# Re-export Item Service functions for backward compatibility
from services.podio.item_service import (
    get_podio_item,
    create_call_activity_item,
    update_call_activity_recording,
    # Helper functions
    generate_title,
    convert_to_iso_date,
    parse_currency,
)

# Public API
__all__ = [
    # OAuth functions
    'refresh_podio_token',
    'get_token',
    # Item Service functions
    'get_podio_item',
    'create_call_activity_item',
    'update_call_activity_recording',
    'generate_title',
    'convert_to_iso_date',
    'parse_currency',
]