# Phase 2 Compliance Gates - Design Specification

**Document Type:** UI/UX Design Specification
**Status:** 📋 DESIGN COMPLETE - Awaiting Phase 2 Implementation
**Created:** 2025-11-29
**Target Implementation:** Post-Monday Sync (2025-12-02)
**Authorized By:** High-Level Advisor Strategic Review

---

## Overview

Phase 2 introduces two new SOFT compliance gates for Probate/Estate and Tax Lien leads. Unlike the Phase 1 Owner Occupied gate (HARD gate that blocks dialer), these are informational gates that alert agents to special handling requirements without preventing calls.

**Key Distinction:**
| Gate Type | Behavior | Example |
|-----------|----------|---------|
| HARD | Blocks dialer until acknowledged | Owner Occupied (Phase 1) |
| SOFT | Displays warning, allows immediate action | Fiduciary Contact, Imminent Deadline (Phase 2) |

---

## Gate #1: Probate Fiduciary Gate (SOFT)

### Trigger Condition

```javascript
lead_data.lead_type === "Probate/Estate";
```

### Visual Elements

**1. Header Badge:**

```html
<span class="compliance-badge fiduciary-contact"> 🔶 Fiduciary Contact </span>
```

**CSS:**

```css
.compliance-badge.fiduciary-contact {
  background-color: #ff9800; /* Orange */
  color: #000;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
```

**2. Info Tooltip (on hover/click):**

```html
<div class="fiduciary-tooltip" role="tooltip">
  <div class="tooltip-header">
    <span class="icon">⚖️</span>
    <strong>Fiduciary Contact Notice</strong>
  </div>
  <div class="tooltip-body">
    <p>
      <strong>Important:</strong> You are contacting a
      <em>Personal Representative</em> (Executor or Administrator), NOT the
      property owner.
    </p>
    <ul>
      <li>The property owner is <strong>deceased</strong></li>
      <li>The PR has legal authority to sell estate property</li>
      <li>Use fiduciary-appropriate language</li>
      <li>Avoid phrases implying the PR is "in trouble"</li>
    </ul>
  </div>
  <div class="tooltip-action">
    <button class="btn-acknowledge" onclick="acknowledgeFiduciaryNotice()">
      I Understand
    </button>
  </div>
</div>
```

**CSS:**

```css
.fiduciary-tooltip {
  position: absolute;
  background: #fff3e0;
  border: 2px solid #ff9800;
  border-radius: 8px;
  padding: 16px;
  max-width: 350px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.fiduciary-tooltip .tooltip-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
}

.fiduciary-tooltip .tooltip-body {
  font-size: 13px;
  line-height: 1.5;
}

.fiduciary-tooltip .tooltip-body ul {
  margin: 8px 0;
  padding-left: 20px;
}

.fiduciary-tooltip .btn-acknowledge {
  background: #ff9800;
  color: #000;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  margin-top: 12px;
}
```

**3. Script Panel Integration:**
When `lead_type === 'Probate/Estate'`, the Script Panel should display probate-specific opening:

```javascript
const PROBATE_SCRIPT_OPENER = `
Hi, this is [Agent Name] with [Company]. I'm reaching out regarding the property at [Property Address].

I understand you're serving as the Personal Representative for the estate, and I wanted to see if you might be considering selling the property as part of settling the estate.

[Pause for response]

I work with families going through probate and can often help simplify the process...
`;

function getScriptOpener(leadType) {
  if (leadType === "Probate/Estate") {
    return PROBATE_SCRIPT_OPENER;
  }
  // Default script for other types
  return DEFAULT_SCRIPT_OPENER;
}
```

### Behavior

1. **On Page Load:** Badge displays in header next to Lead Type badge
2. **On Badge Hover:** Tooltip appears with fiduciary notice
3. **On Badge Click:** Tooltip persists until "I Understand" clicked
4. **Dialer Status:** ENABLED (SOFT gate does not block)
5. **Logging:** `console.log('Fiduciary notice displayed for lead:', lead_id)`

### Integration Location

**In [`workspace.html`](templates/workspace.html) (~line 980, after existing compliance gate logic):**

```javascript
// SOFT Gate: Probate Fiduciary Notice
if (leadType === "Probate/Estate") {
  displayFiduciaryBadge();
  loadProbateScript();
  console.log("SOFT GATE: Fiduciary contact notice displayed");
}
```

---

## Gate #2: Redemption Deadline Gate (SOFT)

### Trigger Condition

```javascript
// Calculate days until redemption deadline
const today = new Date();
const deadline = new Date(lead_data.redemption_deadline);
const daysUntilDeadline = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));

// Trigger if deadline exists and is within 30 days
const isImminentDeadline =
  lead_data.redemption_deadline &&
  daysUntilDeadline <= 30 &&
  daysUntilDeadline > 0;
```

### Visual Elements

**1. Header Badge:**

```html
<span class="compliance-badge imminent-deadline">
  🔴 Imminent Deadline (<span id="days-remaining">X</span> days)
</span>
```

**CSS:**

```css
.compliance-badge.imminent-deadline {
  background-color: #f44336; /* Red */
  color: #fff;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  animation: pulse 2s infinite; /* Attention-grabbing pulse */
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}
```

**2. Warning Banner (top of Intelligence Panel):**

```html
<div class="deadline-warning-banner" id="deadline-warning">
  <div class="banner-icon">⚠️</div>
  <div class="banner-content">
    <strong>Imminent Legal Deadline</strong>
    <p>
      This property has a redemption deadline in
      <strong><span id="deadline-days">X</span> days</strong>.
    </p>
    <p class="ethical-notice">
      Urgency language must comply with ethical outreach standards. Do not
      create false urgency or pressure tactics.
    </p>
  </div>
  <button class="banner-dismiss" onclick="dismissDeadlineWarning()">✕</button>
</div>
```

**CSS:**

```css
.deadline-warning-banner {
  background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
  border-left: 4px solid #f44336;
  padding: 12px 16px;
  margin-bottom: 16px;
  border-radius: 0 8px 8px 0;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.deadline-warning-banner .banner-icon {
  font-size: 24px;
}

.deadline-warning-banner .banner-content {
  flex: 1;
}

.deadline-warning-banner .ethical-notice {
  font-size: 12px;
  color: #666;
  margin-top: 8px;
  font-style: italic;
}

.deadline-warning-banner .banner-dismiss {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  color: #666;
}
```

**3. Countdown Display (in Tax Lien section):**

```html
<div class="deadline-countdown">
  <div class="countdown-number" id="countdown-value">X</div>
  <div class="countdown-label">days until deadline</div>
  <div class="deadline-date">
    Redemption: <span id="deadline-formatted">MM/DD/YYYY</span>
  </div>
</div>
```

### Behavior

1. **On Page Load:** Badge displays + Warning banner appears
2. **Countdown Updates:** Days remaining calculated dynamically
3. **Banner Dismissible:** Agent can close banner (logged for audit)
4. **Dialer Status:** ENABLED (SOFT gate does not block)
5. **Audit Logging:**

```javascript
function logDeadlineInteraction(leadId, action) {
  const auditEntry = {
    lead_id: leadId,
    timestamp: new Date().toISOString(),
    action: action, // 'viewed', 'dismissed', 'call_initiated'
    days_remaining: daysUntilDeadline,
  };
  console.log("AUDIT: Redemption deadline interaction", auditEntry);
  // Future: Send to compliance tracking endpoint
}
```

### Integration Location

**In [`workspace.html`](templates/workspace.html) (~line 990, after Fiduciary gate):**

```javascript
// SOFT Gate: Redemption Deadline Warning
if (lead_data.redemption_deadline) {
  const daysUntil = calculateDaysUntil(lead_data.redemption_deadline);
  if (daysUntil <= 30 && daysUntil > 0) {
    displayDeadlineWarning(daysUntil);
    logDeadlineInteraction(lead_id, "viewed");
    console.log(
      "SOFT GATE: Imminent deadline warning displayed",
      daysUntil,
      "days"
    );
  }
}
```

---

## Implementation Notes

### Field Dependencies

These gates require Phase 2 fields to exist in Podio:

| Gate      | Required Field      | Field ID (TBD)       |
| --------- | ------------------- | -------------------- |
| Fiduciary | Lead Type           | 274909279 (existing) |
| Deadline  | Redemption Deadline | TBD (Phase 2)        |

### Data Flow

```
Podio → podio_service.py (extract) → app.py (pass to template) → workspace.html (render gates)
```

### Testing Scenarios

**Fiduciary Gate:**

1. Load lead with `lead_type = 'Probate/Estate'` → Badge + tooltip should display
2. Load lead with `lead_type = 'NED Listing'` → No fiduciary badge

**Deadline Gate:**

1. Load lead with `redemption_deadline = today + 15 days` → Badge + banner should display "15 days"
2. Load lead with `redemption_deadline = today + 45 days` → No deadline warning
3. Load lead with `redemption_deadline = today - 5 days` → Handle expired deadline (different display?)

---

## Future Enhancements (Phase 3+)

1. **Server-side audit logging** - Send compliance interactions to database
2. **Agent performance tracking** - Correlate deadline urgency with conversion rates
3. **Configurable thresholds** - Admin setting for deadline warning days (default 30)
4. **Expired deadline handling** - Special messaging for past-due redemptions

---

**Document Status:** Ready for Code Mode implementation post-Phase 2 field creation
**Estimated Implementation Time:** 2-3 hours per gate
**Dependencies:** Phase 2 Podio fields must exist first
