# Proposal: AI/Backend Engineer -- Clinic Call Automation (Twilio + MCP)

**Job URL**: https://www.upwork.com/freelance-jobs/apply/Design-Build-MVP-Call-Automation-for-Clinic-Twilio-MCP-Transcription_~022008350782733253644/
**Proposed Price**: $500 fixed
**Fit Score**: 8/10
**Date**: 2026-02-19

---

## Cover Letter

Hi,

I have hands-on experience with MCP (Model Context Protocol) integration and conversation context management -- the two core technical challenges in this project.

**Directly relevant experience**:

1. **MCP Integration**:
   - Built and configured MCP servers for CRM (GoHighLevel), database (PostgreSQL), caching (Redis), and browser automation (Playwright)
   - Production MCP workflows connecting AI agents to real-time business data
   - Experience with MCP tool schemas, server lifecycle, and error handling

2. **Conversation Context Preservation**:
   - Built a multi-agent handoff system that preserves full conversation context during agent transitions
   - Context objects include: conversation summary, intent classification, extracted data, and recommended next actions
   - Zero context loss during handoffs with 24-hour TTL on context objects

3. **Relevant Architecture** (for clinic call automation):
   - Twilio integration for voice + SMS channels
   - AI transcription pipeline (audio to text to structured data)
   - MCP-managed conversation state across call sessions
   - CRM sync for patient data (with PII encryption and compliance safeguards)

4. **Healthcare-Adjacent Compliance**:
   - PII encryption at rest (Fernet)
   - JWT authentication with rate limiting
   - Full audit trails for compliance
   - While not HIPAA-certified, the architecture follows HIPAA technical safeguards

**Milestone approach** (matching your two-milestone structure):
- **Milestone 1**: Architecture design document with MCP integration plan, data flow diagrams, and API specifications
- **Milestone 2**: Working MVP with Twilio call handling, MCP-managed context, and transcription pipeline

**Production proof**: 11 repos, 8,500+ tests, all CI green. I deliver production code, not prototypes.

Live demo of multi-agent orchestration: https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/

Available to start this week.

Best,
Cayman Roden
Portfolio: https://chunkytortoise.github.io

---

## READY-TO-SUBMIT-HUMAN

Copy the Cover Letter section above and paste into Upwork proposal form.

**Price**: $500 fixed (matches job budget)
**Milestones**: 2 (architecture + MVP)
**Connects needed**: Estimate 4-8
