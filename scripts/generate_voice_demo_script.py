#!/usr/bin/env python3
"""
Generate Voice AI Demo Script
=============================
Generates a script for sales representatives to demonstrate Voice AI capabilities.
"""

import sys
from datetime import datetime

DEMO_SCRIPT = """

# Enterprise Voice AI Demo Script
# Generated: {timestamp}
# Target Audience: Enterprise Real Estate Brokerages

## 1. Introduction (30 seconds)
"Today I'm going to show you how our Voice AI doesn't just answer calls—it qualifies leads, books appointments, and nurtures relationships 24/7, indistinguishable from your top agents."

## 2. Live Interaction Demo (2 minutes)
**Action:** Click 'Start Voice Session' in the dashboard.
**Roleplay:** Act as a skeptical buyer.

**You:** "Hi, I'm looking for a 3-bedroom house in Rancho Cucamonga under $600k, but I'm worried about interest rates."
**AI (Jorge):** "I completely understand that concern. The good news is that while rates have fluctuated, we're seeing some excellent value in the Rancho Cucamonga market right now, especially for 3-bedroom homes in that price range. Are you looking for move-in ready, or are you open to something that needs a little work?"

**(Highlight: The AI acknowledged the concern (empathy) and pivoted to a qualifying question immediately.)**

**You:** "I need something move-in ready. I have two kids and no time for renovations."
**AI (Jorge):** "Got it. Move-in ready makes perfect sense with a busy family. I have access to several listings in great school districts that just hit the market. Would you be available this Saturday morning to take a look at a few?"

**(Highlight: Context retention (kids -> school districts) and immediate attempt to close for an appointment.)**

## 3. Analytics & Insights (1 minute)
**Action:** Show the 'Voice Analytics Dashboard'.
"While the call is happening, look at what the system captures in real-time:"
- **Sentiment Analysis:** Positive/Negative tracking
- **Intent Detection:** 'High Intent Buyer'
- **Next Best Action:** 'Schedule Viewing'

## 4. Closing (30 seconds)
"This system handles 500+ concurrent calls. That's 500 leads being qualified simultaneously while your agents focus on closing the deals in person. That's the power of Enterprise Voice AI."
"""

def main():
    print(DEMO_SCRIPT.format(timestamp=datetime.now().isoformat()))
    
    with open("VOICE_AI_DEMO_SCRIPT.md", "w") as f:
        f.write(DEMO_SCRIPT.format(timestamp=datetime.now().isoformat()))
    print("\n✅ Demo script saved to VOICE_AI_DEMO_SCRIPT.md")

if __name__ == "__main__":
    main()
