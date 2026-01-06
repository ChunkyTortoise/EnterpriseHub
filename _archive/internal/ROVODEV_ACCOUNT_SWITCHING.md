# Rovo Dev Account Switching Workflow

## Quick Reference

### Your Accounts
1. **Personal Account**: chunkytortoise2@gmail.com (2,000 credits/month)
2. **Work Account**: [YOUR_WORK_EMAIL] (2,000 credits/month)

### Credit Reset Schedule
- Credits reset monthly on the date you first signed up
- Standard trial accounts get 2,000 credits per month
- Extra usage is NOT available on Standard trial

---

## Method 1: Using the Automated Script (Recommended)

### Quick Start
```bash
cd /Users/cave/enterprisehub
./scripts/switch-rovodev-account.sh
```

The script will guide you through:
- Viewing current account status
- Switching between accounts
- Manual login for new accounts

---

## Method 2: Manual Command Line

### Step 1: Check Current Account Status
```bash
acli rovodev auth status
```

**Expected Output:**
```
✓ Authenticated
  Email: chunkytortoise2@gmail.com
  Token: ATAT************************
```

### Step 2: Logout from Current Account
```bash
acli rovodev auth logout
```

**Expected Output:**
```
✓ Logout successful
```

### Step 3: Login to New Account

#### Option A: With Token String
```bash
echo "YOUR_API_TOKEN_HERE" | acli rovodev auth login --email "your-email@example.com" --token
```

#### Option B: With Token from File
```bash
cat ~/path/to/token.txt | acli rovodev auth login --email "your-email@example.com" --token
```

#### Option C: Interactive Login
```bash
acli rovodev auth login
# Then paste your token when prompted
```

### Step 4: Verify New Login
```bash
acli rovodev auth status
```

---

## Generating API Tokens

### For Both Personal and Work Accounts

1. **Go to Atlassian Account Settings**
   - URL: https://id.atlassian.com/manage-profile/security/api-tokens

2. **Login with the account you want to generate token for**
   - For personal: chunkytortoise2@gmail.com
   - For work: [YOUR_WORK_EMAIL]

3. **Create API Token**
   - Click "Create API token"
   - Give it a label: "Rovo Dev CLI - [Month/Year]"
   - Copy the token immediately (it won't be shown again)

4. **Store Token Securely**
   ```bash
   # Create a secure tokens directory
   mkdir -p ~/.atlassian/tokens
   chmod 700 ~/.atlassian/tokens

   # Save token to file (replace with actual token)
   echo "YOUR_TOKEN_HERE" > ~/.atlassian/tokens/personal-token.txt
   chmod 600 ~/.atlassian/tokens/personal-token.txt

   # Or for work account
   echo "YOUR_TOKEN_HERE" > ~/.atlassian/tokens/work-token.txt
   chmod 600 ~/.atlassian/tokens/work-token.txt
   ```

---

## Quick Switch Commands

### Switch to Personal Account
```bash
acli rovodev auth logout && \
cat ~/.atlassian/tokens/personal-token.txt | \
acli rovodev auth login --email "chunkytortoise2@gmail.com" --token && \
acli rovodev auth status
```

### Switch to Work Account
```bash
acli rovodev auth logout && \
cat ~/.atlassian/tokens/work-token.txt | \
acli rovodev auth login --email "YOUR_WORK_EMAIL" --token && \
acli rovodev auth status
```

---

## Creating Convenient Aliases

Add these to your `~/.zshrc` or `~/.bashrc`:

```bash
# Rovo Dev Account Switcher
alias rovo-personal='acli rovodev auth logout && cat ~/.atlassian/tokens/personal-token.txt | acli rovodev auth login --email "chunkytortoise2@gmail.com" --token && acli rovodev auth status'

alias rovo-work='acli rovodev auth logout && cat ~/.atlassian/tokens/work-token.txt | acli rovodev auth login --email "YOUR_WORK_EMAIL" --token && acli rovodev auth status'

alias rovo-status='acli rovodev auth status'

alias rovo-switch='~/enterprisehub/scripts/switch-rovodev-account.sh'
```

**After adding aliases:**
```bash
source ~/.zshrc  # or source ~/.bashrc
```

**Usage:**
```bash
rovo-status     # Check current account
rovo-personal   # Switch to personal account
rovo-work       # Switch to work account
rovo-switch     # Run interactive switcher script
```

---

## Troubleshooting

### Error: "You've reached your Rovo Dev credit limit"

**Solution:**
1. Check when credits reset:
   ```bash
   acli rovodev run
   # Look for message: "Your Rovo Dev usage resets in Xd Xh Xm"
   ```

2. Switch to your other account:
   ```bash
   rovo-work  # or rovo-personal
   ```

### Error: "authentication failed"

**Possible causes:**
1. **Expired Token**: Generate a new API token
2. **Wrong Email**: Verify email matches the account that generated the token
3. **Invalid Token Format**: Check for extra spaces or newlines

**Solution:**
```bash
# Generate new token at: https://id.atlassian.com/manage-profile/security/api-tokens
# Then login again with new token
acli rovodev auth logout
echo "NEW_TOKEN_HERE" | acli rovodev auth login --email "your-email@example.com" --token
```

### Error: "unauthorized: use 'acli rovodev auth login' to authenticate"

**Solution:**
```bash
# You're not logged in, just login
cat ~/.atlassian/tokens/personal-token.txt | \
acli rovodev auth login --email "chunkytortoise2@gmail.com" --token
```

---

## Best Practices

### Security
1. **Never commit tokens to git**
   ```bash
   # Ensure tokens directory is in .gitignore
   echo "~/.atlassian/tokens/" >> ~/.gitignore
   echo ".atlassian/" >> ~/.gitignore
   ```

2. **Rotate tokens regularly** (every 3-6 months)

3. **Use separate tokens for different machines**

### Credit Management
1. **Monitor usage**: Check credits before large tasks
   ```bash
   acli rovodev run
   # Check the credit limit message
   ```

2. **Plan monthly**: Know when credits reset

3. **Account rotation**:
   - Start month with personal account
   - Switch to work account mid-month if needed
   - Switch back when work credits reset

### Workflow Optimization
1. **Check before starting work**:
   ```bash
   rovo-status
   ```

2. **Switch proactively** before credits run out:
   ```bash
   # If you see you're close to limit, switch early
   rovo-work
   ```

3. **Keep both tokens ready** in the secure directory

---

## Reference: Account Information Template

### Personal Account (chunkytortoise2@gmail.com)
- **Email**: chunkytortoise2@gmail.com
- **Token Location**: `~/.atlassian/tokens/personal-token.txt`
- **Credits**: 2,000/month
- **Reset Date**: [Fill in after first use]
- **Use For**: Personal projects, learning, experimentation

### Work Account ([YOUR_WORK_EMAIL])
- **Email**: [YOUR_WORK_EMAIL]
- **Token Location**: `~/.atlassian/tokens/work-token.txt`
- **Credits**: 2,000/month
- **Reset Date**: [Fill in after first use]
- **Use For**: Work projects, professional development

---

## Quick Commands Cheat Sheet

```bash
# Status Check
acli rovodev auth status

# Logout
acli rovodev auth logout

# Login (interactive)
acli rovodev auth login

# Login (with token)
echo "TOKEN" | acli rovodev auth login --email "EMAIL" --token

# Run Rovo Dev
acli rovodev run

# Switch Script
./scripts/switch-rovodev-account.sh

# Aliases (after setup)
rovo-status
rovo-personal
rovo-work
rovo-switch
```

---

## Notes

- **Current Active Account**: chunkytortoise2@gmail.com
- **Credits Remaining**: Check with `acli rovodev run`
- **Last Updated**: 2026-01-04
- **Script Location**: `/Users/cave/enterprisehub/scripts/switch-rovodev-account.sh`

---

## Support

If you encounter issues:
1. Check this documentation
2. Run the troubleshooting commands
3. Regenerate API tokens if needed
4. Contact Atlassian support: https://support.atlassian.com/

For script issues, check:
```bash
cat /Users/cave/enterprisehub/scripts/switch-rovodev-account.sh
```
