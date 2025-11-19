# Podio Link Field Setup Guide
## Compliant Real Estate Lead Dialer Integration

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Configuration](#step-by-step-configuration)
4. [User Experience](#user-experience)
5. [Testing Instructions](#testing-instructions)
6. [Troubleshooting](#troubleshooting)
7. [Firestore Verification](#firestore-verification)

---

## Overview

### Why Link Field Instead of Calculation Field?

**The Problem with Calculation Fields:**
Podio calculation fields output **plain text only** and cannot render HTML or execute JavaScript. Our initial attempt to embed a clickable button directly in a calculation field failed because:

- Calculation fields strip all HTML tags
- JavaScript embedded in calculation fields is displayed as plain text
- No interactive elements (buttons, links) can be rendered within calculation field output

**The Link Field Solution:**
The Link field approach leverages Podio's native link field type, which:

- ✅ Supports HTTPS URLs natively
- ✅ Displays as a clickable link in the Podio interface
- ✅ Can be dynamically generated using a Calculation field
- ✅ Requires no additional software or browser extensions
- ✅ Works with the existing Vercel deployment
- ✅ Zero additional cost

### Architecture Overview

```
Agent clicks Link → Podio Link Field → Vercel /dial endpoint → Twilio → Agent's Phone (Leg 1) → Prospect's Phone (Leg 2) → Firestore Logging
```

---

## Prerequisites

Before configuring Podio, ensure the following are in place:

### 1. Vercel Deployment URL
Your application must be deployed to Vercel with a valid URL. 

**Example:**
```
https://compliant-real-estate-lead-dialer-90ucg6prp.vercel.app
```

**To find your Vercel URL:**
1. Log in to [Vercel Dashboard](https://vercel.com/dashboard)
2. Navigate to your project
3. Copy the production URL from the project overview

### 2. Environment Variables Configured
Verify the following environment variables are set in Vercel:

| Variable | Description | Example |
|----------|-------------|---------|
| `TWILIO_ACCOUNT_SID` | Your Twilio Account SID | `AC********************************` |
| `TWILIO_AUTH_TOKEN` | Your Twilio Auth Token | `3a412a66125879743fd325feefa3bbaa` |
| `TWILIO_PHONE_NUMBER` | Your Twilio phone number | `+17207307865` |
| `AGENT_PHONE_NUMBER` | Agent's phone receiving calls | `+15179184262` |
| `GCP_SERVICE_ACCOUNT_JSON` | Firestore credentials (JSON string) | `{"type": "service_account"...}` |

### 3. Podio App Structure
Your Podio app must have a phone number field containing the prospect's contact number.

**Required Field:**
- **Field Name:** "Best Contact Number" (or similar phone field)
- **Field Type:** Phone

---

## Step-by-Step Configuration

### Step 1: Create or Modify the Phone Number Field

1. Open your Podio workspace
2. Navigate to your Master Lead app
3. Ensure you have a **Phone field** to store the prospect's number
   - **Recommended Field Name:** "Best Contact Number"
   - **Field Type:** Phone
   - **Settings:** Configure with appropriate country code

### Step 2: Create a Calculation Field for the Dialer URL

This calculation field will dynamically generate the URL for each lead.

#### 2.1 Add New Field
1. Click **"Add Field"** in your Podio app
2. Select **"Calculation"** field type
3. Name it **"Dialer URL (Internal)"**

#### 2.2 Configure the Formula

**Formula:**
```
"https://compliant-real-estate-lead-dialer-90ucg6prp.vercel.app/dial?phone=" + @Best Contact Number
```

**Important Notes:**
- Replace `compliant-real-estate-lead-dialer-90ucg6prp.vercel.app` with your actual Vercel deployment URL
- The `@Best Contact Number` token must match your phone field's exact name
- Use the `.` operator for string concatenation in Podio formulas (not `+` if that doesn't work)
- Ensure the phone field name is wrapped with `@` symbols

**Alternative Formula Syntax (if concatenation issues occur):**
```
"https://your-vercel-url.vercel.app/dial?phone=".@Best Contact Number
```

#### 2.3 Field Settings
- **Output Type:** Text
- **Visibility:** You can hide this field from users since it's only used to generate the URL

### Step 3: Create the Link Field

This is the field users will actually click to initiate calls.

#### 3.1 Add New Field
1. Click **"Add Field"** in your Podio app
2. Select **"Link"** field type
3. Name it **"📞 Click to Dial"** (the emoji makes it visually distinctive)

#### 3.2 Configure Link Field Settings

**Option A: Using Globiflow (Recommended for automatic population)**

If you have Globiflow access:
1. Create a Globiflow automation that triggers when an item is created or updated
2. Set the automation to copy the value from **"Dialer URL (Internal)"** calculation field
3. Paste it into the **"📞 Click to Dial"** link field

**Option B: Manual Entry Template**

If not using automation, you can:
1. Create an item template that includes the link pattern
2. Users manually ensure the link field contains the correct URL before dialing

**Option C: Using Calculation Field Directly (Simplified)**

*Note: This approach assumes users can copy/paste from the calculation field into their browser or that you add instructions to do so.*

### Step 4: Add Instructions for Users

Create a **Text field** in your app with usage instructions:

**Field Name:** "How to Use Click-to-Dial"

**Content:**
```
📞 CLICK-TO-DIAL INSTRUCTIONS:

1. Click the link in the "📞 Click to Dial" field
2. Your desk phone will ring first
3. Answer your phone
4. You'll be automatically connected to the prospect
5. The call will be logged in Firestore automatically

⚠️ IMPORTANT: You MUST answer your phone when it rings, or the call will fail.
```

---

## User Experience

### What Happens When a User Clicks the Link?

1. **Link Click:**
   - User clicks the **"📞 Click to Dial"** link in Podio
   - A new browser tab opens with the Vercel endpoint

2. **Browser Feedback:**
   - User sees an HTML page displaying:
     ```
     📞 Initiating Call to [prospect_number]
     Your phone should ring shortly...
     ```
   - The page automatically closes after 3 seconds

3. **Agent's Phone Rings (Leg 1):**
   - Within 2-5 seconds, the agent's configured phone number receives a call from the Twilio number
   - Agent answers the phone

4. **Prospect Connection (Leg 2):**
   - Upon answering, agent hears: *"Connecting you to the prospect."*
   - Twilio automatically dials the prospect's number
   - When prospect answers, both parties are connected

5. **Automatic Logging:**
   - Call events (answered, completed) are sent to Firestore
   - Call SID, status, timestamp, and phone numbers are recorded
   - No manual logging required

---

## Testing Instructions

### Test with a Safe Number

**IMPORTANT:** For initial testing, use your own mobile number as the prospect number to avoid accidentally calling real leads.

#### Test Procedure

1. **Create a Test Lead:**
   - In Podio, create a new lead item
   - Set **"Best Contact Number"** to your personal mobile: `+1234567890`
   - Verify the **"Dialer URL (Internal)"** field shows the correct URL
   - Populate the **"📞 Click to Dial"** link field (if using Globiflow, it should auto-populate)

2. **Initiate Test Call:**
   - Click the **"📞 Click to Dial"** link
   - Browser tab should open showing "Initiating Call..." message
   - Tab should auto-close after 3 seconds

3. **Verify Leg 1 (Agent Call):**
   - Your configured agent phone (`+15179184262`) should ring
   - Answer the call
   - You should hear: *"Connecting you to the prospect."*

4. **Verify Leg 2 (Prospect Call):**
   - Your test mobile phone should start ringing
   - Answer it (if testing alone, you'll need to put agent phone on speaker or use another device)
   - Verify both phones are connected

5. **End Call:**
   - Hang up from either phone
   - Call should disconnect cleanly

### Expected Results

✅ **Success Indicators:**
- Agent phone rings within 5 seconds of clicking link
- Agent hears Twilio connection message
- Prospect phone rings after agent answers
- Both parties can hear each other clearly
- Call logs appear in Firestore (see Firestore Verification section)

❌ **Failure Indicators:**
- No call received on agent phone → Check Vercel environment variables
- Error page in browser → Check Vercel deployment logs
- Call drops immediately → Check Twilio account balance
- No Firestore logs → Check GCP_SERVICE_ACCOUNT_JSON configuration

---

## Troubleshooting

### Issue 1: Link Field is Empty

**Symptom:** The "📞 Click to Dial" field shows no link

**Diagnosis:**
- Calculation field formula is incorrect
- Field reference `@Best Contact Number` doesn't match actual field name
- Globiflow automation not triggering (if using automation)

**Solution:**
1. Verify phone field name exactly matches the calculation formula
2. Test calculation field independently - it should display full URL
3. Check Globiflow automation logs for errors
4. Manually copy URL from calculation field into link field to test

### Issue 2: 400 Error - Missing Phone Number

**Symptom:** Browser shows "Missing phone number parameter"

**Diagnosis:**
- URL is malformed
- Phone field is empty in Podio
- Query parameter not being passed correctly

**Solution:**
1. Verify the phone field contains a valid number
2. Check calculation field output - should be: `https://your-url.vercel.app/dial?phone=+1234567890`
3. Ensure `?phone=` parameter is present in URL

### Issue 3: Agent Phone Doesn't Ring

**Symptom:** Browser shows success but no call received

**Diagnosis:**
- `AGENT_PHONE_NUMBER` environment variable incorrect or missing
- Twilio credentials invalid
- Twilio account suspended or out of credit

**Solution:**
1. Check Vercel environment variables:
   ```
   AGENT_PHONE_NUMBER=+15179184262
   TWILIO_ACCOUNT_SID=AC********************************
   TWILIO_AUTH_TOKEN=3a412a66125879743fd325feefa3bbaa
   TWILIO_PHONE_NUMBER=+17207307865
   ```
2. Verify Twilio account status at [twilio.com/console](https://www.twilio.com/console)
3. Check Vercel function logs for error messages

### Issue 4: Call Connects but No Prospect Connection (Leg 2)

**Symptom:** Agent phone rings and answers, but prospect is never connected

**Diagnosis:**
- `prospect_number` parameter not being passed to `/connect_prospect` endpoint
- Prospect number is invalid or incorrectly formatted

**Solution:**
1. Check Vercel logs for the prospect number being passed
2. Verify phone number format includes country code (e.g., `+12345678901`)
3. Review Twilio call logs for error details

### Issue 5: Calculation Field Shows Formula Instead of URL

**Symptom:** Calculation field displays the formula text rather than the generated URL

**Diagnosis:**
- Formula syntax error
- Field reference invalid
- Podio calculation engine error

**Solution:**
1. Verify formula uses correct syntax:
   ```
   "https://your-url.vercel.app/dial?phone=" + @Best Contact Number
   ```
2. Ensure `@Best Contact Number` exactly matches field name
3. Try alternative concatenation syntax:
   ```
   "https://your-url.vercel.app/dial?phone=".@Best Contact Number
   ```
4. Check for any special characters or spaces in field names

---

## Firestore Verification

### How to Confirm Calls Are Being Logged

#### Access Firestore Console

1. Navigate to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Click **"Firestore Database"** in left sidebar
4. Navigate to the **`call_logs`** collection

### Expected Log Entry Structure

Each completed call creates a document in the `call_logs` collection with the following fields:

```json
{
  "CallSid": "CA1234567890abcdef1234567890abcdef",
  "CallStatus": "completed",
  "Direction": "outbound-api",
  "From": "+17207307865",
  "To": "+15179184262",
  "Timestamp": "2025-01-19T05:00:00.000Z"
}
```

**Field Descriptions:**

| Field | Description | Example Value |
|-------|-------------|---------------|
| `CallSid` | Twilio's unique call identifier | `CA1234567890abcdef...` |
| `CallStatus` | Final call status | `completed`, `busy`, `no-answer`, `failed` |
| `Direction` | Call direction | `outbound-api` |
| `From` | Calling number (Twilio) | `+17207307865` |
| `To` | Receiving number (Agent or Prospect) | `+15179184262` |
| `Timestamp` | Firestore server timestamp | `2025-01-19T05:00:00Z` |

### Verifying Successful Logging

✅ **Success Indicators:**
- New documents appear in `call_logs` collection after each test call
- Document count increases with each call
- `CallStatus` field shows appropriate values (`completed`, `in-progress`, etc.)
- `Timestamp` matches when calls were made

❌ **Logging Failures:**
- No new documents after test calls
- `GCP_SERVICE_ACCOUNT_JSON` environment variable missing in Vercel
- Firestore security rules blocking writes
- Invalid service account credentials

### Manual Verification Query

To verify a specific call, note the **CallSid** from Twilio logs and search for it:

1. In Firestore Console, click **"Start Collection"** if `call_logs` doesn't exist
2. Use the search/filter to find documents where `CallSid` equals your test call's SID
3. Verify all fields are populated correctly

### Troubleshooting Missing Logs

If logs aren't appearing in Firestore:

1. **Check Vercel Logs:**
   ```
   Vercel Dashboard → Your Project → Deployments → [Latest] → Logs
   ```
   Look for messages like:
   - `"Firestore initialized successfully"`
   - `"Logged call status for Call SID: CA123... to Firestore"`
   - Any error messages about Firestore connection

2. **Verify Environment Variable:**
   ```
   Vercel Dashboard → Settings → Environment Variables
   ```
   Ensure `GCP_SERVICE_ACCOUNT_JSON` contains valid JSON service account credentials

3. **Check Firestore Rules:**
   In Firebase Console, go to **Firestore → Rules** and verify write access:
   ```
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /call_logs/{document=**} {
         allow read, write: if true; // Adjust based on security requirements
       }
     }
   }
   ```

4. **Test Service Account Credentials:**
   - Verify the service account has **"Cloud Datastore User"** role
   - Re-generate credentials if necessary
   - Update Vercel environment variable with new JSON

---

## Additional Resources

- **Podio Phone Field Research:** See [`Podio_Phone_Field_Click_to_Dial_Research.md`](Podio_Phone_Field_Click_to_Dial_Research.md) for detailed analysis of why phone field custom actions aren't viable

- **Project Definition:** Reference [`Project_Definition_Compliant_Real_Estate_Lead_Dialer.md`](Project_Definition_Compliant_Real_Estate_Lead_Dialer.md) for overall architecture

- **Twilio Documentation:** [Twilio Voice API](https://www.twilio.com/docs/voice)

- **Podio Field Types:** [Podio Field Documentation](https://docs.sharefile.com/en-us/podio/using-podio/creating-apps/the-fields-in-app-templates.html)

---

## Conclusion

The Link Field approach provides a reliable, cost-effective solution for click-to-dial functionality in Podio. While it requires a few configuration steps, once set up, it provides:

- ✅ Seamless one-click dialing from Podio
- ✅ Compliant two-leg call architecture
- ✅ Automatic call logging to Firestore
- ✅ No additional software or subscriptions required
- ✅ No maintenance overhead

For questions or issues not covered in this guide, check the Troubleshooting section or review Vercel deployment logs for detailed error messages.

---

**Document Version:** 1.0  
**Date:** 2025-01-19  
**Status:** Production Ready  
**Integration Type:** Link Field with Calculation Field URL Generation