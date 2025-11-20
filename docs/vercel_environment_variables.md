# Vercel Environment Variables Configuration

This document lists all required environment variables for the Compliant Real Estate Lead Dialer application when deployed to Vercel.

## Table of Contents
- [Twilio Configuration](#twilio-configuration)
- [Podio Configuration](#podio-configuration)
- [Google Cloud Platform (Firestore)](#google-cloud-platform-firestore)
- [Vercel Project](#vercel-project)
- [Phone Numbers](#phone-numbers)

---

## Twilio Configuration

### `TWILIO_ACCOUNT_SID`
- **Description**: Your Twilio Account SID
- **Format**: Alphanumeric string starting with "AC"
- **Example**: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **Required**: Yes

### `TWILIO_AUTH_TOKEN`
- **Description**: Your Twilio Auth Token
- **Format**: 32-character hexadecimal string
- **Example**: `3a412a66125879743fd325feefa3bbaa`
- **Required**: Yes

---

## Podio Configuration

### Authentication Credentials

#### `PODIO_CLIENT_ID`
- **Description**: Podio OAuth Client ID
- **Format**: String
- **Example**: `compliant-dialer-production`
- **Required**: Yes

#### `PODIO_CLIENT_SECRET`
- **Description**: Podio OAuth Client Secret
- **Format**: Long alphanumeric string
- **Example**: `2KlVwmKbYRKit2NCmCcrbdUCyqmLOfFmcnLcMNLyMfH7vsGbbVGooRCu35hmGKAz`
- **Required**: Yes

#### `PODIO_USERNAME`
- **Description**: Podio account username (email)
- **Format**: Email address
- **Example**: `c1tyv4ult@gmail.com`
- **Required**: Yes

#### `PODIO_PASSWORD`
- **Description**: Podio account password
- **Format**: String
- **Example**: `!AEVw66D2LSDvXd`
- **Required**: Yes

#### `PODIO_WORKSPACE_ID`
- **Description**: Podio Workspace ID
- **Format**: Numeric string
- **Example**: `10485937`
- **Required**: Yes

### App-Specific Credentials

#### `PODIO_MASTER_LEAD_APP_ID`
- **Description**: Podio App ID for the Master Lead App (used for reading lead data)
- **Format**: Numeric string
- **Example**: `30549135`
- **Required**: Yes
- **Usage**: Reading lead information from the Master Lead App

#### `PODIO_MASTER_LEAD_APP_TOKEN`
- **Description**: Podio App Token for the Master Lead App
- **Format**: 32-character hexadecimal string
- **Example**: `4cdb95cc82ec709fb273116ed9bf0bb3`
- **Required**: Yes
- **Usage**: Authentication for reading from Master Lead App

#### `PODIO_CALL_ACTIVITY_APP_ID`
- **Description**: Podio App ID for the Call Activity App (used for writing call dispositions - V2.0)
- **Format**: Numeric string
- **Example**: `30549170`
- **Required**: Yes (for V2.0 features)
- **Usage**: Writing call disposition data to the Call Activity App

#### `PODIO_CALL_ACTIVITY_APP_TOKEN`
- **Description**: Podio App Token for the Call Activity App
- **Format**: 32-character hexadecimal string
- **Example**: `a3dc1157ea504c0ca5b82cd7af23cff4`
- **Required**: Yes (for V2.0 features)
- **Usage**: Authentication for writing to Call Activity App

---

## Google Cloud Platform (Firestore)

### `GCP_SERVICE_ACCOUNT_JSON`
- **Description**: Google Cloud Platform service account credentials in JSON format
- **Format**: JSON string (entire service account key file content)
- **Example**:
  ```json
  {
    "type": "service_account",
    "project_id": "your-project-id",
    "private_key_id": "...",
    "private_key": "...",
    "client_email": "...",
    ...
  }
  ```
- **Required**: Yes (for Firestore call logging)
- **Note**: In Vercel, paste the entire JSON content as a single-line string

### Important: `GCP_SERVICE_ACCOUNT_JSON` is the ONLY GCP Variable Used

This project uses `GCP_SERVICE_ACCOUNT_JSON` exclusively for GCP authentication.

**NOT USED:**
- `GOOGLE_APPLICATION_CREDENTIALS` - This variable (which typically points to a JSON file path) is **NOT** used in this project. The application reads credentials directly from the `GCP_SERVICE_ACCOUNT_JSON` environment variable instead.

### Local Development Setup

For local development:
1. Obtain your GCP service account JSON key file from Google Cloud Console
2. Set `GCP_SERVICE_ACCOUNT_JSON` in your local `.env` file to the **full JSON content** (not a file path)
3. The application will automatically parse this JSON string to authenticate with Firestore

For production (Vercel):
1. Copy the entire contents of your service account JSON key file
2. Paste it into the `GCP_SERVICE_ACCOUNT_JSON` environment variable in Vercel settings
3. Vercel will handle the JSON string appropriately

---

## Vercel Project

### `PROJECT_ID`
- **Description**: Vercel Project ID
- **Format**: String starting with `prj_`
- **Example**: `prj_cmXFnDtMoMok4la2110Wn2IeDO00`
- **Required**: No (informational)

---

## Phone Numbers

### `TWILIO_PHONE_NUMBER`
- **Description**: Your Twilio phone number (the number that will initiate calls)
- **Format**: E.164 format (e.g., +1XXXXXXXXXX)
- **Example**: `+17207307865`
- **Required**: Yes

### `AGENT_PHONE_NUMBER`
- **Description**: The agent's phone number (your phone that receives the calls)
- **Format**: E.164 format (e.g., +1XXXXXXXXXX)
- **Example**: `+15179184262`
- **Required**: Yes

---

## Setting Environment Variables in Vercel

1. Go to your Vercel project dashboard
2. Navigate to **Settings** → **Environment Variables**
3. For each variable listed above:
   - Enter the **Key** (exact variable name)
   - Enter the **Value**
   - Select which environments to apply to (**Production**, **Preview**, **Development**)
   - Click **Save**

### Important Notes

- **Case Sensitivity**: Variable names are case-sensitive. Use exact names as listed.
- **No Quotes**: Do not wrap values in quotes in Vercel (unlike `.env` files).
- **JSON Formatting**: For `GCP_SERVICE_ACCOUNT_JSON`, paste the entire JSON as a single line or use Vercel's multiline input.
- **Redeploy**: After adding/updating environment variables, redeploy your application for changes to take effect.

---

## Naming Convention

### V2.0 Clear Naming Convention (Current)

The current naming convention clearly distinguishes between different Podio apps:
- `PODIO_MASTER_LEAD_APP_*` - For reading lead data from the Master Lead App
- `PODIO_CALL_ACTIVITY_APP_*` - For writing call dispositions to the Call Activity App (V2.0 feature)

### Migration from V1.0

If migrating from V1.0, the following variable names have changed:
- ~~`PODIO_APP_ID`~~ → `PODIO_MASTER_LEAD_APP_ID` (for Master Lead App)
- ~~`PODIO_APP_TOKEN`~~ → `PODIO_MASTER_LEAD_APP_TOKEN` (for Master Lead App)

The old naming caused conflicts because two different apps shared the same variable names.

---

## Security Best Practices

1. **Never commit credentials**: Keep `.env` files in `.gitignore`
2. **Use environment-specific values**: Different credentials for development vs. production
3. **Rotate secrets regularly**: Update tokens and passwords periodically
4. **Limit access**: Only grant necessary permissions to service accounts
5. **Monitor usage**: Check for unexpected API calls or authentication attempts

---

## Troubleshooting

### Podio Authentication Failures
- Verify `PODIO_USERNAME` and `PODIO_PASSWORD` are correct
- Check that `PODIO_CLIENT_ID` and `PODIO_CLIENT_SECRET` match your OAuth app
- Ensure app tokens (`PODIO_MASTER_LEAD_APP_TOKEN`, `PODIO_CALL_ACTIVITY_APP_TOKEN`) are valid

### Twilio Call Issues
- Confirm `TWILIO_PHONE_NUMBER` is a valid Twilio number
- Verify `AGENT_PHONE_NUMBER` is in E.164 format
- Check `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` are correct

### Firestore Logging Issues
- Validate `GCP_SERVICE_ACCOUNT_JSON` is properly formatted
- Ensure the service account has Firestore permissions
- Check that the project ID in the JSON matches your GCP project

---

## Version History

- **V2.0** (2025-11-20): Implemented clear Podio app naming convention to support multiple Podio apps
- **V1.0** (Initial): Basic environment variable setup