"""
Podio Services Package - API Integration Modules

This package contains modular service components for Podio API integration,
extracted from the monolithic podio_service.py for improved maintainability.

Modules:
    oauth: OAuth token refresh and credential management
    item_service: Item retrieval and CRUD operations for Podio items
    field_extraction: Field value extraction and parsing utilities
    intelligence: Lead intelligence extraction (V4.0 Phase 1/2)
    task_service: Task creation and management (V3.3 disposition automation)

Business Justification:
    Pillar 1 (Compliance): OAuth logic isolation enables security audits
    Pillar 2 (Conversion Analytics): Intelligence extraction isolated enables caching and A/B testing
    Pillar 3 (Data Pipeline): Field extraction isolated enables caching and validation
    Pillar 4 (Disposition Funnel): Task creation isolated enables multi-task workflows, templates, escalation rules
    Pillar 5 (Scalability): Completes podio_service.py refactoring - original 832 lines → 5 focused domain services
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

# Re-export Field Extraction functions for backward compatibility
from services.podio.field_extraction import (
    extract_field_value,
    extract_field_value_by_id,
)

# Re-export Intelligence functions for backward compatibility (V4.0.8)
from services.podio.intelligence import (
    FIELD_BUNDLES,
    get_lead_intelligence,
)

# Re-export Task Service functions for backward compatibility (V4.0.8 final extraction)
from services.podio.task_service import (
    create_follow_up_task,
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
    # Field Extraction functions
    'extract_field_value',
    'extract_field_value_by_id',
    # Intelligence functions
    'FIELD_BUNDLES',
    'get_lead_intelligence',
    # Task Service functions
    'create_follow_up_task',
]