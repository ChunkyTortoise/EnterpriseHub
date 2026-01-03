GEMINI BROWSER EXPLORATION PROMPT
System Analysis for GHL Real Estate AI Integration


You are helping me reverse-engineer requirements for a real estate AI qualification assistant by exploring two live systems: GoHighLevel (GHL) and Closer Control. I need you to systematically navigate these platforms, extract configurations, and document everything.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ACCESS CREDENTIALS

SYSTEM 1: Closer Control Dashboard
URL: https://my.closercontrol.com/v2/location/KghwPKXU1zBjqhegruDM/dashboard
Login: Already added as team member (use current browser session or check saved credentials)

SYSTEM 2: GoHighLevel (Lyrio Agency)
Platform: Lyrio sub-account
Access: Already added to team
Note: Look for "Lyrio" in account switcher


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOUR MISSION

Navigate both systems and extract the following information in structured format. Take screenshots of EVERYTHING important.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 1: FIND THE KEY AUTOMATION

CRITICAL: Locate automation named "3. ai assistant on and off tag removal"

Steps:
1. Navigate to Automations section
2. Search for "ai assistant" or browse all automations
3. Click into the automation
4. Take screenshots of ENTIRE flow (all steps, triggers, conditions)

Extract and document:
   • TRIGGER: What starts this automation? (tag added, stage change, reply received?)
   • CONDITIONS: What filters/rules apply? (contact has specific tag, field value, etc.)
   • ACTIONS: What happens? (add tags, remove tags, send webhook, update fields)
   • WEBHOOK URL: If it sends a webhook, what's the URL?
   • TAGS USED: List all tags mentioned in this automation
   • TIMING: Any delays or wait steps?

Screenshot naming:
   screenshot_automation_main.png
   screenshot_automation_trigger.png
   screenshot_automation_actions.png
   screenshot_automation_conditions.png


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 2: MAP ALL AUTOMATIONS RELATED TO AI/QUALIFYING

Search for automations containing these keywords:
   • AI
   • Qualifying
   • Needs Qualifying
   • Hit List
   • Hot Lead
   • Warm Lead
   • Cold Lead
   • Pre-Approval
   • Tag

For EACH automation found, document:

Automation Name: _________________________________

Trigger Type:
   [ ] Contact tagged
   [ ] Pipeline stage change
   [ ] Form submitted
   [ ] Inbound message received
   [ ] Custom field updated
   [ ] Manual
   [ ] Other

Trigger Details: _________________________________

Actions (step by step):
   1. ______________________________________________
   2. ______________________________________________
   3. ______________________________________________

Tags Added: _____________________________________
Tags Removed: ___________________________________
Webhooks Called: ________________________________
Custom Fields Updated: __________________________

Screenshot: automation_[name].png


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 3: DOCUMENT THE PIPELINE

Navigate to: Contacts → Pipelines (or Opportunities → Pipelines)

Find the main pipeline for lead qualification.

Extract:
   • Pipeline name
   • All stages (in order, from first to last)
   • Which stage triggers AI engagement
   • Which stage means "hot lead ready for human"
   • Any automation triggers on stage changes

Create a flow diagram (text format):

Stage 1: [Name] → Action: [what happens]
   ↓
Stage 2: [Name] → Action: [what happens]
   ↓
Stage 3: [Name] → Action: [AI ENGAGES HERE]
   ↓
Stage 4: [Name] → Action: [AI STOPS HERE]
   ↓
Stage 5: [Name] → Action: [human takes over]

Screenshot: pipeline_stages.png


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 4: EXTRACT ALL TAGS

Navigate to: Settings → Tags

List EVERY tag, organized by category:

AI CONTROL TAGS:
   • ________________________________________________
   • ________________________________________________

LEAD TEMPERATURE TAGS:
   • ________________________________________________
   • ________________________________________________

QUALIFYING STATUS TAGS:
   • ________________________________________________
   • ________________________________________________

DISPOSITION TAGS:
   • Needs Qualifying
   • Hit List
   • [others...]

PROPERTY PREFERENCE TAGS:
   • ________________________________________________
   • ________________________________________________

OTHER TAGS:
   • ________________________________________________
   • ________________________________________________

Screenshot: tags_full_list.png


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 5: ANALYZE CUSTOM FIELDS

Navigate to: Settings → Custom Fields

For fields related to qualifying, document:

Field Name: Budget
   Type: [ ] Text [ ] Number [ ] Dropdown [ ] Date [ ] Phone
   Options (if dropdown): ___________________________
   Required: [ ] Yes [ ] No
   Used in automations: [ ] Yes [ ] No

Field Name: Location Preference
   Type: _____________________________________________
   Options: __________________________________________

Field Name: Timeline
   Type: _____________________________________________
   Options: __________________________________________

Field Name: Bedrooms
   Type: _____________________________________________
   Options: __________________________________________

Field Name: Pre-Approval Status
   Type: _____________________________________________
   Options: __________________________________________

Field Name: Lead Score
   Type: _____________________________________________
   Options: __________________________________________

[List ALL other custom fields]

Screenshot: custom_fields.png


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 6: REVIEW CONVERSATION TEMPLATES

Navigate to: Marketing → Templates OR Conversations → Templates

Find and document templates for:

TEMPLATE 1: Initial Outreach
   Name: ____________________________________________
   Channel: [ ] SMS [ ] Email [ ] WhatsApp
   Full text:
   ________________________________________________
   ________________________________________________
   ________________________________________________

TEMPLATE 2: Qualifying Questions
   Name: ____________________________________________
   Questions asked (in order):
   1. ______________________________________________
   2. ______________________________________________
   3. ______________________________________________
   4. ______________________________________________
   5. ______________________________________________

TEMPLATE 3: Objection Handling
   Name: ____________________________________________
   Example objection: "Too expensive"
   Response:
   ________________________________________________
   ________________________________________________

TEMPLATE 4: Hot Lead Handoff
   Name: ____________________________________________
   What it says:
   ________________________________________________
   ________________________________________________

Screenshot: templates_list.png
Screenshot: template_qualifying.png
Screenshot: template_objection.png


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 7: CHECK WEBHOOK CONFIGURATION

Navigate to: Settings → Webhooks OR Integrations → Webhooks

For EACH webhook found:

Webhook 1:
   Name: ____________________________________________
   URL: _____________________________________________
   Trigger Event: ___________________________________
   Payload includes:
      [ ] Contact ID
      [ ] Contact name
      [ ] Contact tags
      [ ] Contact custom fields
      [ ] Message text
      [ ] Other: _____________________________________
   Active: [ ] Yes [ ] No

Screenshot: webhook_config.png


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 8: EXAMINE AI SETTINGS (If Available)

Navigate to: Settings → AI OR Conversations → AI

Document current AI configuration:

AI Assistant Name: _______________________________
Provider: [ ] GHL Native [ ] External [ ] None
Model: ___________________________________________
System Instructions/Prompt:
   ________________________________________________
   ________________________________________________
   ________________________________________________
   ________________________________________________

Knowledge Base:
   [ ] Uploaded documents
   [ ] Website scraping
   [ ] Manual entries
   Content includes:
   ________________________________________________

Enabled for:
   [ ] All contacts
   [ ] Specific tags: _______________________________
   [ ] Specific stages: ____________________________

Screenshot: ai_settings.png


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 9: ANALYZE SAMPLE CONTACTS

Navigate to: Contacts → All Contacts

Find 3 example contacts in different states:

CONTACT 1: Cold Lead
   Name: ____________________________________________
   Tags: ____________________________________________
   Pipeline Stage: __________________________________
   Custom Fields (Budget, Location, etc.):
   ________________________________________________
   Last Activity: ___________________________________
   Last Message Exchange (copy 3-5 messages):
   ________________________________________________
   ________________________________________________

Screenshot: contact_cold.png

CONTACT 2: Warm Lead
   Name: ____________________________________________
   Tags: ____________________________________________
   Pipeline Stage: __________________________________
   Custom Fields:
   ________________________________________________

Screenshot: contact_warm.png

CONTACT 3: Hot Lead
   Name: ____________________________________________
   Tags: ____________________________________________
   Pipeline Stage: __________________________________
   Custom Fields:
   ________________________________________________

Screenshot: contact_hot.png


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 10: CONVERSATION FLOW ANALYSIS

Find a complete conversation thread from start to finish.

Navigate to: Conversations → Recent

Open a conversation that shows:
   • Initial outreach
   • Lead responds
   • Qualifying questions asked
   • Lead provides information
   • Lead gets tagged/moved to stage

Document the EXACT flow:

Message 1 (Outbound from agent/AI):
   Text: ___________________________________________
   ________________________________________________

Message 2 (Inbound from lead):
   Text: ___________________________________________
   ________________________________________________

Message 3 (Outbound):
   Text: ___________________________________________
   ________________________________________________

[Continue for entire conversation]

After message X, automation triggered:
   Action: __________________________________________
   Tags added: ______________________________________
   Stage changed to: ________________________________

Screenshot: conversation_example.png


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 11: EXTRACT QUALIFYING CRITERIA

Based on all the above, determine:

WHAT MAKES A LEAD "HOT"?
   Criteria 1: ______________________________________
   Criteria 2: ______________________________________
   Criteria 3: ______________________________________

WHAT MAKES A LEAD "WARM"?
   Criteria 1: ______________________________________
   Criteria 2: ______________________________________

WHAT MAKES A LEAD "COLD"?
   Criteria 1: ______________________________________
   Criteria 2: ______________________________________

WHEN DOES AI ENGAGE?
   Trigger: _________________________________________
   Condition: _______________________________________

WHEN DOES AI STOP?
   Trigger: _________________________________________
   Condition: _______________________________________


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DELIVERABLE FORMAT

Please provide your findings in this exact structure:


PART 1: AUTOMATION FLOW SUMMARY

The "3. ai assistant on and off tag removal" automation works as follows:

Trigger: [exact trigger condition]

Step 1: [what happens]
Step 2: [what happens]
Step 3: [what happens]
...

Tags used:
   • AI-On
   • AI-Off
   • Needs-Qualifying
   • [etc.]

Webhook: [URL if present]


PART 2: LEAD LIFECYCLE

Stage 1: [name] → [what happens]
Stage 2: [name] → [what happens]
Stage 3: [name] → AI ENGAGES because [condition]
Stage 4: [name] → AI STOPS because [condition]
Stage 5: [name] → Human takes over


PART 3: QUALIFYING QUESTIONS

The system asks these questions in this order:
1. [question text]
2. [question text]
3. [question text]
...


PART 4: CUSTOM FIELDS

Budget: [field type, options]
Location: [field type, options]
Timeline: [field type, options]
...


PART 5: CONVERSATION TONE

Based on templates and actual conversations, the tone is:
[description + examples]


PART 6: TECHNICAL REQUIREMENTS

To build the webhook integration, I need:
   • Webhook endpoint that receives: [data format]
   • AI should respond via: [GHL API, webhook response, etc.]
   • Authentication: [API key location, header format]
   • Response format: [JSON structure expected]


PART 7: SCREENSHOTS

All screenshots saved with descriptive filenames:
   • screenshot_automation_main.png
   • screenshot_pipeline_stages.png
   • [list all screenshots]


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANT NOTES

1. Take screenshots of EVERYTHING - especially the automation flow
2. Copy exact text from templates (don't paraphrase)
3. Note exact tag names (spelling matters)
4. Document webhook URLs completely
5. If you can't find something, note "NOT FOUND" instead of guessing
6. If login is needed, check browser for saved credentials
7. Explore thoroughly - check all sidebar menus


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ADDITIONAL EXPLORATION

If you have time, also check:
   • Reports/Analytics (what metrics do they track?)
   • Phone number settings (twilio integration?)
   • Email settings (SMTP, templates)
   • Calendar/booking settings
   • Forms (lead capture forms)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BEGIN EXPLORATION NOW

Start with TASK 1 (find the key automation) and work through systematically. Take your time - accuracy is more important than speed. Document everything.
