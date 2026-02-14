# Account Setup Automation Prompt

**Email**: `caymanroden@gmail.com`  
**Purpose**: Set up third-party services for portfolio website integration

---

## Instructions for Comet Browser

Copy and paste the sections below into Comet Browser or similar automation tool. Complete each section sequentially and record the credentials as you go.

---

## 1. Formspree Setup (formspree.io)

### Step 1: Navigate and Create Account
```
1. Navigate to https://formspree.io
2. Click "Sign Up" or "Get Started"
3. Choose "Sign up with Google" OR enter email: caymanroden@gmail.com
4. If email signup: Check email for verification link and click it
5. Complete any onboarding questions (skip optional ones)
```

### Step 2: Create Contact Form
```
1. From dashboard, click "New Form" or "Create Form"
2. Enter form name: "Portfolio Contact Form"
3. Select form type: "Contact Form" or basic form
4. Set notification email to: caymanroden@gmail.com
5. Click "Create Form" or "Save"
```

### Step 3: Get Form ID
```
1. On the form details page, look for the form endpoint URL
2. It will look like: https://formspree.io/f/xyzabcde
3. The form ID is the last part: xyzabcde
4. Record this as FORMSPREE_ID
```

**Expected Output**: `FORMSPREE_ID=xyzabcde` (8 character alphanumeric)

---

## 2. Google Analytics 4 Setup (analytics.google.com)

### Step 1: Navigate and Create Account
```
1. Navigate to https://analytics.google.com
2. Sign in with Google account (use caymanroden@gmail.com)
3. If first time: Click "Start measuring"
4. Create account name: "Cayman Roden Portfolio"
5. Uncheck "Google products and services" data sharing (optional)
6. Click "Next"
```

### Step 2: Create Property
```
1. Property name: "Cayman Roden Portfolio"
2. Reporting time zone: America/Los_Angeles (Pacific Time)
3. Currency: United States Dollar (USD)
4. Click "Next"
```

### Step 3: Business Information
```
1. Industry category: "Technology" or "Business and Industrial"
2. Business size: "Small" or appropriate option
3. How you intend to use Google Analytics: Select all that apply:
   - Measure user behavior
   - Analyze performance
   - Optimize website performance
4. Click "Create"
5. Accept Terms of Service
```

### Step 4: Create Data Stream
```
1. Select platform: "Web"
2. Website URL: https://chunkytortoise.github.io
3. Stream name: "Portfolio Website"
4. Enhanced measurement: Keep enabled (default)
5. Click "Create stream"
```

### Step 5: Get Measurement ID
```
1. On the data stream details page
2. Look for "Measurement ID" (format: G-XXXXXXXXXX)
3. Record this as GA4_MEASUREMENT_ID
4. Also note the Measurement Protocol API secret if needed
```

**Expected Output**: `GA4_MEASUREMENT_ID=G-XXXXXXXXXX` (G- followed by 10 characters)

---

## 3. Stripe Setup (stripe.com)

### Step 1: Create Account
```
1. Navigate to https://dashboard.stripe.com/register
2. Email: caymanroden@gmail.com
3. Full name: Cayman Roden
4. Password: [Create secure password]
5. Click "Create account"
6. Verify email if prompted
```

### Step 2: Skip/Complete Onboarding (Test Mode)
```
1. For test mode, you can skip most verification steps
2. Click "Skip for now" or "Continue to dashboard" when possible
3. Ensure "Test mode" toggle is ON (top right corner should show "Test mode")
```

### Step 3: Get API Keys
```
1. From dashboard, click "Developers" in left sidebar
2. Click "API Keys"
3. Under "Standard keys" section:
   - Copy "Publishable key" (starts with pk_test_)
   - Click "Reveal test key" for Secret key
   - Copy "Secret key" (starts with sk_test_)
4. Record these as:
   - STRIPE_PUBLISHABLE_KEY
   - STRIPE_SECRET_KEY
```

### Step 4: Create Products and Prices

#### Product 1: Starter Plan
```
1. Navigate to "Products" in left sidebar
2. Click "Add product"
3. Name: "Starter Plan"
4. Description: "Perfect for individuals and small projects"
5. Pricing:
   - Select "Recurring"
   - Price: $49
   - Billing period: Monthly
6. Click "Save product"
7. On product page, find the "Price ID" (starts with price_)
8. Record as STRIPE_STARTER_PRICE_ID
```

#### Product 2: Professional Plan
```
1. Click "Add another product" or navigate to Products > Add product
2. Name: "Professional Plan"
3. Description: "For growing teams and businesses"
4. Pricing:
   - Select "Recurring"
   - Price: $149
   - Billing period: Monthly
5. Click "Save product"
6. Record the Price ID as STRIPE_PROFESSIONAL_PRICE_ID
```

#### Product 3: Enterprise Plan
```
1. Click "Add another product" or navigate to Products > Add product
2. Name: "Enterprise Plan"
3. Description: "For large organizations with custom needs"
4. Pricing:
   - Select "Recurring"
   - Price: $499
   - Billing period: Monthly
5. Click "Save product"
6. Record the Price ID as STRIPE_ENTERPRISE_PRICE_ID
```

**Expected Outputs**:
- `STRIPE_SECRET_KEY=sk_test_xxxxx`
- `STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx`
- `STRIPE_STARTER_PRICE_ID=price_xxxxx`
- `STRIPE_PROFESSIONAL_PRICE_ID=price_xxxxx`
- `STRIPE_ENTERPRISE_PRICE_ID=price_xxxxx`

---

## Final Output Format

After completing all setups, compile credentials in this exact format:

```env
# Formspree Configuration
FORMSPREE_ID=xyzabcde

# Google Analytics 4
GA4_MEASUREMENT_ID=G-XXXXXXXXXX

# Stripe Configuration (Test Mode)
STRIPE_SECRET_KEY=your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key_here

# Stripe Product Price IDs
STRIPE_STARTER_PRICE_ID=your_starter_price_id
STRIPE_PROFESSIONAL_PRICE_ID=your_professional_price_id
STRIPE_ENTERPRISE_PRICE_ID=price_xxxxxxxxxxxxxx
```

---

## Troubleshooting Notes

### Formspree
- If Google SSO fails, use email signup
- Free tier allows 50 submissions/month
- Form ID is visible in the form URL and dashboard

### Google Analytics
- If property already exists, create a new data stream instead
- Measurement ID is different from Property ID
- Enhanced measurement tracks page views automatically

### Stripe
- Test mode keys start with `sk_test_` and `pk_test_`
- Live mode keys start with `sk_live_` and `pk_live_`
- Price IDs are permanent once created
- Products can be edited but prices cannot be changed (create new price instead)

---

## Security Reminders

1. **Never commit these credentials to public repositories**
2. Add to `.env` file locally
3. Add `.env` to `.gitignore`
4. For production, use environment variables in hosting platform
5. Rotate Stripe keys if they're ever exposed

---

## Verification Checklist

After setup, verify each service:

- [ ] **Formspree**: Test form submission to `https://formspree.io/f/{FORMSPREE_ID}`
- [ ] **GA4**: Check real-time reports after visiting portfolio site
- [ ] **Stripe**: Verify products appear in dashboard with correct prices

---

## Quick Reference URLs

| Service | Dashboard URL |
|---------|---------------|
| Formspree | https://formspree.io/forms |
| Google Analytics | https://analytics.google.com |
| Stripe | https://dashboard.stripe.com/test |
