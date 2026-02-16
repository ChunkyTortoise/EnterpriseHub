# Email 6: Cart Close

**Trigger**: D-0 (enrollment deadline day)
**Send time**: 6:00 PM PT (6 hours before close)
**From**: Cave <cave@productionai.dev>

---

**Subject**: Enrollment closes tonight at midnight

**Preview text**: This is the last email. Doors close in 6 hours.

---

Hey {first_name},

This is the final email about Cohort 1 enrollment. Doors close tonight at 11:59 PM PT.

**{total_enrolled} engineers are enrolled.** Here's a snapshot of who's in the room:

- Senior engineers from companies building AI-powered products
- Freelancers who want to offer production AI services at premium rates
- Tech leads who need to architect AI systems for their teams
- Career switchers moving from traditional software to AI engineering

If you want to be in this cohort, you have 6 hours.

[ENROLL NOW — CLOSES AT MIDNIGHT]

---

**If you're enrolled**, ignore this email. I'll see you on Day 1. Check your inbox for the onboarding email with your Discord invite and lab setup instructions.

**If you're not enrolling for Cohort 1**, no worries. I'll add you to the Cohort 2 waitlist automatically. You'll get first access when the next cohort is announced.

Cave

---

**CTA Button**: "Enroll Now — Closes at Midnight" → Maven enrollment page
**Tags to add**: cart-close-sent
**Tags to remove**: None
**Post-close automation**: After deadline passes, run automation:
  - Remove "cohort-1-prospect" tag from non-purchasers
  - Add "cohort-2-waitlist" tag
  - Move to Cohort 2 Nurture sequence
