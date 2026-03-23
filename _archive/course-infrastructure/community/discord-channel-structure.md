# Discord Channel Structure

Detailed channel list for the Production AI Systems Discord server.

## Channel Map

```
Production AI Systems
│
├── WELCOME
│   ├── #rules                    [read-only] Server rules and code of conduct
│   ├── #introductions            [all roles] Name, background, goals
│   ├── #announcements            [read-only] Instructor posts only
│   └── #get-roles                [all roles] Reaction roles for interest tags
│
├── COURSE
│   ├── #week-1-agentforge        [cohort+] Week 1 discussion: agent architecture
│   ├── #week-2-docqa             [cohort+] Week 2 discussion: RAG systems
│   ├── #week-3-mcp               [cohort+] Week 3 discussion: MCP integration
│   ├── #week-4-enterprisehub     [cohort+] Week 4 discussion: production hardening
│   ├── #week-5-insight-engine    [cohort+] Week 5 discussion: observability + testing
│   └── #week-6-deployment        [cohort+] Week 6 discussion: deployment + operations
│
├── HELP
│   ├── #technical-support        [cohort+] Setup issues, environment problems
│   ├── #code-review              [cohort+] Share code for peer/TA review
│   └── #office-hours             [cohort+] Questions for live office hours
│
├── LABS
│   ├── #lab-submissions          [read-only] Bot posts autograder results
│   ├── #lab-help                 [cohort+] TA + peer support for lab work
│   └── #showcase                 [all roles] Completed projects and demos
│
├── COMMUNITY
│   ├── #general                  [all roles] Open discussion
│   ├── #job-board                [all roles] Job postings, freelance leads
│   ├── #resources                [all roles] Articles, tools, tutorials
│   └── #off-topic               [all roles] Non-course conversation
│
├── ALUMNI (visible after cohort completion)
│   ├── #alumni-general           [alumni] Post-course discussion
│   ├── #alumni-projects          [alumni] Ongoing project collaboration
│   └── #alumni-referrals         [alumni] Job referrals and intros
│
├── VOICE
│   ├── voice-office-hours        [cohort+] Scheduled instructor sessions
│   ├── voice-study-group-1       [cohort+] Student-organized study sessions
│   └── voice-study-group-2       [cohort+] Student-organized study sessions
│
└── STAFF (hidden from students)
    ├── #staff-general            [staff] Internal coordination
    ├── #mod-log                  [staff] Bot moderation actions log
    └── #server-log               [staff] Join/leave/role change events
```

## Channel Details

### WELCOME Category

**#rules**
- Permissions: Read-only for all, write for Instructor only
- Pinned message with the full code of conduct (see `moderation-guidelines.md`)
- Slow mode: N/A (read-only)

**#introductions**
- Permissions: All roles can post
- Template pinned: "Hi! I'm [name], I'm a [role] at [company]. I'm taking this course because [reason]. I'm most excited about [topic]."
- Slow mode: 1 message per 5 minutes (prevent spam)

**#announcements**
- Permissions: Instructor and TA only
- Used for: session reminders, schedule changes, important deadlines, resource drops
- @everyone pings limited to 1/week max

**#get-roles**
- Permissions: All roles can react
- Contains the reaction role message (see discord-setup.md)

### COURSE Category

Each week channel follows the same pattern:
- Opens on Monday of that week (use Discord's scheduled events or manual role unlock)
- Pinned messages: Session recording link, lab instructions link, key resources
- Thread creation: Enabled (students create threads for specific topics)
- Slow mode: None

Channel naming convention: `#week-N-topic` where topic matches the repo name.

### HELP Category

**#technical-support**
- For environment setup issues (Codespace, Docker, Python, dependencies)
- TA responds within 4 hours during business hours
- Pinned: Common issues and solutions document

**#code-review**
- Students share code snippets or GitHub links for peer review
- TA provides feedback on at least 2 submissions per week
- Thread creation encouraged for multi-message reviews

**#office-hours**
- Students post questions before scheduled office hours
- Instructor picks top-voted questions to address live
- Upvote system: Students react with a thumbs-up to prioritize questions

### LABS Category

**#lab-submissions**
- Read-only channel for automated bot posts
- Format: `[Student Name] submitted Lab [N] — Score: [X/100] [PASS/FAIL]`
- Powered by GitHub Classroom autograder webhook

**#lab-help**
- Specific help for lab assignments
- TA response time: Within 2 hours during lab weeks
- Tag format: `[Lab N]` prefix for all messages

**#showcase**
- Students share completed projects with demos
- Encouraged format: Screenshot/GIF + brief description + GitHub link
- Staff reacts with a star emoji to highlight exceptional work

### COMMUNITY Category

**#general** — Open discussion about AI, engineering, career topics
**#job-board** — Job postings and freelance leads (staff-verified only)
**#resources** — Articles, tools, tutorials shared by community
**#off-topic** — Non-course conversation, memes, etc.

### ALUMNI Category

Unlocked when a student completes the cohort (5/6 labs submitted + final project).
- Persists across cohorts (all alumni share the same channels)
- Provides ongoing networking value that justifies course premium

### VOICE Category

**voice-office-hours**
- Scheduled: Thursdays after Session B for 30 min overflow
- Instructor and TAs present
- Push-to-talk not required (but recommended)

**voice-study-group-1 / voice-study-group-2**
- Always open for student-organized study sessions
- No staff presence required
- User limit: 10 per channel

### STAFF Category

Hidden from all non-staff roles.
- **#staff-general**: Coordination between instructor and TAs
- **#mod-log**: Automated moderation action logs from MEE6/Carl-bot
- **#server-log**: Join/leave events, role changes, audit trail
