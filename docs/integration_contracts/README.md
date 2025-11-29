# Integration Contracts: Governance Protocol

**Purpose:** This repository manages schema contracts between the CRM Dialer Project and the Data Pipeline Project for V4.0 integration.

**Contract Interface:** Podio Master Lead App (App ID: 30549135)

---

## 📋 Versioning Strategy

We use **Semantic Versioning** for all schema contracts:

- **Major Version (v2.0):** Breaking changes that require coordination between teams

  - Example: Removing fields, changing field types, renaming fields
  - Requires 30-day deprecation period

- **Minor Version (v1.1):** Backward-compatible additions

  - Example: Adding new enriched fields, adding optional fields
  - Requires 48-hour review SLA

- **Patch Version (v1.0.1):** Documentation updates only
  - Example: Clarifying field usage, updating business justifications
  - No approval required, notification only

**Current Version:** v2.0 (Approved - Pending Implementation)

---

## 📊 Contract Versions

| Version | File                       | Status                                | Date Added     | Description                                                                   |
| ------- | -------------------------- | ------------------------------------- | -------------- | ----------------------------------------------------------------------------- |
| 1.0     | podio-schema-v1.0.json     | Archived                              | 2025-11-25     | Initial schema - 11 baseline fields                                           |
| 1.1     | podio-schema-v1.1.json     | Archived                              | 2025-11-25     | Minor field additions                                                         |
| 1.1.2   | podio-schema-v1.1.2.json   | Archived                              | 2025-11-26     | V3.6 contact fields preparation                                               |
| 1.1.3   | podio-schema-v1.1.3.json   | Active (Production)                   | 2025-11-26     | 16 universal fields with Owner Name, Phone, Email, Mailing Address, Lead Type |
| **2.0** | **podio-schema-v2.0.json** | **Approved (Pending Implementation)** | **2025-11-29** | **47 fields (16 universal + 31 lead-type-specific), 7 lead types**            |

---

## 🚀 Contract v2.0 (Multi-Source Schema)

**Status:** APPROVED WITH CONDITIONS (2025-11-29)
**Effective Date:** Pending Phase 1 field creation (target: 2025-12-06)

### Key Changes from v1.1.3:

- Expanded from 16 to 47 fields
- Added 7 lead type bundles: NED, Probate, Absentee, Tax Lien, Code Violation, Foreclosure Auction, Tired Landlord
- Added secondary owner contact fields (owner_name_secondary, owner_phone_secondary, owner_email_secondary)
- Added compliance field: owner_occupied (CFPA compliance gate)
- Added Field 47: court_jurisdiction for Probate multi-county lookup

### Approval Chain:

- Data Team (Data Normalizer): APPROVED 2025-11-29
- Data Team (High-Level Advisor): APPROVED 2025-11-29
- CRM Team (CRM PM): APPROVED 2025-11-29
- CRM Team (High-Level Advisor): APPROVED WITH CONDITIONS 2025-11-29

### Conditions:

1. **Owner Occupied field** must implement hard workflow gate (Unknown = Yes for compliance)
2. **3-phase rollout**: Phase 1 (Universal+NED+Auction), Phase 2 (Probate+Tax Lien), Phase 3 (Absentee+Code+Tired Landlord)

### GitHub PR Reference:

- [PR #3 - Contract v2.0 Multi-Source Schema](https://github.com/TheCityVault/wholesaling-data-pipeline/pull/3)

---

## ✅ Approval Workflow

### Minor Version Updates (Backward-Compatible)

1. **Submission:** Requesting team commits proposed contract to `/docs/integration_contracts/`
2. **Notification:** GitHub notification + Slack alert to reviewing team
3. **Review Period:** 48-hour SLA for review and approval
4. **Approval Methods:**
   - Explicit approval via GitHub comment
   - Auto-approval if no objections within 48 hours
5. **Implementation:** Approved contract becomes active for implementation

### Major Version Updates (Breaking Changes)

1. **Pre-Review Meeting:** Mandatory 30-minute sync meeting before submission
2. **Submission:** Detailed impact analysis document required
3. **Review Period:** 7-day review window
4. **Deprecation Notice:** 30-day grace period before enforcement
5. **Dual-Version Support:** Both teams must support old + new versions during grace period
6. **Final Cutover:** Coordinated deployment after grace period

---

## 🗑️ Deprecation Policy

### Deprecation Timeline

**Breaking changes require a 30-day grace period:**

1. **Day 0:** Deprecation notice published in contract
2. **Day 1-30:** Both teams support old and new schemas simultaneously
3. **Day 30:** Old schema officially retired

### Deprecation Notice Format

When deprecating fields, the contract must include:

```json
{
  "field_name": "Old Field Name",
  "field_id": 123456789,
  "status": "DEPRECATED",
  "deprecation_date": "2025-12-01",
  "removal_date": "2025-12-31",
  "replacement_field": "New Field Name",
  "migration_guide": "Use new_field_id instead. Values map 1:1."
}
```

### Grace Period Rules

- **CRM Team:** Must continue reading deprecated fields until removal date
- **Data Team:** Must write to both old and new fields during grace period
- **Both Teams:** Must not delete deprecated fields until removal date

---

## 📢 Communication Protocols

### Regular Sync Meetings

- **Frequency:** Weekly 15-minute standup (every Monday 10am MT)
- **Attendees:** CRM Lead + Data Pipeline Lead (minimum)
- **Agenda:**
  - Contract change requests
  - Enrichment success rate review
  - Upcoming deprecations
  - Production issues

### Alert Channels

1. **GitHub Notifications:**

   - All contract commits trigger automatic notifications
   - Use PR comments for approval/objections

2. **Slack Alerts:**

   - Channel: `#crm-pipeline-integration`
   - Use for urgent issues (< 4 hour response time)
   - Alert conditions:
     - Contract approval needed
     - Production sync failures
     - Schema violations detected

3. **Email Escalation:**
   - Use only for critical production issues
   - Escalate if Slack response > 4 hours

### Notification Templates

**New Contract Submission:**

```
🔔 CONTRACT REVIEW NEEDED
Version: v1.1
Type: Minor (backward-compatible)
Review SLA: 48 hours (due: YYYY-MM-DD HH:MM MT)
Link: [GitHub PR URL]
Summary: Adding 10 enriched fields for lead scoring
```

**Deprecation Warning:**

```
⚠️ DEPRECATION NOTICE
Field: "Old Lead Source"
Removal Date: 2025-12-31
Grace Period: 30 days
Action Required: Migrate to "Lead Source V2" by removal date
Migration Guide: [Link to docs]
```

---

## 🔄 Change Request Process

### When to Submit a Contract Change

**Data Team initiates change when:**

- Adding new enriched fields from pipeline
- Modifying enrichment algorithms (affecting field values)
- Deprecating underperforming enrichment fields

**CRM Team initiates change when:**

- Requesting new data points for agent workflow
- Reporting field type mismatches or validation issues
- Proposing schema optimizations

### Change Request Template

Create a new file in `/docs/integration_contracts/proposals/` with this structure:

```markdown
# Contract Change Request: [Brief Title]

**Requested By:** [CRM Team / Data Team]
**Request Date:** YYYY-MM-DD
**Target Version:** v1.X

## Proposed Changes

**Fields to Add:**

- Field Name: [name]
- Field Type: [number/text/category/money/date]
- Podio Field ID: TBD (will be assigned after approval)
- Business Justification: [why this field is needed]
- Dialer Usage: [how CRM will use this field]

**Fields to Modify:**

- Current Field: [name and ID]
- Proposed Change: [description]
- Impact Analysis: [who is affected]

**Fields to Deprecate:**

- Field Name: [name and ID]
- Deprecation Date: [date]
- Removal Date: [date + 30 days]
- Migration Path: [how to transition]

## Impact Assessment

**CRM Team Impact:**

- [ ] UI changes required
- [ ] Code changes required
- [ ] Testing required
- [ ] Agent training required

**Data Team Impact:**

- [ ] Scraping logic changes
- [ ] Enrichment algorithm changes
- [ ] Sync function changes
- [ ] Database schema changes

## Timeline

- Approval Target: [date]
- Implementation Start: [date]
- Testing Complete: [date]
- Production Deploy: [date]
```

### Approval Process

1. Submit change request as GitHub PR to `docs/integration_contracts/proposals/`
2. Tag reviewing team in PR
3. Wait for 48-hour review period (minor) or 7-day period (major)
4. Address feedback/questions
5. Merge after approval
6. Move approved contract to root of `/docs/integration_contracts/`

---

## 📁 Contract File Naming Convention

**Active Contracts:**

- `podio-schema-v1.0.json` - Current production baseline
- `podio-schema-v1.1.json` - Next approved contract
- `podio-schema-v2.0.json` - Future major version

**Archived Contracts:**

- `archive/podio-schema-v1.0.json` - Superseded by v1.1
- `archive/podio-schema-v1.1.json` - Superseded by v2.0

**Proposals (Under Review):**

- `proposals/add-enriched-fields-v1.1.md` - Change request
- `proposals/deprecate-legacy-source-v2.0.md` - Breaking change proposal

---

## 🧪 Contract Validation

### Pre-Deployment Validation

Before implementing any contract:

1. **Schema Validation:**

   - All field IDs are valid Podio field IDs
   - Field types match Podio field types
   - No duplicate field IDs

2. **Business Logic Validation:**

   - All `dialer_usage` specifications are complete
   - Field priorities are assigned (1-10)
   - Business justifications reference Core Pillars

3. **Technical Validation:**
   - JSON syntax is valid
   - All required contract sections present
   - Version numbers follow semantic versioning

### Post-Deployment Verification

After implementing a new contract:

1. **CRM Team Verification:**

   - All fields accessible via Podio API
   - Field values match expected types
   - UI displays fields correctly

2. **Data Team Verification:**

   - Sync function writes to all new fields
   - No errors during data push
   - Field mappings correct (Supabase → Podio)

3. **Joint Verification:**
   - End-to-end test with sample data
   - Performance benchmarks met
   - Both teams sign off

---

## 🚨 Contract Violation Protocol

### Violation Types

**Type 1: Schema Mismatch (Critical)**

- Field ID doesn't exist in Podio
- Field type doesn't match contract
- Required field missing

**Type 2: Data Quality (High)**

- Field values outside expected range
- Invalid data format
- Null values in required fields

**Type 3: Performance (Medium)**

- Sync time exceeds SLA
- Workspace load time > 3 seconds
- API rate limits hit

### Violation Response

1. **Detection:** Automated monitoring alerts both teams
2. **Notification:** Slack alert within 15 minutes
3. **Assessment:** Determine severity and impact
4. **Rollback Decision:**

   - Critical violations → immediate rollback to previous contract version
   - High violations → 24-hour remediation window
   - Medium violations → monitor and fix in next sprint

5. **Root Cause Analysis:** Document what went wrong
6. **Prevention:** Update validation tests to catch similar issues

---

## 📊 Contract Metrics & KPIs

### Data Team Metrics

- **Enrichment Success Rate:** % of leads with all fields populated

  - Target: > 90%
  - Alert Threshold: < 85%

- **Sync Latency:** Time from Supabase write to Podio sync

  - Target: < 5 minutes
  - Alert Threshold: > 15 minutes

- **Data Quality Score:** % of fields passing validation
  - Target: > 95%
  - Alert Threshold: < 90%

### CRM Team Metrics

- **Field Extraction Success:** % of API calls successfully reading fields

  - Target: > 99%
  - Alert Threshold: < 95%

- **Workspace Load Time:** Time to render Lead Intelligence Panel

  - Target: < 2 seconds
  - Alert Threshold: > 3 seconds

- **Field Utilization Rate:** % of enriched fields actually used by agents
  - Target: > 80%
  - Monitor for deprecation candidates

### Joint Metrics

- **Contract Compliance:** % of production data matching contract spec

  - Target: 100%
  - Alert Threshold: < 98%

- **Integration Uptime:** % of time both systems operating normally
  - Target: > 99.5%
  - Alert Threshold: < 99%

---

## 📝 Contract Change Log

All contract changes must be documented here:

### v1.0 (2025-11-25) - Production Baseline

**Status:** Active  
**Type:** Initial Release  
**Changes:** Documented existing Master Lead App fields as pre-enrichment baseline  
**Approved By:** CRM Team  
**Notes:** This contract reflects the current production state before V4.0 integration

---

## 🤝 Team Responsibilities

### CRM Team (This Project)

**Contract Responsibilities:**

- Review and approve Data Team's proposed enrichment fields (48hr SLA)
- Maintain field ID mappings in `config.py`
- Implement UI for displaying enriched data
- Report field usage statistics quarterly

**Communication Responsibilities:**

- Attend weekly sync meetings
- Respond to Slack alerts within 4 hours
- Provide feedback on field priorities and business value

### Data Team (Data Pipeline Project)

**Contract Responsibilities:**

- Propose enrichment field specifications
- Implement sync functions matching contract
- Maintain enrichment success rate > 90%
- Archive deprecated contracts after removal date

**Communication Responsibilities:**

- Attend weekly sync meetings
- Respond to Slack alerts within 4 hours
- Notify CRM team of sync failures within 15 minutes

---

## 📂 Directory Structure

```
docs/integration_contracts/
├── README.md (this file - governance protocol)
├── podio-schema-v1.0.json (current production contract)
├── archive/
│   └── (historical contracts for audit trail)
└── proposals/
    └── (change requests under review)
```

---

## 🔗 Related Documentation

- **Project Status:** [`docs/project_status.md`](../project_status.md) - V4.0 phase tracking
- **Podio Configuration:** [`config.py`](../../config.py) - Field ID mappings
- **Master Lead App:** [`docs/Podio Master Lead App.md`](../Podio%20Master%20Lead%20App.md) - App documentation

---

**Document Owner:** CRM Team
**Last Updated:** 2025-11-29
**Next Review:** Upon Contract v2.0 Phase 1 field creation
