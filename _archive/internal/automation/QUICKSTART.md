# 🚀 QUICK START - Multi-Platform Account Creator

**Goal:** Create 5 freelance accounts in 30-45 minutes

---

## Step 1: Install (2 minutes)

```bash
cd /Users/Cave/Desktop/enterprise-hub/EnterpriseHub/automation

pip install -r requirements_automation.txt
playwright install chromium
```

---

## Step 2: Configure (3 minutes)

Open `master_orchestrator.py` and edit lines 25-57:

```python
USER_PROFILE = {
    "email": "YOUR_EMAIL@gmail.com",       # ← CHANGE
    "password": "YOUR_PASSWORD",            # ← CHANGE
    "full_name": "YOUR FULL NAME",          # ← CHANGE
    "username": "your_username",            # ← CHANGE
    "phone": "+1234567890",                 # ← CHANGE
    # Rest is pre-filled from your portfolio
}
```

---

## Step 3: Run (30-45 minutes)

```bash
python master_orchestrator.py
```

**What happens:**
1. 5 browser windows open
2. Forms auto-fill
3. **YOU solve CAPTCHAs when prompted**
4. Accounts created

---

## Step 4: Verify (15 minutes)

After script finishes:

1. Check email for verification links (all 5 platforms)
2. Click each verification link
3. Complete SMS verification if prompted
4. Upload profile photo to each platform

---

## Expected Results

✅ **Best Case:** 3-4 accounts fully created
⏳ **Likely:** 2-3 accounts created, 1-2 need manual steps
❌ **Worst Case:** 1 account created, others need manual signup

---

## If It Fails

**Option A:** Manual signup with templates
```bash
./quick_setup.sh
# Opens all platforms, copies profile to clipboard
```

**Option B:** Focus on 1-2 platforms manually
- Fiverr (highest revenue)
- Freelancer.com (highest volume)

---

## After Accounts Created

**Day 1 (TODAY):**
- [ ] Verify all emails
- [ ] Upload profile photos
- [ ] Complete bios
- [ ] Set hourly rates ($50+)

**Day 2:**
- [ ] Create 1 Fiverr gig
- [ ] Bid on 5 Freelancer jobs
- [ ] Create 2 PeoplePerHour Hourlies

**Day 3:**
- [ ] Check for responses
- [ ] Apply to 5 more jobs across platforms

---

## ⚠️ Remember

- This violates most platform ToS
- 30-60% success rate expected
- Manual verification always required
- Use VPN for best results

---

## Quick Commands

```bash
# Full automation (all 5 platforms)
python master_orchestrator.py

# Test single platform (Fiverr)
python -c "from agents.fiverr_agent import FiverrAgent; import asyncio; asyncio.run(FiverrAgent({...}).create_account())"

# Manual setup with templates
./quick_setup.sh

# Reddit auto-poster
python reddit_forhire_post.py
```

---

**Ready? Run this now:**

```bash
python master_orchestrator.py
```

Solve CAPTCHAs when prompted. Script handles the rest.
