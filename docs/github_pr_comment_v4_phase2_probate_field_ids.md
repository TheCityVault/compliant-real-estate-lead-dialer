# V4.0 Phase 2 Probate Field IDs - Data Team Notification

**Date:** 2025-11-30
**Authorization:** High-Level Advisor (Accelerated Phase 2)
**PR Reference:** https://github.com/TheCityVault/compliant-real-estate-lead-dialer/pull/4

---

## @Data-Team: V4.0 Phase 2 Probate Field IDs (Accelerated)

Probate fields have been created in Podio Master Lead App (ID: `30549135`).

### Field ID Mapping

| Field               | Type        | Podio Field ID |
| ------------------- | ----------- | -------------- |
| Executor Name       | text        | `274950063`    |
| Probate Case Number | text        | `274950064`    |
| Probate Filing Date | date        | `274950065`    |
| Estate Value        | money (USD) | `274950066`    |
| Decedent Name       | text        | `274950067`    |
| Court Jurisdiction  | text        | `274950068`    |

### Scraper Integration Notes

**Ready for Population:**

- All 6 Probate fields are now live in Podio
- Field IDs above can be used for direct API writes
- Fields support standard Podio field value formats

**Write Examples:**

```python
# Text field (executor_name, probate_case_number, decedent_name, court_jurisdiction)
{
    "field_id": 274950063,
    "values": [{"value": "John Smith (Executor)"}]
}

# Date field (probate_filing_date) - ISO 8601 format
{
    "field_id": 274950065,
    "values": [{"start": "2025-10-15"}]
}

# Money field (estate_value) - value + currency
{
    "field_id": 274950066,
    "values": [{"value": 450000, "currency": "USD"}]
}
```

### CRM Team Status

| Component               | Status      |
| ----------------------- | ----------- |
| Podio Fields Created    | ✅ Complete |
| config.py Updated       | ✅ Complete |
| podio_service.py Bundle | ✅ Complete |
| Fiduciary Gate (SOFT)   | ✅ Complete |
| PR #4 Submitted         | ✅ Complete |

### Blocked Items (Pending Monday Bilateral Sync)

The following Tax Lien fields are **NOT** created per High-Level Advisor authorization:

| Field                  | Type     | Reason                 |
| ---------------------- | -------- | ---------------------- |
| Tax Debt Amount        | money    | Blocked                |
| Delinquency Start Date | date     | Blocked                |
| Redemption Deadline    | date     | **CRITICAL** - Blocked |
| Lien Type              | category | Blocked                |

**Reason:** Tax Lien scraper validation pending Monday bilateral sync with Data Team.

---

## Contract Reference

**Integration Contract:** v2.0.0  
**Field Bundle:** Probate/Estate  
**Gate Type:** SOFT (Fiduciary Contact - informational only, does NOT block dialer)

---

## Next Steps

1. **Data Team:** Begin populating Probate fields via scraper
2. **CRM Team:** Monitor PR #4 for merge approval
3. **Monday Sync:** Validate Tax Lien field requirements with Data Team
4. **Post-Monday:** Execute Tax Lien field creation + Redemption Deadline SOFT Gate

---

_This document serves as the official notification of Probate field availability for Data Team integration._
