# **Podio Master Lead App: Required Fields Blueprint**

This blueprint outlines the fields required for the main **Master Lead** Podio application. This app will store the distressed lead data, compliance statuses, and the click-to-dial interface.

## **Section 1: Core Lead Data (Editable via Import/User Input)**

|

| Field Name | Type | Description |

| Parcel ID | Text (Single Line) | Unique identifier for the property (e.g., R0623028). |

| Full Address | Text (Multi Line) | The complete mailing/property address. |

| Owner Name | Text (Single Line) | The name of the property owner. |

| Tax Delinquency Amount | Money | The amount owed (Currency: USD). |

| Best Contact Number | Phone | The primary number to call. |

| Alternate Contact Number | Phone | A secondary number. |

## **Section 2: Compliance & Status Management (Required for Dialer Logic)**

| Field Name | Type | Description |

| DNC Status | Category (Single) | Options: Clean (Ready to Call), DNC List, Manual Review Required. Default: Manual Review Required. |

| Contact Status | Category (Single) | Options: New Lead, Attempt 1, Attempt 2, Attempt 3, Success (Contacted), Disqualified. Default: New Lead. |

| Contact Timezone | Category (Single) | Options: EST, CST, MST, PST. This dictates compliant calling times. |

| Last Contact Attempt | Date | Timestamp of the last successful or failed call attempt. |

## **Section 3: Dialer Interface (Click-to-Dial Button)**

| Field Name | Type | Description |

| Dialer URL | Calculation | CRITICAL: This field will house the HTML/JS for the Click-to-Dial button. It calls the Vercel API Bridge. (See click\_to\_dial\_button.html) |

## **Section 4: Relationship & Logging**

| Field Name | Type | Description |

| Call Activity Log | App Reference | Reference to the Call Activity Log app (One-to-many relationship). |

