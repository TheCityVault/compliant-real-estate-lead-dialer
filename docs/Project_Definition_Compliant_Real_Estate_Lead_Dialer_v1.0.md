# **Project Definition: Compliant Real Estate Lead Dialer (v2.1)**

This document is the single source of truth for the **Compliant Real Estate Lead Dialer** project. It defines the goal, the streamlined architecture, and the technical constraints, including the integration of **Google Cloud Firestore** for reliable, immediate audit logging.

## **1\. Project Goal and Compliance Mandate**

The system's goal is to create a reliable, high-efficiency method for real estate agents to initiate a phone call from a **Podio** lead record, strictly enforcing TCPA compliance and automating the initial call logging process.

* **Compliance Mandate:** The architecture must adhere to the **Two-Leg Click-to-Dial** standard. The call initiation must be triggered by a **manual click** from the agent, and the system must call the **Agent first** (Leg 1), and then connect the Agent to the **Prospect** (Leg 2). This architecture avoids classification as an ATDS (Automated Telephone Dialing System).  
* **Audit Trail:** Every completed call must be fully recorded by Twilio, and the final call details must be logged **immediately** into a dedicated Firestore document.

## **2\. Architectural Overview (The Firestore-Enabled Bridge)**

The system functions as a resilient, serverless bridge. **The critical change is that Vercel writes directly to Firestore, eliminating the need for an external webhook step for immediate logging.**

|

| Component | Technology | Function | Immediate Data Destination |

| Frontend/Trigger | Podio (HTML Calculation Field) | Agent clicks the button to initiate the HTTP request. | Vercel /dial endpoint |

| API Bridge (Controller) | Python / Flask (Vercel) | Orchestrates the compliant call via Twilio SDK; handles status callbacks. | Firestore (call\_logs collection) |

| Telephony/Logging | Twilio | Initiates Leg 1 (Agent), bridges to Leg 2 (Prospect), records, and sends final status webhook. | Vercel /status\_webhook endpoint |

| Data Synchronization | Make.com / Zapier (DEFERRED) | Will eventually monitor Firestore and create the final Call Activity Log item in Podio. | (TBD \- Implementation Deferred) |

## **3\. Functional Requirements**

#### **A. Outbound Dialing Sequence (The /dial Endpoint)**

1. **Trigger:** The Podio button fires an HTTP GET request to the Vercel API /dial endpoint, passing necessary identifiers (item\_id, target\_number, owner\_name).  
2. **Agent Call (Leg 1):** The Vercel function uses the Twilio SDK to call the **Agent's fixed phone number** (AGENT\_PHONE\_NUMBER).  
3. **Prospect Connection (Leg 2):** The Python code embeds the TwiML instructions, which execute when the Agent answers, running a **\<Dial\>** command to the **Prospect's number** (target\_number).  
4. **Logging Hook:** The Twilio command **must** include a status\_callback parameter pointing to the Vercel /status\_webhook endpoint, ensuring the original item\_id is passed through via the query string.

#### **B. Call Logging Sequence (The /status\_webhook Endpoint)**

1. **Twilio Event:** When the call completes, Twilio sends an HTTP POST request to the Vercel API /status\_webhook.  
2. **Firestore Write (Audit Trail):** The Vercel endpoint extracts the Twilio data (CallSid, CallStatus, CallDuration) and the original item\_id. It then executes a **single write operation** to the **call\_logs collection in Firestore**, ensuring the audit data is instantly captured.  
3. **Podio Synchronization:** **The final step of syncing data from Firestore to the Podio Call Activity App via Make/Zapier is deferred to a later phase.**

## **4\. Technical Constraints & Dependencies**

| Constraint | Detail | Location |

| Platform | Python / Flask Serverless Architecture | Vercel |

| Database | Google Cloud Firestore must be used for all call logging. | Google Cloud Project |

| Code Locations | All Python logic in src/api\_bridge.py. Podio button logic in src/click\_to\_dial\_button.html. | src/ directory |

| Environment Variables (MANDATORY) | TWILIO\_ACCOUNT\_SID, TWILIO\_AUTH\_TOKEN, TWILIO\_PHONE\_NUMBER, AGENT\_PHONE\_NUMBER, Google Service Account Credentials (for Firestore access). | Vercel Configuration |

| Pending Integration | The Podio synchronization (PODIO\_WEBHOOK\_URL) is not required for initial deployment. | Deferred |

