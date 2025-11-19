# Twilio Credential Collection Plan using Playwright MCP

This document outlines the steps required to gather the necessary Twilio credentials (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_PHONE_NUMBER`) using the Playwright MCP.

## Prerequisites

*   An active Twilio account with login credentials.
*   Playwright MCP server running and accessible.

## Steps to Gather Twilio Credentials via Playwright MCP

### Step 1: Navigate to Twilio Console Login Page

Use the `browser_navigate` tool to go to the Twilio Console login page.

```xml
<use_mcp_tool>
<server_name>playwright</server_name>
<tool_name>browser_navigate</tool_name>
<arguments>
{
  "url": "https://www.twilio.com/console"
}
</arguments>
</use_mcp_tool>
```

### Step 2: Log in to your Twilio Account

After navigating to the login page, you'll need to fill in the username and password fields and click the login button. This will require inspecting the page using `browser_snapshot` to get the selectors for the input fields and the login button.

1.  **Take a snapshot to identify elements:**
    ```xml
    <use_mcp_tool>
    <server_name>playwright</server_name>
    <tool_name>browser_snapshot</tool_name>
    <arguments>{}</arguments>
    </use_mcp_tool>
    ```
    *   *Analyze the snapshot to find the `ref` and `element` for username, password, and login button.*

2.  **Fill in username and password:**
    ```xml
    <use_mcp_tool>
    <server_name>playwright</server_name>
    <tool_name>browser_fill_form</tool_name>
    <arguments>
    {
      "fields": [
        {
          "name": "Email or Username",
          "type": "textbox",
          "ref": "YOUR_USERNAME_FIELD_REF",
          "value": "YOUR_TWILIO_USERNAME"
        },
        {
          "name": "Password",
          "type": "textbox",
          "ref": "YOUR_PASSWORD_FIELD_REF",
          "value": "YOUR_TWILIO_PASSWORD"
        }
      ]
    }
    </arguments>
    </use_mcp_tool>
    ```

3.  **Click the login button:**
    ```xml
    <use_mcp_tool>
    <server_name>playwright</server_name>
    <tool_name>browser_click</tool_name>
    <arguments>
    {
      "element": "Login button",
      "ref": "YOUR_LOGIN_BUTTON_REF"
    }
    </arguments>
    </use_mcp_tool>
    ```

### Step 3: Locate your Account SID and Auth Token

Once logged in, you will be on the Twilio Console Dashboard.

1.  **Take a snapshot to identify elements:**
    ```xml
    <use_mcp_tool>
    <server_name>playwright</server_name>
    <tool_name>browser_snapshot</tool_name>
    <arguments>{}</arguments>
    </use_mcp_tool>
    ```
    *   *Analyze the snapshot to find the `ref` and `element` for Account SID and Auth Token. You may need to click a "show" button for the Auth Token.*

2.  **If Auth Token is masked, click "Show":**
    ```xml
    <use_mcp_tool>
    <server_name>playwright</server_name>
    <tool_name>browser_click</tool_name>
    <arguments>
    {
      "element": "Show Auth Token button",
      "ref": "YOUR_SHOW_AUTH_TOKEN_BUTTON_REF"
    }
    </arguments>
    </use_mcp_tool>
    ```

3.  **Extract Account SID and Auth Token:**
    ```xml
    <use_mcp_tool>
    <server_name>playwright</server_name>
    <tool_name>browser_evaluate</tool_name>
    <arguments>
    {
      "function": "() => {
        const accountSid = document.querySelector('YOUR_ACCOUNT_SID_SELECTOR').innerText;
        const authToken = document.querySelector('YOUR_AUTH_TOKEN_SELECTOR').innerText;
        return { accountSid, authToken };
      }"
    }
    </arguments>
    </use_mcp_tool>
    ```
    *   *Replace `YOUR_ACCOUNT_SID_SELECTOR` and `YOUR_AUTH_TOKEN_SELECTOR` with the actual CSS selectors obtained from the snapshot.*

### Step 4: Obtain a Twilio Phone Number

If you already have a Twilio Phone Number, you can skip to step 4.5.

1.  **Navigate to Phone Numbers section:**
    ```xml
    <use_mcp_tool>
    <server_name>playwright</server_name>
    <tool_name>browser_click</tool_name>
    <arguments>
    {
      "element": "Phone Numbers link in navigation",
      "ref": "YOUR_PHONE_NUMBERS_NAV_LINK_REF"
    }
    </arguments>
    </use_mcp_tool>
    ```
    Then, navigate to "Manage" and "Buy a number" if necessary, using `browser_click` and `browser_snapshot` to identify the correct elements.

2.  **Search for a Number:**
    *   **Take a snapshot to identify elements:**
        ```xml
        <use_mcp_tool>
        <server_name>playwright</server_name>
        <tool_name>browser_snapshot</tool_name>
        <arguments>{}</arguments>
        </use_mcp_tool>
        ```
        *   *Analyze the snapshot to find the `ref` and `element` for country, capabilities filters, and search button.*

    *   **Fill in search criteria (example: country and SMS capability):**
        ```xml
        <use_mcp_tool>
        <server_name>playwright</server_name>
        <tool_name>browser_fill_form</tool_name>
        <arguments>
        {
          "fields": [
            {
              "name": "Country dropdown",
              "type": "combobox",
              "ref": "YOUR_COUNTRY_DROPDOWN_REF",
              "value": "United States"
            },
            {
              "name": "SMS checkbox",
              "type": "checkbox",
              "ref": "YOUR_SMS_CHECKBOX_REF",
              "value": "true"
            }
          ]
        }
        </arguments>
        </use_mcp_tool>
        ```

    *   **Click "Search":**
        ```xml
        <use_mcp_tool>
        <server_name>playwright</server_name>
        <tool_name>browser_click</tool_name>
        <arguments>
        {
          "element": "Search button",
          "ref": "YOUR_SEARCH_BUTTON_REF"
        }
        </arguments>
        </use_mcp_tool>
        ```

3.  **Choose and Buy a Number:**
    *   **Take a snapshot to identify elements:**
        ```xml
        <use_mcp_tool>
        <server_name>playwright</server_name>
        <tool_name>browser_snapshot</tool_name>
        <arguments>{}</arguments>
        </use_mcp_tool>
        ```
        *   *Analyze the snapshot to find the `ref` and `element` for the "Buy" button next to a desired number.*

    *   **Click "Buy" for a chosen number:**
        ```xml
        <use_mcp_tool>
        <server_name>playwright</server_name>
        <tool_name>browser_click</tool_name>
        <arguments>
        {
          "element": "Buy button for chosen number",
          "ref": "YOUR_BUY_NUMBER_BUTTON_REF"
        }
        </arguments>
        </use_mcp_tool>
        ```

    *   **Handle confirmation dialog (if any):**
        ```xml
        <use_mcp_tool>
        <server_name>playwright</server_name>
        <tool_name>browser_handle_dialog</tool_name>
        <arguments>
        {
          "accept": true
        }
        </arguments>
        </use_mcp_tool>
        ```

4.  **Record your Twilio Phone Number:**
    *   Navigate to `Phone Numbers` -> `Manage` -> `Active numbers` (using `browser_click` and `browser_snapshot`).
    *   **Extract the phone number:**
        ```xml
        <use_mcp_tool>
        <server_name>playwright</server_name>
        <tool_name>browser_evaluate</tool_name>
        <arguments>
        {
          "function": "() => {
            const phoneNumber = document.querySelector('YOUR_ACTIVE_PHONE_NUMBER_SELECTOR').innerText;
            return phoneNumber;
          }"
        }
        </arguments>
        </use_mcp_tool>
        ```
        *   *Replace `YOUR_ACTIVE_PHONE_NUMBER_SELECTOR` with the actual CSS selector obtained from the snapshot.*

### Step 5: Close the browser

```xml
<use_mcp_tool>
<server_name>playwright</server_name>
<tool_name>browser_close</tool_name>
<arguments>{}</arguments>
</use_mcp_tool>
```

## Summary of Credentials to Collect

The Playwright MCP will be used to programmatically extract:

*   `TWILIO_ACCOUNT_SID`
*   `TWILIO_AUTH_TOKEN`
*   `TWILIO_PHONE_NUMBER` (in E.164 format, e.g., +1234567890)

These credentials will then be available for use in the application.