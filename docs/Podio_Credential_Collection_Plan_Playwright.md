# Podio Credential Collection Plan for Playwright Agent

This document outlines the steps for a Playwright agent to collect the necessary Podio credentials: `PODIO_CLIENT_ID` and `PODIO_CLIENT_SECRET`. These credentials are essential for Phase 2 synchronization.

## Phase 0: Credential Collection - Podio (Playwright Agent)

### Goal
To programmatically obtain `PODIO_CLIENT_ID` and `PODIO_CLIENT_SECRET` using a Playwright agent for secure integration with the Podio API.

### Prerequisites
*   A Podio account with administrative access.
*   Playwright environment set up and configured.

### Steps for Playwright Agent

1.  **Launch Browser and Navigate to Podio Developer Portal**
    *   **Action:** Launch a new browser instance.
    *   **Action:** Navigate to the Podio Developer website.
    *   **URL:** `https://developers.podio.com/`

2.  **Log in to Podio**
    *   **Action:** Identify the login form elements (username/email and password fields, and the login button).
    *   **Selector (Username/Email):** `input[name="email"]` or similar (inspect element for exact selector)
    *   **Selector (Password):** `input[name="password"]` or similar
    *   **Selector (Login Button):** `button[type="submit"]` or similar
    *   **Action:** Type the Podio username/email into the email field.
    *   **Action:** Type the Podio password into the password field.
    *   **Action:** Click the login button.
    *   **Note:** The agent will need to be provided with the Podio username/email and password securely (e.g., via environment variables).

3.  **Navigate to "Get an API Key" / "Register new app"**
    *   **Action:** After successful login, identify the link or button to register a new API application.
    *   **Selector:** `a[href="/api-key"]` or `button:has-text("Register new app")` or similar.
    *   **Action:** Click on the identified element.

4.  **Fill in Application Details**
    *   **Action:** Identify the input fields for the new application registration.
    *   **Selector (Application Name):** `input[name="app_name"]` or similar
    *   **Selector (Description):** `textarea[name="description"]` or similar
    *   **Selector (Full Domain):** `input[name="url"]` or similar
    *   **Selector (Callback URL):** `input[name="callback_url"]` or similar
    *   **Action:** Type "Compliant Real Estate Lead Dialer Integration" into the Application Name field.
    *   **Action:** Type a brief description (e.g., "Integration for compliant lead dialing system") into the Description field.
    *   **Action:** Type the appropriate full domain (e.g., `http://localhost:3000` for development) into the Full Domain field.
    *   **Action:** Type the appropriate callback URL (e.g., `http://localhost:3000/auth/podio/callback`) into the Callback URL field.
    *   **Action:** Identify and click the "Create App" or "Register" button.
    *   **Selector (Create App Button):** `button[type="submit"]` or similar.

5.  **Extract `PODIO_CLIENT_ID` and `PODIO_CLIENT_SECRET`**
    *   **Action:** After successful registration, the page should display the `Client ID` and `Client Secret`.
    *   **Selector (Client ID):** Identify the element containing the Client ID (e.g., `span#client-id`, `code.client-id`, or an input field).
    *   **Selector (Client Secret):** Identify the element containing the Client Secret (e.g., `span#client-secret`, `code.client-secret`, or an input field).
    *   **Action:** Use Playwright's `evaluate` function to extract the text content of these elements.
    *   **Example Playwright `evaluate` script:**
        ```javascript
        const clientId = await page.$eval('YOUR_CLIENT_ID_SELECTOR', el => el.textContent);
        const clientSecret = await page.$eval('YOUR_CLIENT_SECRET_SELECTOR', el => el.textContent);
        ```

6.  **Securely Store the Credentials**
    *   **Action:** The extracted `PODIO_CLIENT_ID` and `PODIO_CLIENT_SECRET` should be returned by the Playwright script.
    *   **Action:** The calling process (e.g., the orchestrator agent) will then be responsible for securely storing these credentials (e.g., in environment variables or a secret management system).

### Example Playwright Flow (Conceptual)

```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // 1. Navigate to Podio Developer Portal
  await page.goto('https://developers.podio.com/');

  // 2. Log in to Podio (replace with actual selectors and credentials)
  await page.fill('input[name="email"]', process.env.PODIO_USERNAME);
  await page.fill('input[name="password"]', process.env.PODIO_PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForNavigation(); // Wait for login to complete

  // 3. Navigate to "Register new app" (replace with actual selector)
  await page.click('a[href="/api-key"]'); // Or similar selector
  await page.waitForNavigation();

  // 4. Fill in Application Details (replace with actual selectors)
  await page.fill('input[name="app_name"]', 'Compliant Real Estate Lead Dialer Integration');
  await page.fill('textarea[name="description"]', 'Integration for compliant lead dialing system');
  await page.fill('input[name="url"]', 'http://localhost:3000');
  await page.fill('input[name="callback_url"]', 'http://localhost:3000/auth/podio/callback');
  await page.click('button[type="submit"]'); // Or similar selector for "Create App"
  await page.waitForNavigation();

  // 5. Extract PODIO_CLIENT_ID and PODIO_CLIENT_SECRET (replace with actual selectors)
  const podioClientId = await page.$eval('YOUR_CLIENT_ID_SELECTOR', el => el.textContent);
  const podioClientSecret = await page.$eval('YOUR_CLIENT_SECRET_SELECTOR', el => el.textContent);

  console.log('PODIO_CLIENT_ID:', podioClientId);
  console.log('PODIO_CLIENT_SECRET:', podioClientSecret);

  await browser.close();
})();