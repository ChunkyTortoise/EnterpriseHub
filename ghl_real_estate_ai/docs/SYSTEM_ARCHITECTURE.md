SYSTEM EXPLORATION GUIDE
GHL & Closer Control Analysis for Jose's Project

Date: January 3, 2026
Purpose: Reverse-engineer requirements from live systems


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1: ACCESS CLOSER CONTROL DASHBOARD

URL: https://my.closercontrol.com/v2/location/KghwPKXU1zBjqhegruDM/dashboard

Login: (Already added as team member)

WHAT TO LOOK FOR:

1. Left Sidebar - Find "Automations" or "Workflows"
   → Take screenshot of menu

2. Search for: "3. ai assistant on and off tag removal"
   → This is the key automation Jose mentioned
   → Take screenshots of ENTIRE automation flow

3. Look for:
   → Trigger conditions (What starts the automation?)
   → Tag operations (What tags are added/removed?)
   → Webhook URLs (Where does it send data?)
   → Conditions/filters (When does AI engage?)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 2: FIND AI TRIGGER POINTS

Navigate to: Automations → Active Automations

SEARCH FOR KEYWORDS:
   • "AI"
   • "Qualifying"
   • "Needs Qualifying"
   • "Hit List"
   • "Hot Lead"
   • "Tag"
   • "Webhook"

FOR EACH AUTOMATION FOUND:

1. Automation Name: ___________________________

2. Trigger:
   [ ] Contact tagged with: ___________________
   [ ] Contact enters pipeline stage: __________
   [ ] Contact replies to message
   [ ] Contact custom field changes
   [ ] Manual trigger
   [ ] Other: _________________________________

3. Actions Taken:
   [ ] Add tag: _______________________________
   [ ] Remove tag: ____________________________
   [ ] Send webhook to: _______________________
   [ ] Update custom field: ___________________
   [ ] Send SMS/Email
   [ ] Other: _________________________________

4. Conditions (What must be true?):
   _____________________________________________
   _____________________________________________

5. Screenshot filename: _______________________


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 3: ANALYZE CONTACT FLOW

Navigate to: Contacts → Pipelines (or Opportunities)

DOCUMENT THE PIPELINE:

Pipeline Name: _______________________________

Stages (in order):
   1. ___________________________________________
   2. ___________________________________________
   3. ___________________________________________
   4. ___________________________________________
   5. ___________________________________________

WHERE DOES AI ENGAGE?
   Stage: _______________________________________
   Tag: _________________________________________

WHERE DOES AI STOP?
   Stage: _______________________________________
   Tag: _________________________________________


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 4: EXAMINE TAGS

Navigate to: Settings → Tags (or Contacts → Tags)

LIST ALL TAGS RELATED TO:

AI Control:
   • ____________________________________________
   • ____________________________________________

Lead Temperature:
   • ____________________________________________
   • ____________________________________________

Qualifying Status:
   • ____________________________________________
   • ____________________________________________

Other Important Tags:
   • ____________________________________________
   • ____________________________________________


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 5: CHECK CUSTOM FIELDS

Navigate to: Settings → Custom Fields

DOCUMENT FIELDS USED FOR:

Budget:
   Field Name: __________________________________
   Type: [ ] Text [ ] Number [ ] Dropdown
   Options: _____________________________________

Location:
   Field Name: __________________________________
   Type: [ ] Text [ ] Number [ ] Dropdown
   Options: _____________________________________

Timeline:
   Field Name: __________________________________
   Type: [ ] Text [ ] Number [ ] Dropdown
   Options: _____________________________________

Bedrooms:
   Field Name: __________________________________
   Type: [ ] Text [ ] Number [ ] Dropdown
   Options: _____________________________________

Pre-Approval Status:
   Field Name: __________________________________
   Type: [ ] Text [ ] Number [ ] Dropdown
   Options: _____________________________________

Other Qualifying Fields:
   • ____________________________________________
   • ____________________________________________


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 6: REVIEW CONVERSATION TEMPLATES

Navigate to: Marketing → Templates (or Conversations → Templates)

FIND TEMPLATES FOR:

Initial Outreach:
   Template Name: _______________________________
   Copy first 2-3 messages here:
   _____________________________________________
   _____________________________________________

Qualifying Questions:
   Template Name: _______________________________
   Questions asked:
   1. __________________________________________
   2. __________________________________________
   3. __________________________________________

Objection Handling:
   Template Name: _______________________________
   Example responses:
   _____________________________________________
   _____________________________________________

Hot Lead Handoff:
   Template Name: _______________________________
   What happens:
   _____________________________________________


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 7: FIND WEBHOOK CONFIGURATION

Navigate to: Settings → Webhooks (or Integrations → Webhooks)

FOR EACH WEBHOOK FOUND:

Webhook Name: ________________________________
URL: __________________________________________
Trigger: ______________________________________
Payload includes: _____________________________
Active: [ ] Yes [ ] No


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 8: EXAMINE SAMPLE CONTACTS

Navigate to: Contacts → All Contacts

FIND 3 EXAMPLE CONTACTS:

CONTACT 1 (Cold Lead):
   Name: ________________________________________
   Tags: ________________________________________
   Stage: _______________________________________
   Last Activity: _______________________________
   Screenshot: __________________________________

CONTACT 2 (Warm Lead):
   Name: ________________________________________
   Tags: ________________________________________
   Stage: _______________________________________
   Last Activity: _______________________________
   Screenshot: __________________________________

CONTACT 3 (Hot Lead):
   Name: ________________________________________
   Tags: ________________________________________
   Stage: _______________________________________
   Last Activity: _______________________________
   Screenshot: __________________________________


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 9: REVIEW AI ASSISTANT SETTINGS

Navigate to: Settings → AI → Conversations (or similar)

CURRENT AI CONFIGURATION:

AI Name: ______________________________________
Model: ________________________________________
Enabled for: __________________________________
Instructions/Prompt:
   _____________________________________________
   _____________________________________________
   _____________________________________________

Knowledge Base:
   [ ] Property listings
   [ ] FAQs
   [ ] Scripts
   [ ] Other: __________________________________


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL SCREENSHOTS NEEDED

Priority 1 (MUST HAVE):
   1. "3. ai assistant on and off tag removal" automation (full flow)
   2. Pipeline stages view
   3. All tags list
   4. Qualifying question templates

Priority 2 (Important):
   5. Webhook configuration
   6. Custom fields list
   7. Sample hot lead conversation
   8. Current AI settings

Priority 3 (Nice to Have):
   9. Dashboard overview
   10. Contact example profiles


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SAVE SCREENSHOTS TO:

/Users/cave/Downloads/ghl_exploration/
   → screenshot_01_automation.png
   → screenshot_02_pipeline.png
   → screenshot_03_tags.png
   → etc.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NEXT STEPS AFTER EXPLORATION

Once you have this information:
   1. Share screenshots with me
   2. Fill in the blanks above
   3. I'll create exact technical requirements
   4. We'll build Path B backend API
   5. Deploy and integrate

Estimated time: 30-45 minutes for exploration
