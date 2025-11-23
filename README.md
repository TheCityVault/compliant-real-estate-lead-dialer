# Compliant Real Estate Lead Dialer - V3.2 Automated Recording Linkage

[![Production Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](https://github.com/yourusername/compliant-real-estate-lead-dialer)
[![Version](https://img.shields.io/badge/Version-3.2-blue)](https://github.com/yourusername/compliant-real-estate-lead-dialer/releases)
[![Platform](https://img.shields.io/badge/Platform-Vercel-black)](https://vercel.com)
[![TCPA Compliant](https://img.shields.io/badge/TCPA-Compliant-success)](https://www.fcc.gov/tcpa)

**🎉 Production Ready - Version 3.2 (Automated Recording Linkage Edition)**

A compliant, two-leg dialing system for real estate lead calling with **browser-based VOIP** for agent connections and **fully automated call recording linkage to Podio**.

## Current Version: V3.2 - Automated Call Recording Linkage ✅

### Latest Feature: CallSid-to-PodioItemId Mapping

V3.2 completes the automated call recording workflow by implementing persistent state mapping infrastructure. Recording URLs are now automatically written to Podio Call Activity items without manual intervention.

**Key Capabilities:**
- ✅ Real-time CallSid capture during call initiation
- ✅ Persistent CallSid→PodioItemId mapping in Firestore
- ✅ Automatic Podio updates via webhook integration
- ✅ Authentication-free recording playback through proxy endpoint
- ✅ Complete end-to-end automated recording linkage

**Previous Versions:**
- **V3.1:** Call Recording Infrastructure (TwiML, webhooks, proxy endpoint)
- **V3.0:** Agent Workspace UI with call disposition form
- **V2.1:** VOIP-only architecture with Twilio Client SDK

**🌐 Production Deployment:** https://compliant-real-estate-lead-dialer.vercel.app/

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Compliance](#compliance)
- [Documentation](#documentation)
- [Production Deployment](#production-deployment)
- [Version History](#version-history)

---

## 🎯 Overview

**Version:** 3.1.0 (Call Recording Edition)
**Status:** Production
**Architecture:** Browser-Based VOIP + Direct Podio API Integration + Automatic Call Recording

The Compliant Real Estate Lead Dialer enables real estate agents to initiate phone calls directly from Podio lead records with a single click using browser-based VOIP, while maintaining strict TCPA (Telephone Consumer Protection Act) compliance through a two-leg dialing architecture.

## V2.0 Features

### **Agent Workspace**
- Single, persistent browser window (no auto-close)
- Pre-loaded lead information (Name, Phone, Address)
- AJAX-based call initiation
- Mandatory 5-field disposition entry
- Real-time feedback and validation

### **Direct Podio Integration**
- Real-time Call Activity item creation
- 10-field data mapping (5 agent + 5 system fields)
- Automatic relationship linking to Master Lead items
- Eliminates Make/Zapier dependency
- Immediate data availability in Podio

### **Disposition Fields**
1. **Disposition Code** (required): Call outcome selection
2. **Agent Notes/Summary** (required): Call details and follow-up context
3. **Seller Motivation Level**: Prioritization indicator
4. **Next Action Date**: Callback scheduling
5. **Target Asking Price**: Pipeline value tracking

### **System Fields** (Auto-populated)
- Title: Auto-generated call reference
- Relationship: Links to Master Lead (field 274851864)
- Date of Call: Timestamp
- Call Duration: From Twilio API
- Recording URL: From Twilio API

### What Makes This System Compliant?

1. **Manual Click Required**: Every call requires an explicit manual action from the agent
2. **Two-Leg Architecture**: The system calls the agent first, then connects to the prospect
3. **No Auto-Dialing**: Avoids ATDS (Automated Telephone Dialing System) classification
4. **Complete Audit Trail**: Every call is logged to Firestore with full details
5. **Mandatory Dispositions**: All calls require documented outcomes

### V2.1 Feature Highlights (VOIP Architecture)
- 🌐 **Browser-Based VOIP Calling** - Agents use browser instead of phone
- 🚫 **No Carrier Blocking** - Eliminates "Busy" statuses from PSTN congestion
- 🔑 **Auto-Generated Identities** - System manages client:agent_xxxxx format
- 📞 **Twilio Voice SDK v2.11.1** - Self-hosted modern SDK architecture

### V3.1 Feature Highlights (Call Recording & Playback)
- 🎙️ **Automatic Call Recording** - All conversations recorded when prospect answers
- 📊 **Firestore Audit Trail** - Recording metadata (SID, URL, duration) linked to call logs
- 🔒 **Secure Proxy Playback** - Authentication-free recording access via `/play_recording/<sid>` endpoint
- 🎵 **Browser-Compatible** - Direct MP3 streaming without credential exposure
- 🔗 **Ready for Podio** - Infrastructure prepared for V3.2 automatic Podio updates

---

## ✨ Key Features

- ✅ **Browser-Based VOIP Calling** - Agents use browser instead of phone (V2.1)
- ✅ **No Carrier Blocking** - Eliminates "Busy" statuses from PSTN congestion
- ✅ **Auto-Generated Identities** - System manages client:agent_xxxxx format
- ✅ **Twilio Voice SDK v2.11.1** - Self-hosted modern SDK architecture
- ✅ Two-leg calling system (complies with TCPA regulations)
- ✅ Podio CRM integration (Master Lead & Call Activity apps)
- ✅ Real-time call disposition capture
- ✅ Firestore audit logging

### V3.3: Automated Task Creation (November 2024)
- **Smart Task Automation**: Automatically creates follow-up tasks based on call dispositions
- **Flexible Due Dates**: Agents can override default due dates with custom dates
- **Task Management**: Integrated Podio Tasks app with automated field configuration
- **Non-Blocking**: Task creation failures never prevent Call Activity from being saved

---

## 🏗️ Architecture

## V3.1 Architecture (VOIP + Call Recording)

### Call Flow
1. **Agent Workspace** - Browser-based interface with Twilio Voice SDK
2. **Leg 1 (VOIP)** - Twilio → Agent Browser (WebRTC, client:agent_xxxxx)
3. **Leg 2 (PSTN)** - Twilio → Prospect Phone (+1234567890)

### Why VOIP-Only?
V2.0 used PSTN for agent connections, causing carrier blocking due to high call volume from the same Twilio number. V2.1 eliminates this by using browser-based VOIP for the agent leg, preventing carrier spam detection while maintaining compliance for the prospect leg.

```
Podio Link Field → /workspace → Load Lead Data →
→ Agent UI (5-field form) → Initiate Call (VOIP) → Twilio →
→ Complete Call → Fill Disposition → Submit →
→ /submit_call_data → Direct Podio Write →
→ Call Activity Created → Firestore Audit →
→ Success Response to Agent
```

### Call Sequence (V2.1)

1. **Agent Initiates**: Clicks link field in Podio containing item ID
2. **Workspace Loads**: `/workspace` endpoint loads lead data and displays Agent UI
3. **VOIP Registration**: Twilio Voice SDK registers browser as client:agent_xxxxx
4. **Agent Reviews**: Agent sees lead name, phone, and address pre-loaded
5. **Call Initiation**: Agent clicks "Initiate Call" button (AJAX request)
6. **Agent Call (Leg 1)**: Twilio connects to agent's browser via WebRTC (VOIP)
7. **Prospect Connection (Leg 2)**: Upon agent answer, system bridges to prospect
8. **Call Completion**: Agent completes conversation
9. **Disposition Entry**: Agent fills mandatory 5-field disposition form
10. **Submit to Podio**: `/submit_call_data` creates Call Activity item with all fields
11. **Relationship Linking**: Call Activity automatically linked to Master Lead
12. **Firestore Logging**: Complete audit trail saved
13. **Success Feedback**: Agent receives confirmation, workspace remains open for next call

## 🚀 Quick Start

## Requirements

- Python 3.9+
- Twilio Account (Voice API)
- Podio Account with OAuth credentials
- Google Cloud Firestore (for audit logging)
- Vercel (for hosting)

## Installation

See deployment documentation in `/docs` folder.

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/compliant-real-estate-lead-dialer.git
   cd compliant-real-estate-lead-dialer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=+1234567890
   TWILIO_API_KEY=your_twilio_api_key
   TWILIO_API_SECRET=your_twilio_api_secret
   TWILIO_TWIML_APP_SID=your_twiml_app_sid
   GCP_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
   PODIO_CLIENT_ID=your_podio_client_id
   PODIO_CLIENT_SECRET=your_podio_client_secret
   PODIO_USERNAME=your_podio_username
   PODIO_PASSWORD=your_podio_password
   ```

4. **Run locally**
   ```bash
   python app.py
   ```
   
   The app will be available at `http://localhost:5000`

---

## ⚙️ Configuration

## Configuration

### Environment Variables (Vercel)

#### Twilio Configuration
- `TWILIO_ACCOUNT_SID` - Your Twilio account SID
- `TWILIO_AUTH_TOKEN` - Your Twilio auth token
- `TWILIO_PHONE_NUMBER` - Twilio phone number (E.164 format)
- `TWILIO_API_KEY` - **New in V2.1** - API Key for Access Tokens
- `TWILIO_API_SECRET` - **New in V2.1** - API Secret for Access Tokens
- `TWILIO_TWIML_APP_SID` - **New in V2.1** - TwiML Application SID

#### Podio Configuration
- `PODIO_CLIENT_ID`, `PODIO_CLIENT_SECRET`, `PODIO_USERNAME`, `PODIO_PASSWORD`
- `PODIO_MASTER_LEAD_APP_ID`, `PODIO_CALL_ACTIVITY_APP_ID`
- `PODIO_MASTER_LEAD_APP_TOKEN`, `PODIO_CALL_ACTIVITY_APP_TOKEN`

#### Google Cloud
- `GCP_SERVICE_ACCOUNT_JSON`

#### Removed in V2.1
- ~~`AGENT_PHONE_NUMBER`~~ - No longer used (VOIP-only architecture)

See [`docs/vercel_environment_variables.md`](docs/vercel_environment_variables.md) for complete setup guide.

## V1.0 → V2.0 Migration

- **Breaking Change**: Podio link field URL must be updated from `/dial` to `/workspace`
- **Data Impact**: None (V1.0 and V2.0 can coexist during transition)
- **Rollback**: Revert link field URL to restore V1.0 behavior

## Known Issues

- ~~**Intermittent Busy Status**~~: Fixed in V2.1 - VOIP architecture eliminates carrier blocking

### Vercel Configuration

All environment variables must be configured in your Vercel project settings:

1. Navigate to your project in Vercel Dashboard
2. Go to Settings → Environment Variables
3. Add all required variables listed above
4. Redeploy for changes to take effect

---

## 📱 Usage

### Setting Up Podio Integration

1. **Create a Link Field** in your Podio leads app:
   - Field Label: "Click to Dial" or "Call Lead"
   - Field Type: Link
   - URL Template: `https://your-vercel-app.vercel.app/dial?item_id=[item-id]`

2. **Ensure Phone Field Exists**:
   - Field Label: "Best Contact Number"
   - Field Type: Phone

3. **Click to Dial**:
   - Agent clicks the link field in any lead record
   - System automatically retrieves phone number
   - Agent's phone rings first
   - Upon answering, prospect is called
   - Call details logged to Firestore

### Manual Testing

Test the `/dial` endpoint directly:
```
https://your-app.vercel.app/dial?phone=+15551234567
```

Or test with Podio item ID:
```
https://your-app.vercel.app/dial?item_id=123456789
```

---

## 🔌 API Endpoints

### `GET /workspace`

Loads the agent workspace with pre-populated lead data.

**Parameters:**
- `item_id` (required): Podio Master Lead item ID

**Example:**
```
GET /workspace?item_id=123456789
```

**Response:** HTML workspace interface with lead information

---

### `GET /dial`

Initiates a TCPA-compliant two-leg call.

**Parameters:**
- `item_id` (optional): Podio item ID to fetch phone number from
- `phone` (optional): Direct phone number in E.164 format

**Example:**
```
GET /dial?item_id=123456789
```

**Response:** HTML page confirming call initiation

---

### `POST /connect_prospect`

Internal endpoint called by Twilio to connect agent to prospect.

**Parameters:**
- `prospect_number`: Phone number to dial (passed via query string)

**Returns:** TwiML instructions for connecting the call

---

### `POST /call_status`

Webhook endpoint for Twilio call status callbacks.

**Automatically logs to Firestore:**
- CallSid
- CallStatus
- Direction
- From/To numbers
- Server timestamp

---

### `POST /recording_status`

Twilio webhook for recording completion callbacks.

**Receives from Twilio:**
- RecordingSid
- RecordingUrl
- CallSid
- RecordingDuration

**Actions:**
- Updates Firestore call log with recording metadata
- Stores proxy URL for authentication-free playback

---

### `GET /play_recording/<recording_sid>`

Proxy endpoint for authentication-free call recording playback.

**Parameters:**
- `recording_sid` (required): Twilio Recording SID from URL path

**Example:**
```
GET /play_recording/RExxx
```

**Response:** MP3 audio stream with proper headers

**Security:**
- Server-side Twilio authentication
- No credentials exposed to browser
- Returns 404 if recording not found

---

## 📋 Task Automation (V3.3)

The system automatically creates follow-up tasks in Podio based on the agent's disposition selection:

### Default Task Rules
- **Voicemail** → Follow-up Call (2 days)
- **No Answer** → Follow-up Call (1 day)
- **Appointment Set** → Appointment (today)
- **Callback Scheduled** → Follow-up Call (1 day)

### Agent Override
Agents can override default due dates by filling in the "Next Action Date" field in the workspace. When specified, the agent's date takes priority over the default.

### Configuration
Task automation is configured in [`config.py`](config.py) via the `DISPOSITION_TASK_MAPPING` dictionary. Environment variables for the Task app are configured in Vercel.

---

## ✅ Compliance

### TCPA Compliance Features

1. **Manual Initiation**: Every call requires explicit agent action (clicking link)
2. **Two-Leg Architecture**: 
   - Leg 1: System calls agent first
   - Leg 2: Only after agent answers, prospect is called
3. **No Predictive/Auto-Dialing**: System never calls prospects without live agent
4. **Audit Trail**: Complete Firestore logging of all call activities
5. **Consent Tracking**: Can be extended to track consent status per lead

### Best Practices

- Only call leads during permitted hours (8am-9pm local time)
- Maintain internal Do Not Call (DNC) list
- Honor opt-out requests immediately
- Keep detailed records (provided by Firestore integration)
- Train agents on TCPA compliance requirements

---

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[Project Definition](docs/Project_Definition_Compliant_Real_Estate_Lead_Dialer.md)**: Complete system architecture and requirements
- **[Progress Report](docs/Project_Progress_Report_Compliant_Lead_Dialer.md)**: Development history and phase completion status
- **[Podio Link Field Setup Guide](docs/Podio_Link_Field_Setup_Guide.md)**: Step-by-step Podio integration instructions
- **[Twilio Credential Collection Plan](docs/Twilio_Credential_Collection_Plan_Playwright.md)**: Twilio account setup guide
- **[Podio Credential Collection Plan](docs/Podio_Credential_Collection_Plan_Playwright.md)**: Podio authentication setup

---

## 🚢 Production Deployment

### Current Status: **PRODUCTION READY** ✅

- **Version**: 1.0
- **Platform**: Vercel
- **Status**: Fully operational
- **Deployment Date**: November 19, 2024
- **URL**: [Your Production URL]

### Deployment Checklist ✓

- [x] All environment variables configured in Vercel
- [x] Twilio credentials verified and working
- [x] Firestore database initialized and accessible
- [x] Podio OAuth authentication configured
- [x] End-to-end testing completed successfully
- [x] Call logging verified in Firestore
- [x] Podio integration tested with live data
- [x] Error handling verified for all edge cases
- [x] Production URL confirmed accessible
- [x] Documentation completed and reviewed

### Deployment Command

```bash
vercel --prod
```

### Monitoring

- **Vercel Logs**: Real-time application logs via Vercel dashboard
- **Firestore Console**: View call logs at [Google Cloud Console](https://console.cloud.google.com/firestore)
- **Twilio Console**: Monitor call activity and usage

---

## 📊 Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

### v2.0 - Agent Workspace (November 20, 2025)

**Status**: Production Release 🎉

**Major Architectural Upgrade:**
- ✅ Agent Workspace UI with pre-loaded lead data
- ✅ Mandatory 5-field disposition system
- ✅ Direct Podio API integration (eliminates Make/Zapier)
- ✅ Bi-directional Call Activity relationships
- ✅ Real-time Podio writes with 10-field mapping
- ✅ Complete Firestore audit logging
- ✅ AJAX call initiation
- ✅ 8 critical bug fixes

### v1.0 - Initial Release (November 19, 2024)

**Status**: Superseded by V2.0

**Features:**
- ✅ TCPA-compliant two-leg dialing
- ✅ Basic Podio Link field integration
- ✅ Real-time Firestore call logging
- ✅ Auto-close window workflow
- ✅ External connector integration (Make/Zapier)

---

## 🤝 Contributing

This is a production system. For feature requests or bug reports, please create an issue in the repository.

---

## 📄 License

Copyright © 2024. All rights reserved.

---

## 🆘 Support

For technical support or questions:
- Review the [documentation](docs/)
- Check [Vercel logs](https://vercel.com/docs/concepts/observability/logs)
- Review [Firestore data](https://console.cloud.google.com/firestore)
- Contact your system administrator

---

## License

Proprietary - LeadGenAlchemy

## Support

For issues or questions, contact: c1tyv4ult@gmail.com

---

**Built with ❤️ for compliant, efficient real estate operations**