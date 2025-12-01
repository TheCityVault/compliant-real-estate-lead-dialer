"""
Podio Service Module - Backward Compatibility Facade

This module provides backward compatibility for existing imports.
All business logic has been extracted to domain-specific services.

Extracted modules (services/podio/):
- oauth.py: OAuth token management (~112 lines)
- item_service.py: Item CRUD operations (~320 lines)
- field_extraction.py: Field value extraction (~140 lines)
- intelligence.py: Lead intelligence extraction (~220 lines)
- task_service.py: Task creation (~90 lines)

Refactoring complete: Original 832 lines → 5 focused domain services
This facade remains for backward compatibility (~50 lines)

For new imports, use:
    from services.podio import function_name
"""

# =============================================================================
# BACKWARD COMPATIBILITY RE-EXPORTS
# =============================================================================
# All functions are re-exported from their respective domain modules
# to maintain backward compatibility for existing imports like:
#   from podio_service import refresh_podio_token
#   from podio_service import create_follow_up_task

# OAuth token management
from services.podio.oauth import refresh_podio_token, _podio_token

# Item CRUD operations
from services.podio.item_service import (
    get_podio_item,
    create_call_activity_item,
    update_call_activity_recording,
    generate_title,
    convert_to_iso_date,
    parse_currency,
)

# Field extraction utilities
from services.podio.field_extraction import (
    extract_field_value,
    extract_field_value_by_id,
)

# Lead intelligence extraction (V4.0 Phase 1/2)
from services.podio.intelligence import (
    FIELD_BUNDLES,
    get_lead_intelligence,
)

# Task creation (V3.3 disposition automation)
from services.podio.task_service import (
    create_follow_up_task,
)