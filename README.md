# Compliant Real Estate Lead Dialer

[![Production Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](https://github.com/yourusername/compliant-real-estate-lead-dialer)
[![Version](https://img.shields.io/badge/Version-1.0-blue)](https://github.com/yourusername/compliant-real-estate-lead-dialer/releases)
[![Platform](https://img.shields.io/badge/Platform-Vercel-black)](https://vercel.com)
[![TCPA Compliant](https://img.shields.io/badge/TCPA-Compliant-success)](https://www.fcc.gov/tcpa)

**🎉 Production Ready - Version 1.0**

A TCPA-compliant, two-leg click-to-dial system for real estate professionals that seamlessly integrates Podio CRM, Twilio telephony, and Google Cloud Firestore for comprehensive call logging and audit trails.

**🌐 Production Deployment:** [Your Vercel URL]

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

The Compliant Real Estate Lead Dialer enables real estate agents to initiate phone calls directly from Podio lead records with a single click, while maintaining strict TCPA (Telephone Consumer Protection Act) compliance through a two-leg dialing architecture.

### What Makes This System Compliant?

1. **Manual Click Required**: Every call requires an explicit manual action from the agent
2. **Two-Leg Architecture**: The system calls the agent first, then connects to the prospect
3. **No Auto-Dialing**: Avoids ATDS (Automated Telephone Dialing System) classification
4. **Complete Audit Trail**: Every call is logged to Firestore with full details

---

## ✨ Key Features

### Core Functionality
- **🔐 TCPA-Compliant Architecture**: Two-leg dialing ensures regulatory compliance
- **📞 Seamless Podio Integration**: Click-to-dial directly from lead records via Link fields
- **🔥 Real-time Firestore Logging**: Immediate audit trail for every call
- **📊 Comprehensive Call Data**: Captures CallSid, status, duration, timestamps, and participant numbers
- **🚀 Serverless Deployment**: Runs on Vercel for scalability and reliability

### Technical Highlights
- **Flask/Python Backend**: Robust server-side processing
- **Twilio SDK Integration**: Professional telephony capabilities
- **Google Cloud Firestore**: Scalable, real-time database
- **Environment-Based Configuration**: Secure credential management
- **Error Handling**: Comprehensive error messages and graceful degradation

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Podio CRM      │
│  (Link Field)   │
└────────┬────────┘
         │ 1. Agent clicks link
         │    with item_id parameter
         ▼
┌─────────────────────────────────┐
│  Vercel (Flask/Python)          │
│  ┌───────────────────────────┐  │
│  │ GET /dial?item_id=xxx     │  │
│  │ - Fetches Podio item      │  │
│  │ - Extracts phone number   │  │
│  │ - Initiates Twilio call   │  │
│  └───────────┬───────────────┘  │
│              │                  │
│  ┌───────────▼───────────────┐  │
│  │ POST /connect_prospect    │  │
│  │ - Connects agent to       │  │
│  │   prospect (Leg 2)        │  │
│  └───────────┬───────────────┘  │
│              │                  │
│  ┌───────────▼───────────────┐  │
│  │ POST /call_status         │  │
│  │ - Logs call details to    │  │
│  │   Firestore               │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Twilio         │
│  - Calls agent  │ (Leg 1)
│  - Connects to  │ (Leg 2)
│    prospect     │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Google Cloud   │
│  Firestore      │
│  (Audit Trail)  │
└─────────────────┘
```

### Call Sequence

1. **Agent Initiates**: Clicks link field in Podio containing item ID
2. **Item Retrieval**: System fetches lead details from Podio API
3. **Phone Extraction**: Retrieves "Best Contact Number" from Podio item
4. **Agent Call (Leg 1)**: Twilio calls the agent's phone
5. **Prospect Connection (Leg 2)**: Upon agent answer, system bridges to prospect
6. **Call Logging**: All call details logged to Firestore in real-time
7. **Future Sync**: Firestore data can be synced back to Podio via Make/Zapier (Phase 2)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Twilio account with phone number
- Google Cloud project with Firestore enabled
- Podio workspace and app
- Vercel account (for deployment)

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
   AGENT_PHONE_NUMBER=+1234567890
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

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TWILIO_ACCOUNT_SID` | Twilio account identifier | `ACxxxxxxxxxxxxx` |
| `TWILIO_AUTH_TOKEN` | Twilio authentication token | `your_auth_token` |
| `TWILIO_PHONE_NUMBER` | Twilio phone number (E.164 format) | `+15551234567` |
| `AGENT_PHONE_NUMBER` | Agent's phone number (E.164 format) | `+15559876543` |
| `GCP_SERVICE_ACCOUNT_JSON` | Google Cloud service account JSON (stringified) | `{"type":"service_account",...}` |
| `PODIO_CLIENT_ID` | Podio OAuth client ID | `your_client_id` |
| `PODIO_CLIENT_SECRET` | Podio OAuth client secret | `your_client_secret` |
| `PODIO_USERNAME` | Podio account username/email | `agent@example.com` |
| `PODIO_PASSWORD` | Podio account password | `your_password` |

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

### v1.0 - Production Ready (November 19, 2024)

**Status**: Production Release 🎉

This is the first production-ready release with full TCPA compliance, Podio integration, and Firestore audit logging.

**Features:**
- ✅ TCPA-compliant two-leg dialing
- ✅ Seamless Podio Link field integration
- ✅ Real-time Firestore call logging
- ✅ Podio API integration for retrieving lead phone numbers
- ✅ Comprehensive error handling
- ✅ Production deployment on Vercel
- ✅ Full documentation suite

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

## 🎯 Roadmap

### Phase 2 (Future Enhancement)
- [ ] Implement Make.com/Zapier automation for Podio call log sync
- [ ] Add call recording capabilities
- [ ] Implement call analytics dashboard
- [ ] Add multi-agent support
- [ ] Enhanced error notifications

---

**Built with ❤️ for compliant, efficient real estate operations**