"""
Podio Field Extraction Service - Field Value Parsing Utilities

Handles extraction and normalization of field values from Podio items.
Supports all Podio field types: text, category, money, number, date.

Business Justification:
    Pillar 3 (Data Pipeline): Field extraction isolated enables future enhancements
        like caching, batched extraction, and type-specific validation
    Pillar 5 (Scalability): Reusable utilities for any Podio integration work

Extracted from podio_service.py for improved modularity.
"""
import re


def extract_field_value(item, field_label):
    """
    Extract field value from Podio item by field label
    
    Args:
        item: Podio item dictionary containing 'fields' array
        field_label: Label string of the field to extract
        
    Returns:
        str: Field value with HTML tags stripped, or empty string if not found
        
    Examples:
        >>> item = {'fields': [{'label': 'Name', 'values': [{'value': '<p>John</p>'}]}]}
        >>> extract_field_value(item, 'Name')
        'John'
        
        >>> item = {'fields': [{'label': 'Status', 'values': [{'value': {'text': 'Active'}}]}]}
        >>> extract_field_value(item, 'Status')
        'Active'
        
    Note:
        V3.6 Fix: Handles multiple field types:
        - Text fields: {'value': '<p>Name</p>'} -> strips HTML
        - Category fields: {'value': {'text': 'NED Listing', ...}} -> extracts 'text'
        - Other fields: converts to string
    """
    for field in item.get('fields', []):
        if field.get('label') == field_label:
            values = field.get('values', [])
            if values:
                value = values[0]
                
                # Handle different field types
                if isinstance(value, dict):
                    inner_value = value.get('value', '')
                    
                    # V3.6 FIX: Handle category fields with nested {'text': '...'} structure
                    if isinstance(inner_value, dict):
                        # Category field - extract 'text' property
                        text = inner_value.get('text', '')
                    else:
                        # Text field or other - convert to string
                        text = str(inner_value) if inner_value is not None else ''
                else:
                    text = str(value)
                
                # Strip HTML tags (e.g., <p>Name</p> -> Name)
                text = re.sub(r'<[^>]+>', '', text)
                return text.strip()
    return ''


def extract_field_value_by_id(item, field_id, field_type=None):
    """
    Extract field value from Podio item by field ID (V4.0.5 Enhanced)
    
    Args:
        item: Podio item dictionary containing 'fields' array
        field_id: Numeric field ID to extract (will be converted to int)
        field_type: Optional field type hint (number, category, money, text, date)
                   If not provided, type is auto-detected from field metadata
        
    Returns:
        Extracted value with type depending on field_type:
        - category: str (the text value)
        - money: float (the numeric value)
        - number: float (the numeric value)
        - date: str (YYYY-MM-DD format)
        - text: str (with HTML tags stripped)
        - default: raw value
        Returns None if field not found or empty
        
    Examples:
        >>> item = {'fields': [{'field_id': 123, 'type': 'number', 'values': [{'value': '65.0000'}]}]}
        >>> extract_field_value_by_id(item, 123)
        65.0
        
        >>> item = {'fields': [{'field_id': 456, 'type': 'category', 'values': [{'value': {'text': 'HOT'}}]}]}
        >>> extract_field_value_by_id(item, 456)
        'HOT'
        
    Note:
        Handles all Podio field types: number, category, money, text, date.
        Returns None for graceful degradation in UI.
    """
    if not item:
        return None
    
    for field in item.get('fields', []):
        if field.get('field_id') == int(field_id):
            values = field.get('values', [])
            if not values:
                return None
            
            value = values[0]
            # Use provided field_type or auto-detect from field metadata
            detected_type = field.get('type')
            field_type = field_type or detected_type
            
            # Handle different Podio field types
            if field_type == 'category':
                # Category fields: [{'value': {'text': 'WARM', ...}}]
                # Extract nested 'value' dict first
                if isinstance(value, dict) and 'value' in value:
                    inner_value = value['value']
                    return inner_value.get('text') if isinstance(inner_value, dict) else str(inner_value)
                # Fallback for direct structure (shouldn't happen but defensive)
                return value.get('text') if isinstance(value, dict) else str(value)
            elif field_type == 'money':
                # Money fields: [{'value': '323000.0000', 'currency': 'USD'}]
                # Already handles nested 'value' correctly
                return float(value.get('value')) if isinstance(value, dict) else None
            elif field_type == 'number':
                # Number fields: [{'value': '65.0000'}]
                # Extract nested 'value' string first
                if isinstance(value, dict) and 'value' in value:
                    try:
                        return float(value['value']) if value['value'] else None
                    except (ValueError, TypeError):
                        return None
                # Fallback for direct value (old behavior)
                try:
                    return float(value) if value else None
                except (ValueError, TypeError):
                    return None
            elif field_type == 'date':
                # Date fields return dict with 'start' key (YYYY-MM-DD format)
                return value.get('start') if isinstance(value, dict) else str(value)
            elif field_type == 'text':
                # Text fields: [{'value': '<p>R0090271</p>'}]
                # Extract nested 'value' first
                if isinstance(value, dict) and 'value' in value:
                    text = value['value']
                else:
                    text = str(value) if value else None
                
                if text:
                    text = re.sub(r'<[^>]+>', '', str(text))
                    return text.strip()
                return None
            else:
                # Default: return raw value
                return value
    return None