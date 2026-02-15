# Gumroad Bank Setup Checklist

**Purpose**: Step-by-step guide to connect a bank account for payouts on Gumroad.
**Account**: chunktort@gmail.com

---

## Prerequisites

- [ ] Gumroad account verified (email confirmed)
- [ ] US bank account with routing and account numbers ready
- [ ] OR Stripe-supported international bank account details
- [ ] Government-issued ID available (may be required for verification)

---

## Steps

### 1. Log In to Gumroad

- Go to **https://app.gumroad.com/login**
- Sign in with **chunktort@gmail.com**

### 2. Navigate to Settings

- Click the **avatar/profile icon** in the top-right corner
- Select **Settings** from the dropdown menu

### 3. Go to Payouts

- In the Settings sidebar, click **Payouts**
- This page shows your current payout method and balance

### 4. Add Bank Account

- Click **"Connect a bank account"** (or "Update payout method" if one exists)
- Gumroad uses **Stripe Connect** for payouts -- you will be redirected to Stripe's onboarding flow

### 5. Complete Stripe Onboarding

- **Business type**: Select "Individual" (unless you have a registered business)
- **Personal information**: Legal name, date of birth, last 4 of SSN
- **Address**: Must match your bank account's address on file
- **Bank account**: Enter routing number and account number
  - Routing number: 9 digits (find on checks or bank app)
  - Account number: varies by bank (find in bank app under account details)
- **ID verification**: Upload government-issued ID if prompted (driver's license or passport)

### 6. Verify Connection

- After completing Stripe onboarding, you are redirected back to Gumroad
- The Payouts page should now show your connected bank account (last 4 digits)
- Status should read **"Active"** or **"Verified"**

### 7. Set Payout Schedule

- **Options**: Weekly (default), Biweekly, Monthly
- Select your preferred schedule on the Payouts page
- Minimum payout threshold: $10.00

---

## Verification Checklist

- [ ] Bank account shows as connected on Gumroad Payouts page
- [ ] Payout schedule is set (weekly/biweekly/monthly)
- [ ] Test: Check that a small balance triggers a payout on the next cycle
- [ ] Note: First payout may take 7-14 business days while Stripe verifies

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Bank account not supported" | Ensure your bank supports ACH transfers. Try a different account. |
| Stripe onboarding stuck | Clear browser cache, try incognito mode. |
| ID verification failed | Ensure photo is clear, not expired, matches the name on file. |
| Payout not received | Check Gumroad Payouts page for "pending" status. Allow 3-5 business days after "paid" status. |
| Wrong bank details entered | Go to Settings > Payouts > Update payout method. Re-enter correct details. |

---

## Important Notes

- Gumroad takes a **10% fee** on each sale (flat rate, no monthly fee)
- Payouts are processed via **Stripe** -- you may see "Stripe" on bank statements
- **International sellers**: Gumroad supports payouts to 40+ countries via Stripe. Currency conversion fees may apply.
- Keep your bank details updated if you switch accounts
