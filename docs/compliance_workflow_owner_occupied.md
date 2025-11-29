# **Compliance Workflow Design: Owner Occupied Gate (CFPA/Dodd-Frank)**

**Document Type:** Technical Design Specification  
**Target Audience:** Code Mode (Implementation), Lead Manager (Operations)  
**Author:** High-Level Advisor  
**Date:** 2025-11-29  
**Status:** **APPROVED FOR IMPLEMENTATION (Phase 1.4)**

---

## **1. Executive Summary & Strategic Alignment**

### **The Risk (Pillar 1: Compliance)**

Distressed homeowners who occupy their property are a protected class under the **Consumer Financial Protection Act (CFPA)** and state-specific laws like the **Colorado Foreclosure Protection Act (CFPA)**.

- **Risk:** Soliciting these owners with standard "cash offer" scripts can be construed as "foreclosure consulting," triggering strict contract requirements, rescission rights, and criminal penalties for non-compliance.
- **Goal:** Prevent agents from inadvertently treating an Owner-Occupied lead like a standard absentee investor lead.

### **The Solution (Pillar 5: Scalability)**

We will implement a **"Hard Gate"** in the software. This is not a policy; it is a code-enforced block that prevents standard dialing until specific "Safe Harbor" actions are taken by the agent.

---

## **2. Data Logic & State Definitions**

The gate is controlled by the Podio field `Owner Occupied` (Field ID: TBD in Phase 1).

| Value         | State             | System Behavior                                                     |
| :------------ | :---------------- | :------------------------------------------------------------------ |
| **'Yes'**     | 🔴 **RESTRICTED** | **Hard Gate Active.** Auto-dialing BLOCKED. SMS Automation BLOCKED. |
| **'Unknown'** | 🟠 **CAUTION**    | **Hard Gate Active.** Treated as 'Yes' until manually verified.     |
| **'No'**      | 🟢 **STANDARD**   | Standard workflow. Auto-dialing and SMS allowed.                    |

---

## **3. The "Hard Gate" Mechanics**

When a lead is loaded into `workspace.html`, the system checks `lead_data.owner_occupied`.

### **3.1 Blocked Actions (Default State)**

If State is **RESTRICTED** or **CAUTION**:

1.  **Dialer Button:** Disabled (Greyed out). Text changes to "⚠️ Compliance Check Required".
2.  **SMS Input:** Hidden or Disabled.
3.  **Script Panel:** Hidden or replaced with "Compliance Warning".
4.  **Keyboard Shortcuts:** 'Enter' to dial is disabled.

### **3.2 The "Safe Harbor" Workflow (Unlocking)**

To proceed, the agent must execute a **Manual Override**:

1.  **Action:** Agent clicks the disabled Dialer button (or a specific "Unlock" icon).
2.  **Gate:** A **Compliance Modal** appears.
    - **Header:** "⚠️ OWNER OCCUPIED DISCLOSURE REQUIRED"
    - **Body:** "This property is flagged as Owner Occupied. You MUST read the Foreclosure Consultant Disclaimer immediately upon connection."
    - **Checkbox:** "I acknowledge I will read the required disclaimer."
    - **Action:** "Unlock Dialer & Load Compliance Script" button.
3.  **Result:**
    - Dialer unlocks for **ONE CALL ONLY**.
    - Script Panel loads the **"Owner Occupied / CFPA Compliant"** script (emphasizing "I am a buyer, not a consultant").
    - **Audit Log:** The unlock action is logged to the database with timestamp and agent ID.

---

## **4. UI/UX Specifications (`workspace.html`)**

### **4.1 Visual Indicators**

- **Header Badge:**
  - If 'Yes': `[🏠 Owner Occupied]` (Red Background, White Text)
  - If 'Unknown': `[❓ Occupancy Unknown]` (Orange Background, White Text)
- **Intelligence Panel:**
  - In the "Compliance & Risk" section, display the status prominently.

### **4.2 Script Dynamic Loading**

The workspace must support dynamic script injection based on this field.

- **Standard Script:** "Hi, I'm calling about buying your property..."
- **Compliance Script:** "Hi, this is [Name]. I'm calling as a private buyer interested in [Address]. **I want to be clear: I am not a foreclosure consultant, I am not offering to save your home, and I am not charging any fees.** I am simply looking to buy a property in the neighborhood..."

---

## **5. Implementation Checklist (Code Mode)**

### **Step 1: Backend (`podio_service.py`)**

- [ ] Ensure `owner_occupied` field is extracted in `get_lead_intelligence()`.
- [ ] Map 'Yes', 'No', 'Unknown' values correctly.

### **Step 2: Frontend Logic (`workspace.html`)**

- [ ] **State Check:** On load, check `lead_data.owner_occupied`.
- [ ] **Disable Elements:** If Yes/Unknown, add `disabled` attribute to `#dial-button` and `#sms-input`.
- [ ] **Visuals:** Render the appropriate Badge in the Header.

### **Step 3: The Modal (`workspace.html`)**

- [ ] Create a hidden `div` for the Compliance Modal (Tailwind styled).
- [ ] Add event listener to the disabled dial button to trigger the modal.
- [ ] Implement "Unlock" logic:
  - [ ] Remove `disabled` attribute.
  - [ ] Update button text to "Initiate Compliant Call".
  - [ ] **CRITICAL:** Swap the text in the Script Panel (if present) or show a "Script Updated" toast.

### **Step 4: Audit Logging (Optional for Phase 1, Required for Phase 2)**

- [ ] (Phase 2) Send an event to the backend when "Unlock" is clicked to log the compliance acknowledgement.

---

## **6. Business Justification (ROI)**

- **Risk Mitigation:** A single CFPA lawsuit can cost $50k+ in legal fees and fines. This feature costs <4 hours of dev time.
- **Agent Confidence:** Agents hesitate when calling distressed leads. This workflow gives them a "Safe Harbor" script, increasing their confidence and dial volume on high-equity leads.
