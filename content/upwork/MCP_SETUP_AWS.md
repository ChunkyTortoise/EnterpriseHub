# Upwork MCP Setup with AWS Secrets Manager

**Status**: ❌ Not Recommended - Use manual search instead (see UPWORK_WORKFLOW.md)

**Complexity**: HIGH - Requires AWS account, Secrets Manager setup, OAuth flow

**Value**: LOW - MCP tool only provides search interface, not proposals

---

## Why This Is Over-Engineering

The `@chinchillaenterprises/mcp-upwork` package requires:
1. AWS account (if you don't already have one)
2. AWS Secrets Manager configuration
3. IAM permissions setup
4. Upwork OAuth application creation
5. Manual OAuth token retrieval
6. Storing tokens in AWS Secrets Manager

**All of this just to automate keyword search.**

**Alternative**: Use the simple tracker script + manual Upwork search = 2 minutes vs 2 hours of AWS setup.

---

## If You Still Want to Set It Up

### Prerequisites

1. **AWS Account** with:
   - Access Key ID
   - Secret Access Key
   - Region configured (e.g., `us-west-1`)

2. **Upwork API Credentials**:
   - Create an API app at https://www.upwork.com/services/api/keys
   - Get Client ID and Client Secret
   - Complete OAuth flow to get access/refresh tokens

3. **IAM Permissions**:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "secretsmanager:GetSecretValue",
           "secretsmanager:PutSecretValue"
         ],
         "Resource": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:upwork/oauth-*"
       }
     ]
   }
   ```

### Step 1: Configure AWS Credentials

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_REGION="us-west-1"
```

Reload:
```bash
source ~/.zshrc
```

### Step 2: Create Upwork API Application

1. Go to https://www.upwork.com/services/api/keys
2. Click "Create a New API Key"
3. Fill in:
   - **Name**: "Claude MCP Upwork"
   - **Type**: Desktop Application
   - **Callback URL**: `http://localhost:8080/callback` (or any local URL)
4. Save **Client ID** and **Client Secret**

### Step 3: Get OAuth Tokens

You'll need to complete the OAuth flow manually. The MCP server doesn't provide a built-in OAuth handler, so you'll need to:

1. Use a tool like Postman or write a script to:
   - Request authorization: `https://www.upwork.com/ab/account-security/oauth2/authorize`
   - Exchange code for tokens
   - Get `access_token`, `refresh_token`, `expires_in`, `token_type`

2. Or use the Upwork Python SDK:
   ```python
   from upwork import Client
   # Follow OAuth flow
   # Get tokens
   ```

### Step 4: Store Tokens in AWS Secrets Manager

```bash
aws secretsmanager create-secret \
    --name upwork/oauth \
    --secret-string '{
      "access_token": "YOUR_ACCESS_TOKEN",
      "refresh_token": "YOUR_REFRESH_TOKEN",
      "expires_in": 86400,
      "token_type": "Bearer",
      "obtained_at": 1739577600
    }' \
    --region us-west-1
```

### Step 5: Update .mcp.json

```json
{
  "mcpServers": {
    "upwork": {
      "command": "npx",
      "args": ["-y", "@chinchillaenterprises/mcp-upwork@latest"],
      "env": {
        "AWS_ACCESS_KEY_ID": "${AWS_ACCESS_KEY_ID}",
        "AWS_SECRET_ACCESS_KEY": "${AWS_SECRET_ACCESS_KEY}",
        "AWS_REGION": "${AWS_REGION}",
        "UPWORK_OAUTH_SECRET_NAME": "upwork/oauth"
      }
    }
  }
}
```

### Step 6: Restart Claude Code

Close and reopen Claude Code for the MCP server to reload with new config.

### Step 7: Test

```bash
# In Claude Code conversation:
"Search Upwork for RAG engineering jobs"
```

If it works, you'll see job listings. If not, check:
- AWS credentials are valid
- Secret exists in Secrets Manager
- IAM permissions are correct
- Tokens haven't expired

---

## Maintenance

- **Token refresh**: The MCP server should auto-refresh, but monitor for expiration
- **AWS costs**: Secrets Manager costs ~$0.40/month per secret + API calls
- **Security**: Rotate AWS keys every 90 days
- **Upwork API limits**: Be aware of rate limits

---

## Why You Probably Shouldn't Do This

**Time investment**: 2-4 hours initial setup + ongoing maintenance

**What you get**: Automated keyword search (you can do this manually in 2 minutes)

**What you DON'T get**:
- ❌ Automatic proposal generation
- ❌ Automatic proposal submission
- ❌ Job quality filtering
- ❌ Client vetting
- ❌ Rate negotiation

**Better use of 2-4 hours**:
- ✅ Submit 10+ proposals manually
- ✅ Update your Upwork profile
- ✅ Record video intro
- ✅ Research high-value clients
- ✅ Optimize proposal templates

---

## Recommendation

**Skip the MCP setup.** Use the manual workflow in `UPWORK_WORKFLOW.md` instead.

If you REALLY want automation, consider:
1. Building a simple web scraper for Upwork RSS feeds
2. Using Upwork's free email alerts
3. Checking Upwork 2x daily as part of your routine

All of these are simpler than AWS Secrets Manager + OAuth flows.

---

**Last Updated**: 2026-02-15
**Status**: Documentation only - not implemented
