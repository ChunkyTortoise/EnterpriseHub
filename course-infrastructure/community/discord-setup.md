# Discord Server Setup Guide

Complete setup guide for the Production AI Systems Discord community server.

## Server Creation

### Step 1: Create Server

1. Open Discord and click the **+** button in the server list
2. Select **Create My Own** > **For a club or community**
3. **Server Name**: Production AI Systems
4. **Server Icon**: Use the course logo (blue gradient with circuit/brain motif)
5. Enable **Community Server** features immediately after creation

### Step 2: Enable Community Features

Go to **Server Settings > Enable Community** and configure:

- Community overview channel: #announcements
- Rules channel: #rules
- Default notification: Only @mentions
- Remove inappropriate content: Enabled
- Require email verification: Enabled (prevents spam accounts)

### Step 3: Server Settings

| Setting | Value |
|---------|-------|
| Verification Level | Medium (must be registered on Discord for 5+ minutes) |
| Explicit Content Filter | Scan messages from all members |
| Default Notifications | Only @mentions |
| System Messages Channel | #server-log (staff only) |
| 2FA Requirement for Moderation | Enabled |

## Roles

Create the following roles in order (highest to lowest):

| Role | Color | Permissions | Assignment |
|------|-------|-------------|------------|
| **Instructor** | Gold (#F59E0B) | Administrator | Manual (instructor only) |
| **Teaching Assistant** | Purple (#8B5CF6) | Manage messages, mute members, create threads | Manual |
| **Cohort 1** | Blue (#3B82F6) | Send messages, embed links, attach files, use voice | On enrollment |
| **Cohort 2** | Green (#10B981) | Same as Cohort 1 | On enrollment |
| **Alumni** | Silver (#9CA3AF) | Send messages, embed links, view alumni channels | After cohort completion |
| **Self-Paced** | Teal (#14B8A6) | Send messages in self-paced channels only | On self-paced purchase |
| **Guest** | Gray (#6B7280) | View #announcements and #rules only | Default role |

## Bot Setup

### MEE6 (Moderation + Welcome)

1. Invite MEE6 from [mee6.xyz](https://mee6.xyz)
2. Configure:

**Welcome Message** (DM to new members):
```
Welcome to Production AI Systems!

Here's how to get started:

1. Read the #rules channel
2. Introduce yourself in #introductions (name, background, what you want to build)
3. Check #announcements for the latest course updates
4. If you're enrolled, you should have your cohort role — if not, message a TA

Course resources:
- Lab repos: github.com/[classroom-org]
- Office hours: Check #announcements for schedule
- Need help? Post in #technical-support

See you in class!
```

**Auto-Moderation Rules**:
- Block invite links from non-staff
- Warn on excessive caps (70%+ caps in messages over 10 chars)
- Warn on repeated messages (3 identical messages in 5 seconds)
- Log all moderation actions to #mod-log

### Carl-bot (Reaction Roles + Logging)

1. Invite Carl-bot from [carl.gg](https://carl.gg)
2. Set up reaction roles in #get-roles:

```
React to get your interest tags:

🤖 — AI Agents
📄 — RAG / Document AI
🔧 — MCP / Tool Integration
📊 — Dashboards / BI
🚀 — Deployment / DevOps
💼 — Looking for work
🏢 — Hiring
```

### Lab Submission Bot (Custom or Webhook)

For lab tracking, use a webhook-based approach:
1. Create a webhook in #lab-submissions channel
2. GitHub Classroom's autograder posts results via webhook
3. Format: `[Student] [Lab N] [Pass/Fail] [Score]`

## Verification Flow

1. New member joins and sees only #rules and #announcements
2. Member reads #rules and reacts with a checkmark emoji
3. MEE6 grants the Guest role (access to #general and #introductions)
4. Enrolled students receive their Cohort role via manual assignment or ConvertKit webhook integration
5. Cohort role unlocks all course channels

## Onboarding Checklist

When a new enrolled student joins:

- [ ] Assign appropriate Cohort role
- [ ] Verify they posted in #introductions
- [ ] Confirm they have GitHub Classroom access
- [ ] Confirm Codespace launches successfully
- [ ] Welcome them in the cohort channel

## Moderation Escalation

| Level | Action | Who |
|-------|--------|-----|
| 1 — Minor | Verbal warning via DM | TA or bot auto-warn |
| 2 — Repeated | Temporary mute (1 hour) | TA |
| 3 — Serious | 24-hour mute + instructor notification | TA → Instructor |
| 4 — Severe | Ban from server | Instructor only |

Bannable offenses (immediate):
- Harassment or hate speech
- Sharing course content outside the server
- Posting malware or phishing links
- Impersonating staff
