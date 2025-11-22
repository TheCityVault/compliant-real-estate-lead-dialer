# Twilio VOIP Environment Variables - SDK v1.14

This document outlines the required Twilio environment variables for the VOIP functionality in the Compliant Real Estate Lead Dialer using Twilio Voice JavaScript SDK v1.14.

## Required Variables

### 1. TWILIO_ACCOUNT_SID
- **Purpose**: Your Twilio Account SID (identifier)
- **Format**: Starts with `AC` followed by 32 hexadecimal characters
- **Example**: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **How to obtain**: 
  - Log into [Twilio Console](https://console.twilio.com)
  - Copy from the Account Info section on the dashboard

### 2. TWILIO_AUTH_TOKEN
- **Purpose**: Authentication token for your Twilio account
- **Format**: 32-character hexadecimal string
- **Example**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **How to obtain**:
  - Log into [Twilio Console](https://console.twilio.com)
  - Copy from the Account Info section on the dashboard
  - Click "Show" to reveal the token

### 3. TWILIO_PHONE_NUMBER
- **Purpose**: Your Twilio phone number used as the caller ID
- **Format**: E.164 format (e.g., `+1XXXXXXXXXX`)
- **Example**: `+13035551234`
- **How to obtain**:
  - In Twilio Console, go to Phone Numbers → Manage → Active numbers
  - Copy your purchased number in E.164 format

### 4. TWILIO_TWIML_APP_SID ⭐ **NEW - REQUIRED FOR SDK v1.14**
- **Purpose**: TwiML Application SID for configuring outgoing call capabilities
- **Format**: Starts with `AP` followed by 32 hexadecimal characters
- **Example**: `APxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **How to obtain**:
  1. Go to [Twilio Console → Voice → TwiML Apps](https://console.twilio.com/us1/develop/voice/manage/twiml-apps)
  2. Click "Create new TwiML App" or use existing one
  3. **Configuration:**
     - **Friendly Name**: "Lead Dialer VOIP Client"
     - **Voice Request URL**: `https://your-app.vercel.app/dial` (use your actual deployment URL)
     - **Voice Request Method**: POST
     - **Voice Status Callback URL**: `https://your-app.vercel.app/call_status`
  4. Click "Save"
  5. Copy the **SID** (starts with `AP`)
- **Notes**:
  - **CRITICAL**: This is REQUIRED for SDK v1.14 compatibility
  - Without this, you'll get "Client version not supported" error (Code 31007)
  - The TwiML App connects the VOIP client to your backend call routing

### 5. AGENT_PHONE_NUMBER (Optional)
- **Purpose**: Default agent's phone number or VOIP client identifier
- **Format**: 
  - For phone: E.164 format (e.g., `+1XXXXXXXXXX`)
  - For VOIP: `client:username` format
- **Example**: 
  - Phone: `+13035551234`
  - VOIP: `client:john_doe`
- **Notes**:
  - Use phone format for testing with your actual phone
  - Use VOIP format (client:username) for browser-based calling
  - Can be overridden per-call by the "Agent Connection" field in workspace

## Setting Up in Vercel

1. Go to your Vercel project dashboard
2. Navigate to Settings → Environment Variables
3. Add each variable:
   - Name: Variable name (e.g., `TWILIO_ACCOUNT_SID`)
   - Value: Your value
   - Environment: Select Production, Preview, and Development as needed
4. **IMPORTANT**: Add the new `TWILIO_TWIML_APP_SID` variable
5. Click "Save"
6. **Redeploy** your application for changes to take effect

## SDK v1.14 Compatibility Requirements

The application uses Twilio Voice JavaScript SDK v1.14, which requires:
- **Twilio Python library**: v6.35.5 (pinned in `requirements.txt`)
- **ClientCapabilityToken**: For generating v1.x compatible tokens
- **TwiML App SID**: For allowing outgoing call capabilities
- **Token format**: Capability Token (not v2.x Access Token/JWT)

### Why SDK v1.14?

SDK v1.14 is the last stable version of the v1.x series that:
- Uses ClientCapabilityToken (simpler authentication)
- Requires only Account SID + Auth Token (no API keys needed)
- Has proven stability for browser-based VOIP
- Compatible with older Python library versions

## Testing the Configuration

After setting all environment variables:

1. Visit your workspace URL: `https://your-app.vercel.app/workspace?item_id=<ITEM_ID>`
2. Check the browser console for:
   - `✅ Twilio SDK loaded successfully`
   - `Twilio token obtained for identity: agent_XXXXX`
   - `✅ Twilio Device is ready to receive calls`
3. Verify the VOIP status indicator shows "Ready" (green text)
4. Test calling:
   - Enter `client:test_user` in the Agent Connection field
   - Click "Initiate Call"
   - Browser should receive incoming call
   - Call auto-accepts and connects to prospect

## Troubleshooting

### Error: "Client version not supported" (Code 31007)
- **Cause**: Missing `TWILIO_TWIML_APP_SID` or incorrect token generation
- **Fix**: 
  1. Verify `TWILIO_TWIML_APP_SID` is set in Vercel
  2. Verify TwiML App is configured with correct Voice URL
  3. Check that `requirements.txt` has `twilio==6.35.5`
  4. Redeploy after making changes

### Device shows "SDK Error"
- **Cause**: Token generation failure or network issues
- **Fix**: 
  1. Check Vercel deployment logs for Python errors
  2. Verify Account SID and Auth Token are correct
  3. Check browser console for detailed error messages

### Device shows "Initializing..." forever
- **Cause**: Twilio SDK not loading or JavaScript errors
- **Fix**: 
  1. Open browser DevTools console
  2. Check for 404 errors loading SDK from CDN
  3. Verify `workspace.html` loads SDK from: `https://sdk.twilio.com/js/client/v1.14/twilio.js`

### TwiML App Configuration Issues
- **Symptom**: Calls initiate but don't connect
- **Fix**:
  1. Verify TwiML App Voice URL matches your deployment
  2. Check it ends with `/dial` endpoint
  3. Verify it uses HTTPS (required for production)
  4. Test URL in browser to ensure it's accessible

## Security Notes

- **NEVER** commit these values to version control
- Use `.env` file for local development (already in `.gitignore`)
- Rotate your `TWILIO_AUTH_TOKEN` if it's ever exposed
- Use separate credentials for production vs. development if possible
- TwiML App SID can be public, but Auth Token must remain secret

## Additional Resources

- [Twilio Voice JavaScript SDK v1.14 Documentation](https://www.twilio.com/docs/voice/client/javascript/v1-14)
- [ClientCapabilityToken API Reference](https://www.twilio.com/docs/voice/client/capability-tokens)
- [TwiML Apps Documentation](https://www.twilio.com/docs/voice/twiml/apps)
- [Python SDK v6.x Documentation](https://www.twilio.com/docs/libraries/python)