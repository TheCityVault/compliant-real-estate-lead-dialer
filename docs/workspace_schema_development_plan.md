# **V2.0 Agent Workspace Schema & Development Plan**

This document formalizes the data structure and critical dependencies for implementing the **Agent Workspace** (V2.0 architecture). All development efforts must be based on this schema to ensure continuity and accurate reporting.

## **1\. Mandatory Data Schema Definition**

The Agent Workspace UI must present the following fields. The development team needs to receive the corresponding Podio Field IDs for the **Podio Target** column.

| \# | Field Name | Input Type | Required? | Productivity/Continuity Value | Podio Target (PM Must Provide ID) |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **1** | **Disposition Code** | Dropdown / Category | **YES** | Primary reporting metric. Locks the agent into selecting the call outcome. | **274851083** (Category Field) |
| **2** | **Agent Notes / Summary** | Multi-Line Text | NO | **Continuity:** Crucial context for follow-up. Stored as plain text. | **274851084** (Text Field) |
| **3** | **Seller Motivation Level** | Dropdown / Category | NO | **Qualifying:** Used to prioritize leads for follow-up sprints. | **274851085** (Category Field) |
| **4** | **Next Action Date** | Date Picker | Conditional | **Efficiency:** Schedules the next touchpoint. Only required if Disposition is positive. | **274851086** (Date Field) |
| **5** | **Target Asking Price** | Number/Currency | NO | **Pipeline Value:** Required for forecasting future revenue potential. | **274851087** (Money Field) |

### **Format Instructions (Agent Guidance)**

To maximize data quality (as requested):

* **Target Asking Price:** Placeholder text should be e.g., 450,000 or Undisclosed.  
* **Next Action Date:** Placeholder text should be e.g., MM/DD/YYYY.

## **2\. Technical Dependencies & Critical Constraints (Path 2\)**

Implementing the direct write (Path 2\) requires solving these technical constraints in the Vercel backend.

### **A. Environment & Dependencies**

| Constraint | Action Required | Responsibility |
| :---- | :---- | :---- |
| **Podio SDK** | The requirements.txt file **must** be updated to include the Podio Python SDK. | Development Team |
| **Credentials** | PODIO\_CLIENT\_ID, PODIO\_CLIENT\_SECRET, and the Call Activity App APP\_ID **must** be securely configured in the Vercel environment. | Project Manager / Infrastructure |

### **B. Core Write-Back Logic (/submit\_call\_data Endpoint)**

The endpoint that receives the agent's submission must handle the following logic in sequence:

1. **Input Sanitization:** Clean all text and ensure Target Asking Price is a valid number/float.  
2. **Data Type Conversion:** Convert the browser's date string into the ISO 8601 format required by the Podio API for the Next Action Date.  
3. **Podio Field Mapping:** Use the Podio SDK to construct the item payload, explicitly mapping the Agent Workspace fields to the correct Podio Field IDs (e.g., mapping field \#1 to field\_id\_XXX).  
4. **Item Linking:** **CRITICAL:** Ensure the payload includes the data needed to establish the **Relationship Link** back to the original Lead Item using its item\_id. This prevents the new Call Activity Item from being "orphaned."  
5. **Simultaneous Logging:** The Vercel function must log the complete, final agent data (Notes, Disposition, Price) to a dedicated Firestore collection (disposition\_logs) for auditing and compliance purposes.

### **C. Agent Workflow & Validation**

1. **Front-End Validation:** The Agent Workspace UI must use JavaScript to enforce that **Disposition Code (Field \#1)** is selected before the "Call Completed & Submit" button is enabled.  
2. **Conditional Logic:** Implement conditional validation: If the agent selects a positive disposition (Appointment Set, Callback Scheduled), the **Next Action Date (Field \#4)** must become mandatory.  
3. **Submit Status:** Upon successful submission to /submit\_call\_data, the agent's browser window must display a large, clear confirmation message ("Success\! Data written to Podio.") and then be ready to close.