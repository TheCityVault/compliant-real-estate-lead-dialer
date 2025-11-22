# Twilio VOIP Environment Variables

## Required Environment Variables for Twilio Voice SDK

To enable browser-based VOIP calling with the Twilio Voice JavaScript SDK, the following environment variables must be configured in your deployment environment (e.g., Vercel):

### New Variables Required

#### `TWILIO_API_KEY`
- **Description**: Twilio API Key SID for generating access tokens
- **Format**: Starts with `SK` (e.g., `SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
- **Required**: Yes
- **Purpose**: Used to sign JWT access tokens for the Voice SDK

**How to obtain:**
1. Go to https://console.twilio.com/us1/account/keys-credentials/api-keys
2. Click "Create API Key"
3. Name it (e.g., "VOIP Client Access")
4. Select "Standard" key type
5. Copy the **SID** (starts with `SK`)

#### `TWILIO_API_SECRET`
- **Description**: Secret key associated with the API Key
- **Format**: Random alphanumeric string
- **Required**: Yes
- **Purpose**: Used with API Key to sign access tokens
- **Security**: Keep this secret! Only shown once during API Key creation

**How to obtain:**
1. During API Key creation (see above)
2. Copy the **Secret** value immediately (you won't see it again)
3. Store it securely in your environment variables

### Existing Variables (Already Configured)

These variables should already be set but are required for the complete VOIP flow:

- `TWILIO_ACCOUNT_SID` - Your Twilio Account SID
- `TWILIO_AUTH_TOKEN` - Your Twilio Auth Token
- `TWILIO_PHONE_NUMBER` - Your Twilio phone number (E.164 format)

## Configuration in Vercel

1. Navigate to your project in Vercel Dashboard
2. Go to **Settings** → **Environment Variables**
3. Add the following variables:

```
TWILIO_API_KEY=SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_API_SECRET=your_api_secret_here
```

4. Make sure these are set for all environments (Production, Preview, Development)
5. Redeploy your application for changes to take effect

## Testing the Configuration

After setting the environment variables:

1. Visit your workspace URL: `https://your-app.vercel.app/workspace?item_id=<ITEM_ID>`
2. Check the browser console for:
   - `Twilio token obtained for identity: agent_XXXXX`
   - `✅ Twilio Device is ready to receive calls`
3. Verify the VOIP status indicator shows "Ready" (green text)
4. Test calling with `client:` identifier:
   - Enter `client:test_user` in the Agent Connection field
   - Click "Initiate Call"
   - Browser should receive incoming call
   - Call auto-accepts and connects

## Security Best Practices

1. **Never commit API secrets to git** - Use environment variables only
2. **Rotate API keys periodically** - Create new keys and update environment variables
3. **Use separate keys per environment** - Different keys for dev/staging/production
4. **Monitor API key usage** - Check Twilio console for unusual activity
5. **Restrict API key permissions** - Use Standard keys (not Main credentials) for better security

## Troubleshooting

### Error: "Twilio API credentials not configured"
- **Cause**: `TWILIO_API_KEY` or `TWILIO_API_SECRET` not set
- **Fix**: Add both variables to Vercel environment settings and redeploy

### Error: "Failed to fetch Twilio token"
- **Cause**: Backend `/token` endpoint not accessible or returning errors
- **Fix**: Check Vercel deployment logs for backend errors

### Device shows "SDK Error"
- **Cause**: Invalid API credentials or token generation failure
- **Fix**: Verify API Key and Secret are correctly copied from Twilio Console

### Device never shows "Ready"
- **Cause**: JavaScript errors preventing SDK initialization
- **Fix**: Open browser DevTools console and check for errors

## Additional Resources

- [Twilio Access Tokens Documentation](https://www.twilio.com/docs/iam/access-tokens)
- [Twilio Voice JavaScript SDK Quickstart](https://www.twilio.com/docs/voice/sdks/javascript/get-started)
- [Twilio API Keys Best Practices](https://www.twilio.com/docs/iam/api-keys)