# 📋 Data Team Notification: Phase 2b Tax Lien Fields Ready

**Date:** 2025-11-30
**Authorization:** High-Level Advisor
**Contract Version:** 2.0.0

---

## 🎯 Summary

Phase 2b Tax Lien fields have been created in Podio and are ready for Data Team integration. This completes all Phase 2 fields (10 total: 6 Probate + 4 Tax Lien).

---

## 📊 Tax Lien Field IDs (Master Lead App: 30549135)

| Field Key                | Field Label            | Podio Field ID | Type     | Description                                       |
| ------------------------ | ---------------------- | -------------- | -------- | ------------------------------------------------- |
| `tax_debt_amount`        | Tax Debt Amount        | **274954741**  | money    | Total tax debt/lien amount owed (USD)             |
| `delinquency_start_date` | Delinquency Start Date | **274954742**  | date     | Date when tax delinquency began                   |
| `redemption_deadline`    | Redemption Deadline    | **274954743**  | date     | **CRITICAL**: Last date owner can redeem property |
| `lien_type`              | Lien Type              | **274954744**  | category | Type of tax lien                                  |

---

## 🏷️ Lien Type Category Options

The `lien_type` field (ID: 274954744) accepts the following category values:

| Option Text         | Color Code | Use Case                            |
| ------------------- | ---------- | ----------------------------------- |
| `Property Tax`      | #DCEDC8    | County/municipal property tax liens |
| `IRS Federal`       | #FFCCBC    | Federal tax liens from IRS          |
| `State Tax`         | #B3E5FC    | State income/business tax liens     |
| `HOA/Assessment`    | #F0F4C3    | Homeowner association liens         |
| `Municipal/Utility` | #E1BEE7    | Water, sewer, utility liens         |
| `Multiple`          | #FFCDD2    | Multiple lien types on property     |

---

## 📝 JSON Schema for Data Pipeline

```json
{
  "tax_lien_fields": {
    "tax_debt_amount": {
      "field_id": 274954741,
      "type": "money",
      "format": {
        "value": "float",
        "currency": "USD"
      },
      "example": { "value": 15000.0, "currency": "USD" }
    },
    "delinquency_start_date": {
      "field_id": 274954742,
      "type": "date",
      "format": "YYYY-MM-DD",
      "example": "2023-06-15"
    },
    "redemption_deadline": {
      "field_id": 274954743,
      "type": "date",
      "format": "YYYY-MM-DD",
      "example": "2025-01-15",
      "critical": true,
      "note": "Triggers SOFT Gate when within 30 days of today"
    },
    "lien_type": {
      "field_id": 274954744,
      "type": "category",
      "allowed_values": [
        "Property Tax",
        "IRS Federal",
        "State Tax",
        "HOA/Assessment",
        "Municipal/Utility",
        "Multiple"
      ]
    }
  }
}
```

---

## 🔄 API Integration Example

### Creating/Updating a Tax Lien Lead

```python
# Podio API payload for Tax Lien fields
podio_fields = {
    "274954741": {  # tax_debt_amount
        "value": 15000.00,
        "currency": "USD"
    },
    "274954742": {  # delinquency_start_date
        "start": "2023-06-15"
    },
    "274954743": {  # redemption_deadline (CRITICAL)
        "start": "2025-01-15"
    },
    "274954744": 1  # lien_type - use option ID from Podio
}
```

### Lead Type Identifier

When populating Tax Lien leads, ensure the `lead_type` field (ID: 274909279) is set to `"Tax Lien"` to trigger proper bundle extraction and UI display.

---

## ⚠️ Critical: Redemption Deadline Gate

The `redemption_deadline` field (ID: 274954743) triggers a **SOFT Gate** in the Agent Workspace:

| Condition                | UI Behavior                                |
| ------------------------ | ------------------------------------------ |
| Deadline ≤ 30 days away  | 🔴 Red "Imminent Deadline" badge displayed |
| Deadline 31-60 days away | 🟠 Orange warning indicator                |
| Deadline > 60 days away  | Standard display                           |

**Gate Type:** SOFT (informational only - does NOT block dialer)

**Purpose:** Alerts agents to use ethical urgency language and avoid pressure tactics.

---

## 📁 Reference Files

| File            | Path                                                                                      | Description                        |
| --------------- | ----------------------------------------------------------------------------------------- | ---------------------------------- |
| Field IDs JSON  | [`scripts/v4_phase2_taxlien_field_ids.json`](../scripts/v4_phase2_taxlien_field_ids.json) | Machine-readable field ID mappings |
| Creation Script | [`scripts/add_v4_phase2_taxlien_fields.py`](../scripts/add_v4_phase2_taxlien_fields.py)   | Field creation script              |
| Config          | [`config.py`](../config.py)                                                               | Application field ID constants     |
| Service         | [`podio_service.py`](../podio_service.py)                                                 | Tax Lien bundle extraction logic   |

---

## ✅ Phase 2 Completion Status

| Phase             | Lead Type      | Fields        | Status          |
| ----------------- | -------------- | ------------- | --------------- |
| Phase 2a          | Probate/Estate | 6 fields      | ✅ Complete     |
| Phase 2b          | Tax Lien       | 4 fields      | ✅ Complete     |
| **Total Phase 2** |                | **10 fields** | **✅ COMPLETE** |

---

## 🚀 Next Steps for Data Team

1. **Update Tax Lien scraper** to map extracted data to field IDs listed above
2. **Test data ingestion** with sample Tax Lien records
3. **Verify `lead_type`** is set to `"Tax Lien"` for proper UI bundle display
4. **Ensure date formats** are YYYY-MM-DD for date fields
5. **Validate category values** match exact option text for `lien_type`

---

## 📞 Questions?

Contact CRM Team for any integration questions or field mapping issues.

---

_Document generated: 2025-11-30 | Contract v2.0.0 | Phase 2b Tax Lien_
