# CRM Team Phase 1 Field IDs - Ready for podio-sync Update

**Date:** 2025-11-29
**CRM PM Authorization:** Phase 1 field creation COMPLETE
**Target:** Data Pipeline Team - PR #3 Contract v2.0

---

## Phase 1 Podio Field IDs (Contract v2.0)

All 12 Phase 1 fields have been created in Master Lead App (ID: 30549135). Update `podio-sync` Edge Function with these mappings:

### NED Foreclosure Section

| Contract Field Name | Podio Field ID | Type  | Notes            |
| ------------------- | -------------- | ----- | ---------------- |
| Auction Date        | 274947463      | date  | TBD_AUCTION_DATE |
| Balance Due         | 274947464      | money | TBD_BALANCE_DUE  |
| Opening Bid         | 274947465      | money | TBD_OPENING_BID  |

### Foreclosure Auction Section

| Contract Field Name     | Podio Field ID | Type     | Notes                     |
| ----------------------- | -------------- | -------- | ------------------------- |
| Auction Platform        | 274947466      | category | TBD_AUCTION_PLATFORM      |
| Auction Date (Platform) | 274947467      | date     | TBD_AUCTION_DATE_PLATFORM |
| Opening Bid (Platform)  | 274947468      | money    | TBD_OPENING_BID_PLATFORM  |
| Auction Location        | 274947469      | text     | TBD_AUCTION_LOCATION      |
| Registration Deadline   | 274947470      | date     | TBD_REG_DEADLINE          |

### Compliance & Risk Section (CRITICAL)

| Contract Field Name | Podio Field ID | Type     | Notes                                         |
| ------------------- | -------------- | -------- | --------------------------------------------- |
| Owner Occupied      | 274947471      | category | TBD_OWNER_OCCUPIED - **CFPA Compliance Gate** |

### Secondary Owner Contact Section

| Contract Field Name     | Podio Field ID | Type  | Notes                     |
| ----------------------- | -------------- | ----- | ------------------------- |
| Owner Name (Secondary)  | 274947475      | text  | TBD_OWNER_NAME_SECONDARY  |
| Owner Phone (Secondary) | 274947473      | phone | TBD_OWNER_PHONE_SECONDARY |
| Owner Email (Secondary) | 274947474      | email | TBD_OWNER_EMAIL_SECONDARY |

---

## JSON Format for podio-sync

```json
{
  "auction_date": "274947463",
  "balance_due": "274947464",
  "opening_bid": "274947465",
  "auction_platform": "274947466",
  "auction_date_platform": "274947467",
  "opening_bid_platform": "274947468",
  "auction_location": "274947469",
  "registration_deadline": "274947470",
  "owner_occupied": "274947471",
  "owner_name_secondary": "274947475",
  "owner_phone_secondary": "274947473",
  "owner_email_secondary": "274947474"
}
```

---

## Category Field Options

### Auction Platform (274947466)

Options: ["GovEase", "Zeus Auction", "RealAuction", "Bid4Assets", "Auction.com", "County Courthouse", "Other"]

### Owner Occupied (274947471)

Options: ["Yes", "No", "Unknown"]

---

## CRM Team Status

- ✅ 12 Podio fields created in Master Lead App
- ✅ config.py updated with field ID constants
- ✅ podio_service.py updated with lead-type-aware extraction
- 🔄 workspace.html UI updates (in progress - parallel with Data Team)
- 🔄 Owner Occupied workflow gate design (strategic review pending)

## Data Team Action Required

1. Update `podio-sync` Edge Function with Phase 1 field mappings
2. Enable sync for NED Listing and Foreclosure Auction lead types
3. Provide test leads for CRM integration testing

**ETA for test leads:** Please advise

---

**CRM PM:** @CRM-PM-Mode
**Next Sync:** After test leads received
