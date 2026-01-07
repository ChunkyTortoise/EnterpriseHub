# EnterpriseHub Deployment Checklist - Jorge's System

## Status: READY TO DEPLOY

All code is complete and tested. Follow these steps to go live.

---

## Step 1: Push Code to GitHub

```bash
cd /Users/cave/enterprisehub

# Check status
git status

# Add all changes
git add .

# Commit
git commit -m "feat: Complete Jorge's EnterpriseHub deployment with GHL integration

- Add automatic user registration for Jorge
- Configure GHL API integration
- Set up Render deployment configuration
- Add multi-account support architecture
- Complete email templates and documentation

Ready for production deployment."

# Push to main
git push origin main
```

---

## Step 2: Deploy to Render

### Option A: Automatic (via render.yaml)

1. **Go to Render Dashboard**: https://dashboard.render.com/
2. **Click**: "New" → "Web Service"
3. **Connect Repository**: Select `enterprisehub` repository
4. **Render will auto-detect**: The `render.yaml` file
5. **Click**: "Apply" or "Create Web Service"

### Option B: Manual Setup

1. **Go to Render Dashboard**: https://dashboard.render.com/
2. **Click**: "New" → "Web Service"
3. **Configure**:
   - **Name**: `enterprisehub`
   - **Region**: Oregon (US West)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
   - **Instance Type**: Free

---

## Step 3: Set Environment Variables

In Render Dashboard → Your Service → "Environment" tab, add these **EXACT** variables:

### Required Variables

```bash
# GoHighLevel Configuration
GHL_LOCATION_ID=3xt4qayAh35BlDLaUv7P
GHL_API_KEY=your_ghl_api_key_here

# Anthropic API Key (YOUR KEY - DO NOT COMMIT TO GIT)
ANTHROPIC_API_KEY=your-actual-anthropic-api-key-here

# Database (Render will auto-create and inject this)
# DATABASE_URL will be automatically set by Render PostgreSQL addon
```

### Optional Variables (for future use)

```bash
# Email Configuration (when you set up email sending)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Security
SECRET_KEY=your-secret-key-for-sessions
```

---

## Step 4: Add PostgreSQL Database

1. **In Render Dashboard**: Go to your `enterprisehub` service
2. **Click**: "New" → "PostgreSQL"
3. **Configure**:
   - **Name**: `enterprisehub-db`
   - **Region**: Same as your web service (Oregon)
   - **Plan**: Free
4. **Connect to Service**:
   - Render will automatically add `DATABASE_URL` environment variable
5. **Database will be created with**:
   - Jorge's account pre-configured
   - All necessary tables

---

## Step 5: Verify Deployment

### After deployment completes:

1. **Check Logs**: Render Dashboard → Logs tab
   - Look for: `Streamlit is running`
   - Should show: `You can now view your Streamlit app in your browser`

2. **Access Application**:
   - URL will be: `https://enterprisehub.onrender.com` (or similar)
   - Copy this URL from Render dashboard

3. **Test Login**:
   - Go to the URL
   - Login with Jorge's credentials:
     - **Email**: jorge@rovodevco.com
     - **Password**: (The one you set in the system)

---

## Step 6: Send Email to Jorge

Once deployment is verified and working, send Jorge this email:

### Email Template

**Subject**: EnterpriseHub Live - Your Login Details

---

Hi Jorge,

Great news! Your EnterpriseHub system is now live and ready to use.

**Access Your Dashboard:**
🔗 https://enterprisehub.onrender.com

**Login Credentials:**
- Email: jorge@rovodevco.com
- Password: [INSERT PASSWORD]

**What You Can Do Now:**
1. ✅ Manage all your GoHighLevel contacts in one place
2. ✅ Access AI-powered tools for your business
3. ✅ View analytics and insights from your GHL account

**About Your Sub-Accounts:**
YES - The system is designed to manage all your sub-accounts from a single dashboard. We're launching with your main account today to get you started. I can easily add your other sub-accounts later without you needing to install anything else.

**Need Help?**
If you have any questions or need assistance, just reply to this email.

Best regards,
Cayman

---

**📌 SECURITY NOTE**: Please change your password after first login.

---

## Troubleshooting

### If deployment fails:

1. **Check Logs**: Render Dashboard → Logs
2. **Common Issues**:
   - Missing environment variables → Add them in Environment tab
   - Build failures → Check `requirements.txt` is present
   - Database connection → Verify PostgreSQL is linked

### If login fails:

1. **Check Database**: Verify Jorge's user was created
2. **Check Logs**: Look for authentication errors
3. **Reset Password**: Use admin tools to reset if needed

---

## Post-Deployment Tasks

### Immediate:
- [ ] Push code to GitHub
- [ ] Deploy to Render
- [ ] Set environment variables
- [ ] Add PostgreSQL database
- [ ] Verify deployment
- [ ] Test login
- [ ] Send email to Jorge

### Within 24 Hours:
- [ ] Monitor logs for errors
- [ ] Check Jorge's first login
- [ ] Verify GHL integration is working
- [ ] Test contact sync

### Within 1 Week:
- [ ] Add other sub-accounts (if requested)
- [ ] Set up email notifications
- [ ] Configure backup strategy
- [ ] Add monitoring/alerts

---

## Emergency Contacts

- **Render Support**: https://render.com/docs/support
- **Your Email**: [Your email]
- **Jorge's Email**: jorge@rovodevco.com

---

## Deployment Completion

**Date Deployed**: _______________
**Deployment URL**: _______________
**Jorge Notified**: _______________
**First Login Success**: _______________

---

**Status**: 🟢 READY TO DEPLOY

All systems are configured and tested. Execute steps 1-6 above to go live.
