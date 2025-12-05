"""
Podio Lead Intelligence Service - Data Pipeline Integration

Handles extraction of enriched intelligence data from Master Lead items.
Supports lead-type-aware bundle extraction per Contract v2.0:
- Universal fields (always extracted)
- NED Listing bundle
- Foreclosure Auction bundle
- Probate/Estate bundle
- Tax Lien bundle

This is the core business intelligence layer for Pillar 2 (Conversion Analytics).

Extracted from podio_service.py as part of modularization effort.
See services/podio/__init__.py for package overview.
"""

from services.podio.item_service import get_podio_item
from services.podio.field_extraction import extract_field_value_by_id
from config import (
    # V4.0 Enriched Data Field IDs (Contract v1.1.2) - Universal
    LEAD_SCORE_FIELD_ID,
    LEAD_TIER_FIELD_ID,
    ESTIMATED_PROPERTY_VALUE_FIELD_ID,
    EQUITY_PERCENTAGE_FIELD_ID,
    ESTIMATED_EQUITY_FIELD_ID,
    YEAR_BUILT_FIELD_ID,
    PROPERTY_TYPE_FIELD_ID,
    APN_FIELD_ID,
    VALIDATED_MAILING_ADDRESS_FIELD_ID,
    FIRST_PUBLICATION_DATE_FIELD_ID,
    LAW_FIRM_NAME_FIELD_ID,
    # V3.6 Contact Fields (Contract v1.1.3)
    OWNER_NAME_FIELD_ID,
    OWNER_PHONE_FIELD_ID,
    OWNER_EMAIL_FIELD_ID,
    OWNER_MAILING_ADDRESS_FIELD_ID,
    LEAD_TYPE_FIELD_ID,
    # V4.0 Phase 1 Fields (Contract v2.0 - NED/Foreclosure Auction Bundle)
    AUCTION_DATE_FIELD_ID,
    BALANCE_DUE_FIELD_ID,
    OPENING_BID_FIELD_ID,
    AUCTION_PLATFORM_FIELD_ID,
    AUCTION_DATE_PLATFORM_FIELD_ID,
    OPENING_BID_PLATFORM_FIELD_ID,
    AUCTION_LOCATION_FIELD_ID,
    REGISTRATION_DEADLINE_FIELD_ID,
    OWNER_OCCUPIED_FIELD_ID,
    OWNER_NAME_SECONDARY_FIELD_ID,
    OWNER_PHONE_SECONDARY_FIELD_ID,
    OWNER_EMAIL_SECONDARY_FIELD_ID,
    # V4.0 Phase 2 Fields (Contract v2.0 Accelerated - Probate/Estate)
    EXECUTOR_NAME_FIELD_ID,
    PROBATE_CASE_NUMBER_FIELD_ID,
    PROBATE_FILING_DATE_FIELD_ID,
    ESTATE_VALUE_FIELD_ID,
    DECEDENT_NAME_FIELD_ID,
    COURT_JURISDICTION_FIELD_ID,
    # V4.0 Phase 2b Fields (Contract v2.0 - Tax Lien)
    TAX_DEBT_AMOUNT_FIELD_ID,
    DELINQUENCY_START_DATE_FIELD_ID,
    REDEMPTION_DEADLINE_FIELD_ID,
    LIEN_TYPE_FIELD_ID,
    # V4.0 Phase 2c Fields (Contract v2.1 - Tax Lien Multi-Year)
    TAX_DELINQUENCY_SUMMARY_FIELD_ID,
    DELINQUENT_YEARS_COUNT_FIELD_ID,
    # V4.0 Phase 2d Fields (Contract v2.2 - Stacked Distress Signals)
    ACTIVE_DISTRESS_SIGNALS_FIELD_ID,
    DISTRESS_SIGNAL_COUNT_FIELD_ID,
    MULTI_SIGNAL_LEAD_FIELD_ID,
)

# ============================================================================
# LEAD-TYPE-SPECIFIC FIELD BUNDLES (Contract v2.0)
# ============================================================================

# Lead-type-specific field bundles per Contract v2.0
# Fields are extracted based on lead_type for optimized data retrieval
FIELD_BUNDLES = {
    "NED Listing": [
        "auction_date",        # NED auction date
        "balance_due",         # Amount owed
        "opening_bid",         # NED opening bid
        "law_firm_name",       # Already in universal fields but critical for NED
        "first_publication_date"  # Already in universal fields but critical for NED
    ],
    "Foreclosure Auction": [
        "auction_platform",      # Platform (Auction.com, Hubzu, etc.)
        "auction_date_platform", # Platform-specific auction date
        "opening_bid_platform",  # Platform-specific opening bid
        "auction_location",      # Physical or online location
        "registration_deadline"  # Deadline to register for auction
    ],
    # V4.0 Phase 2a - Probate/Estate Bundle (6 fields)
    "Probate/Estate": [
        "executor_name",        # Personal Representative (Executor/Administrator)
        "probate_case_number",  # Court case identifier for deduplication
        "probate_filing_date",  # Date probate was filed with court
        "estate_value",         # Total estate value from court filings
        "decedent_name",        # Original property owner (deceased)
        "court_jurisdiction"    # County/district court handling probate
    ],
    # V4.0 Phase 2b/2c - Tax Lien Bundle (6 fields, including Multi-Year)
    "Tax Lien": [
        "tax_debt_amount",            # Total tax debt/lien amount owed
        "delinquency_start_date",     # Date when tax delinquency began
        "redemption_deadline",        # CRITICAL: Last date owner can redeem property
        "lien_type",                  # Type of tax lien (Property Tax, IRS Federal, etc.)
        "tax_delinquency_summary",    # Multi-year summary e.g. "$12,740 total (2023: $6,501, 2024: $6,239)"
        "delinquent_years_count"      # Number of years with delinquent taxes
    ],
    # V4.0 Phase 2d - Stacked Distress Signals Bundle (3 fields - Contract v2.2)
    # NOTE: These are UNIVERSAL fields - apply to ALL lead types with stacked signals
    "stacking_signals": [
        "active_distress_signals",    # Combined signals e.g. "Tax Lien + Absentee Owner"
        "distress_signal_count",      # Number of active distress signals (1, 2, 3+)
        "multi_signal_lead"           # Yes/No indicator for multi-signal prioritization
    ],
    # Code Violation - Phase 2 (future)
    # Absentee Owner, Tired Landlord - Phase 3
}

# ============================================================================
# LEAD INTELLIGENCE EXTRACTION (Contract v2.0)
# ============================================================================

def get_lead_intelligence(item_id):
    """
    Extract all V4.0 Phase 1 enriched intelligence fields from Podio Master Lead item
    with lead-type-aware bundle extraction per Contract v2.0.
    
    Args:
        item_id: Podio Master Lead item ID to retrieve and extract from
        
    Returns:
        dict: Intelligence data with all enriched fields, or empty dict if item not found
        
    Note:
        All fields return None if not populated (graceful degradation).
        UI layer must handle None values appropriately (display "Unknown" or "N/A").
        This function retrieves the item from Podio and extracts up to 28 total fields:
        - 11 V4.0 enriched fields (Contract v1.1.2) - Universal
        - 5 V3.6 contact fields (Contract v1.1.3) - Universal
        - 12 V4.0 Phase 1 fields (Contract v2.0) - Lead-type-specific + universal compliance
        
    Lead-Type-Aware Extraction:
        - lead_type is extracted first to determine which bundle to include
        - Universal fields are always extracted
        - Lead-type-specific bundle fields are extracted based on lead_type
        - Secondary owner and owner_occupied fields are always extracted (apply to ALL lead types)
    """
    # Retrieve the lead item from Podio
    item = get_podio_item(item_id)
    
    if not item:
        print(f"WARNING: Could not retrieve item {item_id} for intelligence extraction")
        return {}
    
    # STEP 1: Extract lead_type FIRST (determines bundle extraction)
    lead_type = extract_field_value_by_id(item, LEAD_TYPE_FIELD_ID)
    
    # STEP 2: Extract Universal Fields (always included - 16 fields from v1.1.2/v1.1.3)
    
    # Deal Qualification fields (extracted first for fallback calculation)
    estimated_property_value = extract_field_value_by_id(item, ESTIMATED_PROPERTY_VALUE_FIELD_ID)
    equity_percentage = extract_field_value_by_id(item, EQUITY_PERCENTAGE_FIELD_ID)
    estimated_equity = extract_field_value_by_id(item, ESTIMATED_EQUITY_FIELD_ID)
    
    # V4.0.10 FIX: Calculate estimated_equity if not populated in Podio
    # Fallback: estimated_equity = estimated_property_value * (equity_percentage / 100)
    if estimated_equity is None and estimated_property_value is not None and equity_percentage is not None:
        try:
            estimated_equity = estimated_property_value * (equity_percentage / 100.0)
            print(f"V4.0.10: Calculated estimated_equity via fallback: ${estimated_equity:,.0f} (${estimated_property_value:,.0f} × {equity_percentage:.1f}%)")
        except (TypeError, ValueError) as e:
            print(f"V4.0.10: Could not calculate estimated_equity fallback: {e}")
            estimated_equity = None
    
    intelligence = {
        # Priority Metrics (ui_priority 1-2) - MOST IMPORTANT
        'lead_score': extract_field_value_by_id(item, LEAD_SCORE_FIELD_ID),
        'lead_tier': extract_field_value_by_id(item, LEAD_TIER_FIELD_ID),
        
        # Deal Qualification (ui_priority 3-5) - FINANCIAL INTELLIGENCE
        'estimated_property_value': estimated_property_value,
        'equity_percentage': equity_percentage,
        'estimated_equity': estimated_equity,  # May be calculated via V4.0.10 fallback
        
        # Property Details (ui_priority 6-7) - CONTEXT
        'year_built': extract_field_value_by_id(item, YEAR_BUILT_FIELD_ID),
        'property_type': extract_field_value_by_id(item, PROPERTY_TYPE_FIELD_ID),
        
        # Contact & Context (ui_priority 9) - APN hidden, address displayed
        'validated_mailing_address': extract_field_value_by_id(item, VALIDATED_MAILING_ADDRESS_FIELD_ID),
        
        # Timeline & Compliance (ui_priority 10-11) - REGULATORY
        'first_publication_date': extract_field_value_by_id(item, FIRST_PUBLICATION_DATE_FIELD_ID),
        'law_firm_name': extract_field_value_by_id(item, LAW_FIRM_NAME_FIELD_ID),
        
        # V3.6 Contact Fields (Contract v1.1.3)
        'owner_name': extract_field_value_by_id(item, OWNER_NAME_FIELD_ID),
        'owner_phone': extract_field_value_by_id(item, OWNER_PHONE_FIELD_ID),  # Click-to-dial enabled
        'owner_email': extract_field_value_by_id(item, OWNER_EMAIL_FIELD_ID),
        'owner_mailing_address': extract_field_value_by_id(item, OWNER_MAILING_ADDRESS_FIELD_ID),
        'lead_type': lead_type,  # Already extracted above
    }
    
    # STEP 3: Extract Lead-Type-Specific Bundle Fields (Contract v2.0)
    if lead_type == "NED Listing":
        # NED Foreclosure Bundle
        intelligence.update({
            'auction_date': extract_field_value_by_id(item, AUCTION_DATE_FIELD_ID),
            'balance_due': extract_field_value_by_id(item, BALANCE_DUE_FIELD_ID),
            'opening_bid': extract_field_value_by_id(item, OPENING_BID_FIELD_ID),
        })
        print(f"V4.0 Phase 1: Extracted NED Listing bundle for item {item_id}")
        
    elif lead_type == "Foreclosure Auction":
        # Foreclosure Auction Bundle
        intelligence.update({
            'auction_platform': extract_field_value_by_id(item, AUCTION_PLATFORM_FIELD_ID),
            'auction_date_platform': extract_field_value_by_id(item, AUCTION_DATE_PLATFORM_FIELD_ID),
            'opening_bid_platform': extract_field_value_by_id(item, OPENING_BID_PLATFORM_FIELD_ID),
            'auction_location': extract_field_value_by_id(item, AUCTION_LOCATION_FIELD_ID),
            'registration_deadline': extract_field_value_by_id(item, REGISTRATION_DEADLINE_FIELD_ID),
        })
        print(f"V4.0 Phase 1: Extracted Foreclosure Auction bundle for item {item_id}")
        
    elif lead_type == "Probate/Estate":
        # V4.0 Phase 2a - Probate/Estate Bundle (6 fields)
        intelligence.update({
            'executor_name': extract_field_value_by_id(item, EXECUTOR_NAME_FIELD_ID),
            'probate_case_number': extract_field_value_by_id(item, PROBATE_CASE_NUMBER_FIELD_ID),
            'probate_filing_date': extract_field_value_by_id(item, PROBATE_FILING_DATE_FIELD_ID),
            'estate_value': extract_field_value_by_id(item, ESTATE_VALUE_FIELD_ID),
            'decedent_name': extract_field_value_by_id(item, DECEDENT_NAME_FIELD_ID),
            'court_jurisdiction': extract_field_value_by_id(item, COURT_JURISDICTION_FIELD_ID),
        })
        print(f"V4.0 Phase 2a: Extracted Probate/Estate bundle for item {item_id}")
        
    elif lead_type == "Tax Lien":
        # V4.0 Phase 2b/2c - Tax Lien Bundle (6 fields, including Multi-Year)
        intelligence.update({
            'tax_debt_amount': extract_field_value_by_id(item, TAX_DEBT_AMOUNT_FIELD_ID),
            'delinquency_start_date': extract_field_value_by_id(item, DELINQUENCY_START_DATE_FIELD_ID),
            'redemption_deadline': extract_field_value_by_id(item, REDEMPTION_DEADLINE_FIELD_ID),
            'lien_type': extract_field_value_by_id(item, LIEN_TYPE_FIELD_ID),
            'tax_delinquency_summary': extract_field_value_by_id(item, TAX_DELINQUENCY_SUMMARY_FIELD_ID),
            'delinquent_years_count': extract_field_value_by_id(item, DELINQUENT_YEARS_COUNT_FIELD_ID),
        })
        print(f"V4.0 Phase 2b/2c: Extracted Tax Lien bundle (6 fields) for item {item_id}")
        
    else:
        # Unknown or unsupported lead type - log for Phase 2/3 development
        if lead_type:
            print(f"V4.0: Lead type '{lead_type}' not yet supported - Phase 2/3 bundle")
        else:
            print(f"V4.0: No lead_type set for item {item_id}")
    
    # STEP 4: Extract Universal Compliance & Secondary Owner Fields (apply to ALL lead types)
    # These fields are critical for compliance and apply regardless of lead type
    intelligence.update({
        # Compliance & Risk Section (CRITICAL - applies to all lead types)
        'owner_occupied': extract_field_value_by_id(item, OWNER_OCCUPIED_FIELD_ID),
        
        # Secondary Owner Contact (applies to all lead types with co-owners)
        'owner_name_secondary': extract_field_value_by_id(item, OWNER_NAME_SECONDARY_FIELD_ID),
        'owner_phone_secondary': extract_field_value_by_id(item, OWNER_PHONE_SECONDARY_FIELD_ID),
        'owner_email_secondary': extract_field_value_by_id(item, OWNER_EMAIL_SECONDARY_FIELD_ID),
    })
    
    # STEP 5: Extract Stacked Distress Signals (Contract v2.2 - UNIVERSAL)
    # These fields apply to ALL lead types that have multiple distress signals
    # Field IDs may be None until script runs - graceful degradation via extract function
    if ACTIVE_DISTRESS_SIGNALS_FIELD_ID is not None:
        intelligence.update({
            'active_distress_signals': extract_field_value_by_id(item, ACTIVE_DISTRESS_SIGNALS_FIELD_ID),
            'distress_signal_count': extract_field_value_by_id(item, DISTRESS_SIGNAL_COUNT_FIELD_ID),
            'multi_signal_lead': extract_field_value_by_id(item, MULTI_SIGNAL_LEAD_FIELD_ID),
        })
        print(f"V4.0 Phase 2d: Extracted Stacking Signals bundle for item {item_id}")
    
    return intelligence