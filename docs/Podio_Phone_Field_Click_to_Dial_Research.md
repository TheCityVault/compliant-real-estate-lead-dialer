# Podio Phone Field Custom Action Research Report
## Option 2 Feasibility Assessment for Click-to-Dial Integration

---

## Executive Summary

**VERDICT: Option 2 (Phone Field Custom Action) is NOT VIABLE for this project.**

Podio phone fields support only standard telephony protocols (`tel:` and `callto:`), not HTTPS URLs or custom webhooks. This limitation makes it impossible to configure phone fields to trigger the Vercel API endpoint directly.

**Recommendation:** Pivot to **Option 1** (Link Field or App Widget approach).

---

## Research Findings

### 1. Podio Phone Field Built-in Functionality

#### Official Documentation
**Source:** [Podio Field Documentation](https://docs.sharefile.com/en-us/podio/using-podio/creating-apps/the-fields-in-app-templates.html)

> "Phone fields are used to store phone numbers. You may consider using this field in a contact app, or any other app where you want to store phone numbers. You can add multiple phone numbers to this field. Click the 'Call' button to the right of any phone number to call that number. **In order to start the call you will need to have software like Skype installed on your device that can execute the call.**"

**Key Points:**
- Phone fields have a built-in "Call" button
- Clicking the button requires compatible telephony software (Skype, Microsoft Teams, etc.)
- The field is designed for traditional telephony, not web APIs

---

### 2. Protocol Configuration Options

#### Available Protocols
**Source:** [Podio Field Documentation](https://docs.sharefile.com/en-us/podio/using-podio/creating-apps/the-fields-in-app-templates.html)

> "Depending on which software you use to make the call, a different protocol might be needed. **Skype for example operates with the default 'callto:' protocol, however most Microsoft software works with a 'tel:' protocol. You can change the protocol in the settings of the phone field.**"

**Supported Protocols:**
- `callto:` - Skype and similar VoIP applications
- `tel:` - Standard telephone protocol (RFC 3966)
- Reference: [RFC 3966 - tel URI specification](https://www.ietf.org/rfc/rfc3966.txt)

**NOT Supported:**
- ❌ `https://` or `http://` - Web URLs
- ❌ Custom protocols for webhooks or API calls
- ❌ JavaScript execution
- ❌ Custom action handlers

---

### 3. API Configuration Details

#### Phone Field Settings (from API Documentation)
**Source:** [Podio Applications API](https://developers.podio.com/doc/applications)

```json
{
  "type": "tel",
  "settings": {
    "strict": false,
    "display_format": "INT",
    "default_country_code": "US"
  }
}
```

**Available Settings:**
- `strict` (boolean) - Controls input validation and formatting
- `display_format` - Options: "INT", "NAT", "E164", "RFC3966"
- `default_country_code` - ISO country codes for phone number formatting

**No settings exist for:**
- Custom URL handlers
- Protocol override beyond `tel:` and `callto:`
- Webhook destinations
- API endpoints

---

### 4. Premium/Plus Feature Requirements

**Finding:** Phone field functionality is available in ALL Podio plans.

**No premium features required for:**
- Basic phone field creation
- Protocol configuration (`tel:` or `callto:`)
- Click-to-call button display

**Premium features (Globiflow) required for:**
- Automation workflows
- Webhook integrations via Globiflow (not directly from phone field)

---

### 5. Community Implementation Examples

#### Third-Party Solutions
Research revealed several community approaches, all requiring additional services:

##### A. smrtPhone Integration
**Source:** [Struggling Investor Tutorial](https://strugglinginvestor.com/2019/04/make-calls-and-send-texts-in-podio-using-smrtphone/)

**Approach:**
- Third-party service: smrtPhone ($50/mo base + usage costs)
- Chrome Extension required for click-to-call from Podio
- Creates separate Communications app for call logging
- Uses Globiflow for automation

**Cost Structure:**
- Base: $50/month
- Additional users: $5/month each
- Phone numbers: $5/month each
- SMS: $0.01113 per message
- Calls: $0.02 per minute

**Limitations:**
- Requires Chrome Extension installation
- Additional monthly costs
- Dependency on external service
- Not a native Podio solution

##### B. JustCall Integration
**Source:** [Podio Extensions - JustCall](https://podio.com/extensions/974)

Similar third-party service requiring:
- External subscription
- Chrome Extension
- Separate communication logging system

---

### 6. Technical Limitations & Constraints

#### Phone Field Architecture
1. **Hard-coded Protocol Handler**
   - Phone fields use the operating system's default handler for `tel:` or `callto:` URIs
   - No mechanism to intercept or redirect to custom URLs
   - Browser/OS security sandboxing prevents custom protocol handlers for phone fields

2. **No JavaScript Execution Context**
   - Phone field "Call" buttons don't support onclick handlers
   - Cannot inject custom JavaScript
   - No event hooks available in Podio API

3. **Field Type Restrictions**
   - Phone field type (`tel`) is strictly for telephony purposes
   - Cannot be repurposed for HTTP requests
   - Field validation enforces phone number format

#### Comparison with Calculation Field Findings
Previously discovered that calculation fields output **plain text only** and cannot render HTML/JavaScript. Phone fields have a similar limitation - they're purpose-built for a specific function (telephony) and cannot be repurposed for web API calls.

---

### 7. Alternative Approaches Considered

#### Option A: Link Field (Most Viable Alternative)
**Pros:**
- Can store custom HTTPS URLs
- Clickable in Podio interface
- No additional costs
- Available in all Podio plans

**Cons:**
- URL must be manually constructed or via Globiflow
- Less intuitive than "Call" button
- Requires calculation field to build dynamic URL with parameters

**Implementation:**
```markdown
Calculation Field Formula:
"https://your-vercel-app.vercel.app/dial?item_id=" + @Item ID + 
"&target_number=" + [Phone Number] + 
"&owner_name=" + [Owner Name]
```

#### Option B: App Widget
**Pros:**
- Custom UI possible
- Native Podio integration
- Can include branding

**Cons:**
- Requires developer portal access
- Complex development process
- Must be approved by Podio/Citrix
- Maintenance overhead

#### Option C: Browser Extension
**Pros:**
- Can intercept click events
- Add custom buttons to Podio interface
- Full control over behavior

**Cons:**
- Must be installed on every user's browser
- Maintenance required for Podio UI changes
- Security/permission concerns
- Distribution challenges

---

## Feasibility Assessment Matrix

| Criterion | Phone Field Option | Link Field Option | App Widget Option |
|-----------|-------------------|-------------------|-------------------|
| **Protocol Support** | ❌ `tel:`/`callto:` only | ✅ HTTPS supported | ✅ Custom actions |
| **Development Effort** | N/A - Not viable | ⭐ Low | ⭐⭐⭐ High |
| **Cost** | $0 | $0 | $0 (dev time) |
| **User Experience** | ⭐⭐⭐⭐⭐ Natural | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Very Good |
| **Maintenance** | ⭐⭐⭐⭐⭐ None | ⭐⭐⭐⭐⭐ None | ⭐⭐ Ongoing |
| **Deployment Speed** | N/A | ⭐⭐⭐⭐⭐ Immediate | ⭐ Weeks |
| **Reliability** | N/A | ⭐⭐⭐⭐⭐ High | ⭐⭐⭐ Medium |

---

## Official Documentation Links

1. **Podio Field Types:** [https://docs.sharefile.com/en-us/podio/using-podio/creating-apps/the-fields-in-app-templates.html](https://docs.sharefile.com/en-us/podio/using-podio/creating-apps/the-fields-in-app-templates.html)

2. **Podio Applications API:** [https://developers.podio.com/doc/applications](https://developers.podio.com/doc/applications)

3. **RFC 3966 (tel: URI):** [https://www.ietf.org/rfc/rfc3966.txt](https://www.ietf.org/rfc/rfc3966.txt)

4. **Podio Webhooks:** [https://developers.podio.com/doc/hooks](https://developers.podio.com/doc/hooks)

---

## Final Recommendation

### ❌ DO NOT PROCEED with Option 2 (Phone Field Custom Action)

**Reasons:**
1. Phone fields only support telephony protocols (`tel:`, `callto:`)
2. No mechanism to configure HTTPS URLs or custom webhooks
3. Cannot intercept or modify click behavior
4. Architectural limitation, not a configuration issue

### ✅ RECOMMENDED: Pivot to Option 1 (Link Field Implementation)

**Implementation Plan:**
1. Create a **Link field** in the Master Lead app
2. Create a **Calculation field** to dynamically generate the Vercel API URL with required parameters
3. Set the Link field value using the Calculation field output (or via Globiflow automation)
4. Users click the link to initiate the call

**Benefits:**
- Zero additional cost
- Immediate implementation
- Fully under your control
- No third-party dependencies
- Works with existing Vercel infrastructure

**Sample Implementation:**
```
Field Name: "Click to Dial"
Field Type: Link
Value Source: Calculation Field

Calculation Formula:
"https://your-vercel-app.vercel.app/dial"
+ "?item_id=" + @Item ID
+ "&target_number=" + [Best Contact Number]
+ "&owner_name=" + [Owner Name]
```

---

## Next Steps

1. ✅ **Accept findings** that Option 2 is not viable
2. ✅ **Proceed with Option 1** implementation using Link field
3. Create detailed implementation guide for Link field approach
4. Test end-to-end workflow with Link field integration
5. Document user instructions for clicking the dial link

---

## Appendix: Phone Field Configuration Screenshot Locations

While phone field protocol settings can be modified, they are limited to telephony protocols only:

- **Field Settings Location:** App Configuration → Field Settings → Phone Field → Protocol dropdown
- **Available Options:**
  - `callto:` (Skype/VoIP)
  - `tel:` (Standard telephone)
- **Not Available:** Custom HTTPS URLs or webhook endpoints

---

**Document Version:** 1.0  
**Date:** 2025-01-19  
**Research Status:** Complete  
**Recommendation:** Pivot to Option 1 (Link Field)