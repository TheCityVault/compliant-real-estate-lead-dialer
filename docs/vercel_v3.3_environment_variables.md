# Vercel Environment Variables - V3.3 Task Automation

## Required Environment Variables for V3.3

The following **6 new environment variables** must be added to Vercel for V3.3 Task Automation to function in production:

```
PODIO_TASK_APP_ID=30559290
TASK_TITLE_FIELD_ID=274877609
TASK_TYPE_FIELD_ID=274877610
TASK_DUE_DATE_FIELD_ID=274877611
TASK_MASTER_LEAD_RELATIONSHIP_FIELD_ID=274877612
TASK_STATUS_FIELD_ID=274877613
```

## Step-by-Step: Adding Variables to Vercel Dashboard

### 1. Access Your Project
1. Go to https://vercel.com/dashboard
2. Click on your project: **Compliant Real Estate Lead Dialer**
3. Navigate to **Settings** → **Environment Variables**

### 2. Add Each Variable
For **each** of the 6 variables listed above:

1. Click **Add New** button
2. **Name**: Enter the variable name (e.g., `PODIO_TASK_APP_ID`)
3. **Value**: Enter the corresponding value (e.g., `30559290`)
4. **Environment**: Select **ALL THREE**:
   - ✅ Production
   - ✅ Preview
   - ✅ Development
5. Click **Save**

### 3. Repeat for All Variables
Add all 6 variables:
- ✅ PODIO_TASK_APP_ID = `30559290`
- ✅ TASK_TITLE_FIELD_ID = `274877609`
- ✅ TASK_TYPE_FIELD_ID = `274877610`
- ✅ TASK_DUE_DATE_FIELD_ID = `274877611`
- ✅ TASK_MASTER_LEAD_RELATIONSHIP_FIELD_ID = `274877612`
- ✅ TASK_STATUS_FIELD_ID = `274877613`

## Step-by-Step: Using Vercel CLI (Alternative)

If you prefer using the command line:

```bash
# Set variables for Production environment
vercel env add PODIO_TASK_APP_ID production
# When prompted, enter: 30559290

vercel env add TASK_TITLE_FIELD_ID production
# When prompted, enter: 274877609

vercel env add TASK_TYPE_FIELD_ID production
# When prompted, enter: 274877610

vercel env add TASK_DUE_DATE_FIELD_ID production
# When prompted, enter: 274877611

vercel env add TASK_MASTER_LEAD_RELATIONSHIP_FIELD_ID production
# When prompted, enter: 274877612

vercel env add TASK_STATUS_FIELD_ID production
# When prompted, enter: 274877613
```

**Repeat for Preview and Development environments if needed.**

## Deployment After Adding Variables

**CRITICAL**: After adding environment variables, you **MUST** trigger a new deployment for the changes to take effect.

### Option A: Automatic Deployment (if Git integration enabled)
```bash
git add .
git commit -m "feat(V3.3): Add Task App environment configuration"
git push origin feature/task-automation
```

### Option B: Manual Deployment via Vercel CLI
```bash
vercel --prod
```

### Option C: Vercel Dashboard
1. Go to **Deployments** tab
2. Click **Redeploy** on the latest deployment
3. Select **Use existing Build Cache** (optional for faster deployment)
4. Click **Redeploy**

## Verification

### 1. Check Deployment Logs
After deployment completes:
1. Go to your deployment in Vercel
2. Click on the **Functions** tab
3. View the function logs for any startup errors

### 2. Test Task Creation
1. Access the Agent Workspace
2. Make a test call
3. Select disposition: "Left Voicemail"
4. Submit call data
5. Check Podio Tasks app for new task item linked to Master Lead

### 3. Expected Logs (Success)
```
V3.3: Disposition 'Left Voicemail' triggers task creation
=== V3.3: CREATE FOLLOW-UP TASK ===
Master Lead ID: [LEAD_ID]
Task Title: Follow up on voicemail
Task Type: Follow-up Call
Due Date: [DATE] (offset: 2 days)
✅ V3.3: Task created successfully - Item ID: [TASK_ID]
```

## Troubleshooting

### Environment Variables Not Loading
**Symptom**: Logs show `TASK_APP_ID_HERE` or similar placeholder values

**Solution**:
1. Verify variables are added to **Production** environment
2. Trigger a **new deployment** (environment variables only load on deployment)
3. Check for typos in variable names (case-sensitive)

### Task Creation Fails with "App Not Found"
**Symptom**: `❌ V3.3: Task creation failed - Status: 404`

**Solution**:
1. Verify `PODIO_TASK_APP_ID=30559290` is correctly set
2. Confirm Task app exists in Podio workspace
3. Check Podio credentials are valid

### Task Creation Fails with "Field Not Found"
**Symptom**: `❌ V3.3: Task creation failed - Status: 400 - Invalid field ID`

**Solution**:
1. Verify all TASK_*_FIELD_ID variables are correctly set
2. Run `python scripts/create_task_app.py` to regenerate field IDs if needed
3. Update Vercel environment variables with new IDs

## Complete Environment Variable Checklist

Before deploying V3.3 to production, ensure **ALL** these variables are configured:

### Core Credentials (Existing)
- ✅ TWILIO_ACCOUNT_SID
- ✅ TWILIO_AUTH_TOKEN
- ✅ PODIO_CLIENT_ID
- ✅ PODIO_CLIENT_SECRET
- ✅ PODIO_USERNAME
- ✅ PODIO_PASSWORD

### App IDs (Existing)
- ✅ PODIO_CALL_ACTIVITY_APP_ID
- ✅ PODIO_MASTER_LEAD_APP_ID

### V3.3 Task App (NEW - Must Add)
- ☐ PODIO_TASK_APP_ID
- ☐ TASK_TITLE_FIELD_ID
- ☐ TASK_TYPE_FIELD_ID
- ☐ TASK_DUE_DATE_FIELD_ID
- ☐ TASK_MASTER_LEAD_RELATIONSHIP_FIELD_ID
- ☐ TASK_STATUS_FIELD_ID

## Next Steps After Configuration

1. ✅ Add all 6 V3.3 environment variables to Vercel
2. ✅ Trigger new deployment
3. 🧪 Test task creation with "Left Voicemail" disposition
4. 🧪 Verify task appears in Podio Tasks app
5. 🧪 Verify task is linked to correct Master Lead
6. 🧪 Verify task due date is 2 days from creation
7. ✅ Mark V3.3 as production-ready

---

**Last Updated**: November 23, 2024
**Version**: V3.3 - Task Automation
**Task App ID**: 30559290