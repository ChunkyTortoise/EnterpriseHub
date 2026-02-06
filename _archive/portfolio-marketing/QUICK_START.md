# Quick Start Guide - Get Live in 2 Hours

> Fastest path from zero to deployed portfolio

## ⚡ Express Launch (2 Hours)

### Phase 1: Customize (30 minutes)

**1. Update Personal Info**

Open `index.html` in text editor:
- Line 5: Update page title
- Line 8: Update meta description
- Line 60-65: Update GitHub/LinkedIn links (search for "github.com/ChunkyTortoise")
- Line 480-520: Update certifications (if different)

Open `pages/services.html`:
- Line 5: Update page title
- Verify pricing matches your rates (Ctrl+F "$")

**2. Add Profile Photo (if you have one)**

- Rename your photo to `profile.jpg`
- Copy to `portfolio/assets/images/`
- Update path in `index.html` (search for "profile.jpg")

### Phase 2: Deploy (30 minutes)

**Option A: GitHub Pages (Recommended)**

```bash
cd portfolio
git init
git add .
git commit -m "Initial portfolio"

# Create repo (install gh cli first: brew install gh)
gh repo create enterprisehub-portfolio --public --source=. --push
```

Then:
1. Go to repo settings
2. Click "Pages"
3. Source: "main" branch
4. Save

Live in 2 minutes at: `https://YOUR_USERNAME.github.io/enterprisehub-portfolio/`

**Option B: Netlify Drop (Fastest)**

1. Go to [https://app.netlify.com/drop](https://app.netlify.com/drop)
2. Drag `portfolio` folder
3. Done!

### Phase 3: Share (1 hour)

**1. Update LinkedIn (20 min)**

- Add portfolio URL to Contact Info
- Update Headline: "AI/ML Engineer | Portfolio: [YOUR_URL]"
- Post announcement (copy from `LINKEDIN_CONTENT.md`)

**2. Update Upwork (20 min)**

- Copy profile overview from `UPWORK_PROFILE.md`
- Add 3 portfolio pieces
- Set hourly rate: $60-120/hr

**3. Test (20 min)**

- Open portfolio on phone
- Click all CTAs (do they work?)
- Test demo link
- Share with 3 friends for feedback

---

## 📋 Pre-Launch Checklist

- [ ] Updated all "yourdomain.com" placeholders
- [ ] Updated GitHub link
- [ ] Updated LinkedIn link
- [ ] Tested live demo link works
- [ ] Verified pricing matches your rates
- [ ] Added profile photo (or placeholder)
- [ ] Deployed to hosting
- [ ] Tested on mobile
- [ ] Shared on LinkedIn

---

## 🎯 First Week Goals

### Day 1 (Today)
- [ ] Deploy portfolio
- [ ] Update LinkedIn profile
- [ ] Post portfolio announcement on LinkedIn

### Day 2-3
- [ ] Take 6 module screenshots
- [ ] Replace placeholder images
- [ ] Add screenshots to portfolio

### Day 4-5
- [ ] Set up Upwork profile
- [ ] Write 2-3 proposals
- [ ] Connect with 10 people on LinkedIn

### Day 6-7
- [ ] Record first demo video (60 seconds)
- [ ] Post on LinkedIn
- [ ] Apply to 5 Upwork jobs

---

## 🚨 Common Issues

### "My GitHub Pages isn't working"
**Solution:**
1. Check repo is public (Settings → General)
2. Verify Pages is enabled (Settings → Pages)
3. Wait 2-3 minutes for build
4. Clear browser cache

### "Images aren't showing"
**Solution:**
- Check file paths are correct
- Verify files uploaded to `assets/images/`
- Use relative paths: `assets/images/photo.jpg` (not `/assets/`)

### "Links don't work on mobile"
**Solution:**
- Verify `<meta name="viewport">` tag exists
- Test in Chrome DevTools mobile view
- Check Tailwind CSS is loading

### "Contact form doesn't work"
**Solution:**
- Form is placeholder by default
- Add Formspree: See `README.md` → "Add Contact Form Backend"
- Or remove form and use "Email me" link

---

## 📞 Need Help?

1. **Read full docs:** `README.md`
2. **Asset creation:** `ASSET_CREATION_GUIDE.md`
3. **Platform content:** `UPWORK_PROFILE.md` & `LINKEDIN_CONTENT.md`
4. **Complete overview:** `PORTFOLIO_SUMMARY.md`

---

## 🎉 You're Ready!

Portfolio deployed? ✅
LinkedIn updated? ✅
Upwork profile ready? ✅

**Next:** Start sending proposals and connecting with potential clients.

**Target:** First inquiry within 7 days, first client within 30 days.

Good luck! 🚀
