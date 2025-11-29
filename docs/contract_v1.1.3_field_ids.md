# Contract v1.1.3 - Field IDs for Data Team

**Created:** 2025-11-26T04:57:38Z  
**Contract Version:** v1.1.3  
**Podio App ID:** 30549135 (Master Lead App)

---

## ✅ All 5 Fields Created Successfully

### Field ID Mappings

| Field Key | Field Label | Field ID | Type | Section | Status |
|-----------|-------------|----------|------|---------|---------|
| `owner_name` | Owner Name | **274769677** | TEXT | Contact Details | ✅ Created |
| `owner_phone_primary` | Owner Phone Primary | **274909275** | PHONE | Contact Details | ⭐ CRITICAL |
| `owner_email_primary` | Owner Email Primary | **274909276** | EMAIL | Contact Details | ✅ Created |
| `owner_mailing_address` | Owner Mailing Address (Personator) | **274909277** | TEXT | Contact Details | ✅ Created |
| `lead_type` | Lead Type | **274909279** | CATEGORY | Lead Intelligence Panel | ⭐ CRITICAL |

---

## 🎯 Critical Field Details

### Owner Phone Primary (ID: 274909275)
- **Priority:** 12
- **Type:** PHONE (mobile)
- **Business Impact:** Unlocks 0% → 70% dialable lead coverage
- **Feature:** Click-to-dial functionality enabled
- **Data Source:** Melissa Property API PrimaryOwner.Phone

### Lead Type (ID: 274909279)
- **Priority:** 16
- **Type:** CATEGORY (single-select)
- **Business Impact:** BLOCKS V4.0 deployment
- **Required:** Yes (cannot be null)
- **Options:**
  - NED Listing
  - Probate/Estate
  - Absentee Owner
  - Tax Lien
  - Code Violation
  - Foreclosure Auction
  - Tired Landlord

---

## 📋 Data Team Integration Points

### Supabase Edge Function Schema Updates Required

```sql
-- Add to master_leads table
ALTER TABLE master_leads ADD COLUMN owner_name TEXT;
ALTER TABLE master_leads ADD COLUMN owner_phone_primary TEXT;
ALTER TABLE master_leads ADD COLUMN owner_email_primary TEXT;
ALTER TABLE master_leads ADD COLUMN owner_mailing_address TEXT;
ALTER TABLE master_leads ADD COLUMN lead_type TEXT NOT NULL DEFAULT 'Absentee Owner';
```

### Podio Sync Mappings

```typescript
// podio-sync edge function mappings
const fieldMappings = {
  owner_name: 274769677,
  owner_phone_primary: 274909275,
  owner_email_primary: 274909276,
  owner_mailing_address: 274909277,
  lead_type: 274909279
};
```

---

## ✅ Validation Results

**API Validation:** All 5 fields confirmed accessible via Podio API  
**Section Placement:** Verified in correct sections  
**Field Types:** All field types match contract specifications  
**Required Constraints:** Lead Type configured as required field

---

## 📊 Next Steps for CRM Team

1. ✅ **COMPLETE:** Create 5 Podio fields
2. **PENDING:** Update [`config.py`](../config.py) with field ID constants
3. **PENDING:** Update [`podio_service.py`](../podio_service.py) with field accessors
4. **PENDING:** Update [`workspace.html`](../templates/workspace.html) UI components
5. **PENDING:** Return field IDs to Data Team (GitHub PR #2 comment)

---

## 🚀 Deployment Timeline

- **Hour 0-4:** ✅ Field creation (COMPLETE)
- **Hour 4-8:** Update CRM codebase (config.py, podio_service.py)
- **Hour 8-12:** Update UI (workspace.html)
- **Hour 12:** Return field IDs to Data Team

**Status:** ON TRACK for 12-hour delivery commitment

---

## 📄 Reference Files

- Script: [`scripts/add_v3_6_contact_fields.py`](../scripts/add_v3_6_contact_fields.py)
- Field IDs JSON: [`scripts/v3_6_field_ids.json`](../scripts/v3_6_field_ids.json)
- Contract: [`docs/integration_contracts/podio-schema-v1.1.3.json`](integration_contracts/podio-schema-v1.1.3.json)