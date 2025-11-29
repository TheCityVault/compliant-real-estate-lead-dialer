# 🐛 BUG REPORT: Property Address Parsing Issue (Data Pipeline)

**Reported**: 2025-11-29  
**Reporter**: CRM Team (Debug Mode)  
**Priority**: Medium  
**Assigned To**: Data Team  
**Field Affected**: Property Address (Field ID: 274896122)

---

## Issue Description

Property Address field (274896122, aka "Validated Mailing Address") contains malformed address with **duplicate state and ZIP code**:

```
Actual:   "10710 King St Westminster, Co 80031, CO, 80031"
Expected: "10710 King St, Westminster, CO 80031"
```

### Screenshot Evidence

From Playwright test on item_id `3208508882`:

```yaml
Property Details:
  - Property Address: "10710 King St Westminster, Co 80031, CO, 80031"
```

---

## Root Cause Analysis

The Data Team's `enrich-lead` Edge Function is incorrectly concatenating Melissa Property API response fields. The address appears to have:

1. Missing comma after street address
2. Lowercase "Co" instead of "CO"
3. State appearing twice ("Co" and "CO")
4. ZIP code appearing twice ("80031" and "80031")

### Suspected API Field Concatenation Issue

```javascript
// Current (buggy) implementation likely looks like:
const validated_address =
  addressLine1 + " " + city + ", " + state + ", " + postalCode;

// But addressLine1 already contains: "10710 King St Westminster, Co 80031"
// So the full string becomes: "10710 King St Westminster, Co 80031, CO, 80031"
```

---

## Impact Assessment

| Impact Area         | Severity | Details                                    |
| ------------------- | -------- | ------------------------------------------ |
| **Functionality**   | None     | Address still readable and usable          |
| **User Experience** | Low      | Looks unprofessional to agents             |
| **Data Integrity**  | Medium   | Double-stored data indicates parsing error |
| **Compliance**      | None     | No regulatory impact                       |

---

## Recommended Fix (Data Team)

Update `enrich-lead` Edge Function in Supabase to properly parse Melissa Property API response:

### Option A: Parse Raw Address Only

```javascript
// Use only the validated address string, don't re-concatenate
const validated_address = response.Records[0].FormattedAddress;
```

### Option B: Build Address Correctly

```javascript
const addressLine1 = response.Records[0].AddressLine1; // "10710 King St"
const city = response.Records[0].City; // "Westminster"
const state = response.Records[0].State; // "CO"
const postalCode = response.Records[0].PostalCode; // "80031"

const validated_address = `${addressLine1}, ${city}, ${state} ${postalCode}`;
// Result: "10710 King St, Westminster, CO 80031"
```

---

## CRM Team Status

| Task                                                 | Status                  |
| ---------------------------------------------------- | ----------------------- |
| Property Address displays in UI                      | ✅ Complete             |
| Semantic mapping correct (Property vs Owner Mailing) | ✅ Complete             |
| Address formatting fix                               | ⏸️ Blocked on Data Team |

---

## Related Files

- [`app.py:108`](../app.py:108) - Property address extraction using field ID
- [`podio_service.py:343`](../podio_service.py:343) - Intelligence data extraction
- [`templates/workspace.html:328`](../templates/workspace.html:328) - Property Address display

---

## Test Case for Verification

After Data Team fix, verify with:

- **Item ID**: 3208508882
- **Expected Property Address**: "10710 King St, Westminster, CO 80031"
- **No duplicate state/ZIP codes**
