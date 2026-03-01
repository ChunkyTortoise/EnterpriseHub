# AI Integration Strategy — The Jewkes Firm, LLC
**Prepared by Cayman Roden | February 2026**

---

## Executive Summary

- **What this covers:** A full AI and automation menu for a solo plaintiff PI/med mal practice — intake, client communication, record review, research, drafting, trial prep, and case closing.
- **Biggest problems solved:** Lead loss from after-hours calls · Demand letter time (5–15 hrs/demand) · Bar complaint risk from poor communication · Missed malpractice deadlines · Medical record review time.
- **How this works:** Each item below is standalone. Pick the ones that match your biggest pain points. There's no required order, no locked package, and no obligation to buy everything at once.
- **Time recovery:** The intake and communication tools alone recover an estimated **15–20 hours per week**.
- **Full-stack economics:** At average usage across all tools, expect approximately **$2,000–3,500/month** in subscriptions — roughly 30–40% of what a single full-time paralegal costs, while covering intake, communication, record review, research, drafting, trial prep, and case closing.
- **Where I'd start:** See the recommendation box at the top of Section 3.

---

## Table of Contents

- [Section 1: The Opportunity](#section-1-the-opportunity)
- [Section 2: What to Avoid (And Why)](#section-2-what-to-avoid-and-why)
- [Section 3: Tools by Problem Area](#section-3-tools-by-problem-area)
- [Section 4: What I Can Build For You](#section-4-what-i-can-build-for-you)
- [Section 5: Monthly Cost Reference](#section-5-monthly-cost-reference)
- [Section 6: Next Steps](#section-6-next-steps)

---

## Section 1: The Opportunity

Six months from now, The Jewkes Firm looks like this: potential clients who call at 11pm get an immediate response — qualified, documented, and scheduled — while you sleep. Your demand letters go out faster, backed by AI-organized medical records that would have taken two weeks to manually review. Clients stop calling to ask "what's the status?" because they already know, with your firm's branded app on their phone. You recover 15–20 hours per week that used to go to intake calls, record review, and drafting boilerplate. AI intake tools consistently drop response time to under 30 seconds; firms using them report 15–25% increases in retained cases from faster contact with leads who would otherwise hit voicemail and disappear (Smith.ai published data, 2024). Firms using AI-assisted demand drafting report 20–30% higher settlements, driven by better-organized medical narratives and fewer missed treatment events (EvenUp firm outcome data, 2024). This isn't hypothetical. The tools exist today, they're priced for solo practitioners, and most Georgia plaintiff attorneys haven't touched them yet. The competitive window for early adopters is real — but the more practical case is simpler: these tools solve specific, expensive problems in a solo PI practice, and most of them pay for themselves on a single case.

> **The defense side has been on this stack for two years.**
>
> The tools in this document — Clio, Case Status, EvenUp, Supio, litigation analytics — have been standard infrastructure at well-run defense firms and insurance carrier litigation departments since 2022–2023. AI-assisted record review, deposition analytics, and litigation intelligence tools aren't new to the attorneys your cases are up against. This isn't about catching up to other plaintiff firms who've adopted AI. It's about reaching parity with the defense side that's been using these tools against plaintiff attorneys for two years — and then using your knowledge of how they think to flip those same tools into a plaintiff's advantage.

---

## Section 2: What to Avoid (And Why)

Before I recommend what to use, here's what to stay away from.

---

**Consumer ChatGPT or Claude for Case Work**
Do not use OpenAI or Anthropic's consumer tools to analyze case facts, draft strategy memos, or process privileged communications. Citation hallucination rates run 17–34% in general models. More critically, Georgia Rule 1.6(c) requires attorneys to take "reasonable measures to prevent the inadvertent or unauthorized disclosure of, or unauthorized access to, information relating to the representation." ABA Opinions 477 and 512 apply this duty directly to AI tool selection. Consumer AI tools, which train on user inputs and do not offer BAAs, do not meet that standard for privileged client communications. Use purpose-built legal tools (EvenUp, Supio, CoCounsel) that operate under BAAs and legal-specific data handling agreements.

---

**Full Automation of Client-Facing Communication**
Settlement discussions, strategy updates, bad news conversations, and anything involving case outcomes must involve you directly. Automation handles the routine. You handle the relationship. ABA Opinion 512 and the Georgia Rules are explicit: attorneys cannot automate substantive legal advice, settlement discussions, or client termination decisions. Case Status is configured to never trigger on those events — that's a deliberate configuration, not a default.

---

**Perplexity Legal / General AI for Legal Research**
General-purpose AI tools (Perplexity, consumer ChatGPT, Google AI) are dangerous for binding legal research. No closed-universe citation verification, no guaranteed hallucination detection. A case fabricated by AI that goes into a filing is a Rule 3.3 violation and a potential *Mata v. Avianca*-level sanctions event. Use CoCounsel (Westlaw-grounded) or Fastcase for any research that affects filings.

---

**Harvey AI**
Harvey is excellent. It's also priced for AmLaw 100 firms. A solo PI practice doesn't have the volume or budget to justify Harvey's pricing when EvenUp and CoCounsel accomplish most of the same tasks at a fraction of the cost.

---

**Custom RAG Systems (Enterprise Scale)**
A custom-built AI system trained on your full case files sounds appealing. The reality: $25K–50K to build, ongoing maintenance costs, and hallucination risks that require constant monitoring. EvenUp and Supio already do this better than a custom build for their specific functions. Section 3's RAG items are targeted, single-purpose deployments on specific document sets — scoped at $800–2,500, not $25K. That's a different animal.

---

**Westlaw Edge Litigation Analytics / Lexis+ AI**
Both are enterprise-priced ($300+/mo) for research capabilities that Fastcase + CoCounsel cover at a fraction of the cost. For Georgia state court litigation analytics specifically, Trellis is already in the stack at a solo-friendly price point.

---

**AI for Unverified Judicial Filings**
*Mata v. Avianca* resulted in sanctions against attorneys who submitted AI-generated briefs with fabricated citations. Courts are watching. Every AI-assisted document going to a tribunal requires citation verification through a traditional citator and attorney certification. No exceptions.

---

### What This Proposal Does NOT Cover

These are known items outside the current scope — each can be addressed in future phases:

- **E-filing automation** — Georgia county-specific filing systems vary significantly; evaluate after Clio is fully configured.
- **Virtual paralegal / staffing recommendations** — can be addressed separately once you know what the automation covers.
- **Physical mail and service of process tracking** — outside the scope of this engagement.
- **Firm website redesign** — Intaker handles chat capture; site design is a separate engagement.
- **Billing and collections automation** — Clio handles invoicing; collections strategy is outside this scope.

---

## Section 3: Tools by Problem Area

> **If you only do one thing after this conversation — do this:**
>
> **Set up Clio Grow + Smith.ai.** Every other tool in this document connects to Clio. And every call that hits voicemail after hours is a lead you've already lost — invisibly, with no record that it happened. Clio gives you the foundation everything else feeds into. Smith.ai fills the after-hours gap and puts qualified leads into your pipeline while you sleep. Together they're the highest-ROI move in the stack because they recover revenue you're currently losing on cases you never knew you missed.
>
> **Cost: ~$370/mo. Timeline: 2–3 weeks to your first captured after-hours lead.**
>
> Everything else in Section 3 is what you add once that foundation is running. Pick by your biggest pain point:
>
> | Your Biggest Problem | Start Here |
> |---------------------|------------|
> | Losing leads after hours | Smith.ai + Clio Grow → Section 3.1 |
> | Demand letters taking 5–15 hours | EvenUp → Section 3.3 |
> | Clients calling, bar complaint risk | Case Status → Section 3.2 |
> | Missed SOL/ante litem/deadlines | Deadline Automation → Section 3.5 |
> | Medical record review taking weeks | Supio → Section 3.3 |
> | Don't know what a case is worth at intake | CaseYak + Trellis → Section 3.6 |
> | Use your defense background as a weapon | EvenUp + Trellis + Low Offer Response → Sections 3.3, 3.6, 3.9 |

---

### The Proprietary Layer — Custom AI Builds

*This is where the original conversation started. Every tool in the rest of this section is an off-the-shelf subscription — good tools you can sign up for directly. The items below are different: AI systems I build specifically for your practice, using your cases, your experts, your venues, and your arguments as the training material. They don't exist before I build them, and they compound in value over time. They're the reason to hire a consultant rather than just reading the Clio sales page.*

These are fixed-cost builds with minimal ongoing running costs — not subscriptions. If you're evaluating where to start, read this section first to understand what a consultant-built stack adds beyond a DIY tool subscription — then jump to whichever problem area below costs you the most right now.

---

#### AI Legal Assistant | OpenClaw

**What it is:** OpenClaw is an AI legal assistant I built for plaintiff law firms. It's a configurable AI layer trained on your firm's knowledge base — your intake criteria, your case types, your jurisdiction-specific procedures, your standard FAQ answers — and it responds to client and internal queries in your voice, on your terms.

**What it solves for you:** Your clients message with the same questions every day — "How long will my case take?" "What do I need to bring to the consultation?" "Will this go to trial?" "Has anything happened on my case?" Right now those questions go to you or sit unanswered. OpenClaw handles them without staff involvement, with answers that match your firm's actual approach and language. Pre-consultation, it gives Jordan a structured intake summary of what the client has already shared — so the first call is about the case facts, not collecting basic information.

**Longer term:** As more of your workflow runs through it, OpenClaw becomes a queryable firm knowledge layer — intake history, procedure references, and communication templates that new matters pull from automatically. The more cases you run through it, the more useful it gets.

**Tool:** OpenClaw
**Monthly cost:** ~$50/mo
**Complexity:** Medium — initial configuration to your practice, voice, and case types required.
**Speed to value:** 3–4 weeks — first client FAQ handled automatically.

*Disclosure: OpenClaw is a product I built. I recommend it here because I believe it fits — weigh that conflict accordingly.*

---

#### Expert Witness Testimony Database | Custom RAG

Searchable database of deposition transcripts from Georgia defense medical experts — indexed by expert, specialty, and case type. Ask: *"What has Dr. Henderson testified about causation in cervical disc herniations from rear-end collisions?"* and get specific prior testimony, internal contradictions, and methodology weaknesses, with source citations.
Every transcript added compounds the value. After two years, Jordan has proprietary intelligence on his market's defense experts that no other plaintiff attorney across his three-county footprint has.
**Build:** Claude API + vector database + web query interface | **Build cost:** ~$1,500–2,500 (one-time) | **Running cost:** ~$10–30/mo

---

#### Personal Case Library RAG | Custom RAG

Jordan's own demand letters, mediation briefs, and settlement memos — indexed and queryable by case type, injury, venue, and outcome. Query your own best language and arguments back to you when starting a new similar matter.
**Build cost:** ~$800–1,500 (one-time) | **Running cost:** ~$10–20/mo | *Documents stripped of identifying client information before indexing.*

---

#### Medical Literature RAG for Med Mal | Custom RAG

Clinical guidelines and standard-of-care literature for Jordan's med mal and dental mal case types (ACOG, ACS, ACEP, ADA guidelines; Cochrane reviews; expert treatises) — indexed and queryable. Know the standard of care before the first call with an expert.
**Build cost:** ~$1,000–2,000 (one-time) | **Running cost:** ~$10–20/mo

---

#### Per-Case Document Querying | NotebookLM (Free)

Upload up to 50 non-PHI case documents per notebook (police reports, court filings, contracts, correspondence) and query in plain English with cited source answers.
**Tool:** NotebookLM (free) | **HIPAA caveat:** Do not upload identifiable medical records. Anonymize first. I set up this protocol during onboarding.

---

#### Georgia Pattern Jury Instructions RAG | NotebookLM (Free)

Georgia PJIs indexed in NotebookLM — query the right instruction instead of navigating the full index. *"What is the Georgia charge for sudden emergency doctrine?"*
**Tool:** NotebookLM (free) | *I set up the notebook during onboarding.*

---

### 1. Intake & Lead Capture

*The problem: leads call after hours, hit voicemail, and hire the next attorney who picks up.*

---

#### AI Intake + CRM | Smith.ai + Clio Grow

**What it is:** Smith.ai is an AI + human hybrid receptionist service. Their AI handles the initial greeting, runs through intake questions, and hands off to a live receptionist for complex or sensitive conversations. Every call — regardless of when it comes in — is answered, qualified, and documented. Clio Grow is the CRM layer: it manages leads, automates follow-up sequences, and feeds structured intake data directly into your case management system.

**What it solves for you:** Right now, every call that hits voicemail after hours is a lead you've lost. Smith.ai answers the phone in under 30 seconds, runs through your intake questions (accident date, injury type, whether they've spoken to a lawyer, contact info, liability indicators), flags high-value leads, and syncs the data to Clio automatically. There's no call log to manually review in the morning — the lead is already in your pipeline with a follow-up task waiting. Clio Grow's intake forms capture web inquiries the same way, so no lead falls through the cracks regardless of channel.

**Why hybrid over pure AI:** A solo PI practice spans auto wrecks, truck wreck cases, slip-and-falls, wrongful death, and medical and dental malpractice. The complexity of your intake — especially med mal and dental mal, where statute of limitations and standard of care questions come up immediately — benefits from human judgment on complex calls, not just scripted AI. Smith.ai's model gives you speed without sacrificing quality on the calls that matter most.

**Tool:** Smith.ai Virtual Receptionist + Clio Grow
**Monthly cost:** Smith.ai ~$285/mo (50-call plan) + Clio Grow included in Clio Advanced subscription
**ROI:** AI intake recovers 15–20 hours per week of lost lead-contact time — every call that would have gone to voicemail now converts.
**Complexity:** Medium — requires configuration of intake scripts, call routing rules, and Clio pipeline stages.
**Speed to value:** 2–3 weeks — first captured after-hours lead.

**Ethics/Risk:**
Smith.ai's live receptionist component is bound by your firm's confidentiality requirements. Every Smith.ai call must be disclosed as intake assistance, not legal advice — their agents are trained to stay in scope. Clio Grow uses a signed Business Associate Agreement (BAA) for HIPAA compliance.

---


**Intake receptionist alternatives compared:**

| Option | Model | Cost | Best For |
|--------|-------|------|----------|
| **Smith.ai** *(recommended)* | AI + human hybrid | ~$285/mo | Complex PI/med mal; calls needing human judgment |
| Ruby Receptionists | Human-only | ~$235–360/mo | Brand-focused; less automation |
| Answer1 | Human-only | ~$160–285/mo | Lower volume; fewer integrations |
| Clio Grow alone | Web forms only | Included in Clio | No live call coverage |

*For a practice spanning auto wrecks, med mal, and dental mal, the hybrid model matters — calls that immediately surface SOL questions or standard-of-care facts benefit from human judgment, not just a script.*

---

#### Website AI Chat + Lead Capture | Intaker

**What it is:** Intaker is a PI-specific AI chat widget for your firm's website. Built exclusively for plaintiff personal injury practices, it walks website visitors through structured intake questions matched to your case types, operates 24/7 without staff involvement, and pushes qualified leads directly into Clio Grow with intake data attached.

**What it solves for you:** Smith.ai handles phone calls. Intaker handles the website visitor who lands at 2am and never calls. These are different people at different stages: phone callers are ready to talk; website visitors are often still deciding whether they have a case. Intaker captures them with a conversational intake experience before they click away to a competitor. A solo firm with no staff has exactly one intake channel covered without it — the phone. Search traffic, paid ads, and organic visitors all land on the website and currently go uncontacted unless they dial.

**Tool:** Intaker
**Monthly cost:** ~$80/mo
**ROI:** If Intaker captures one additional viable case per quarter from website traffic that would otherwise have bounced, it pays for itself many times over against a $30K+ average PI settlement.
**Complexity:** Easy — installs as a website widget. I configure intake question flows per case type and connect the Clio Grow integration.
**Speed to value:** Days — widget installs same day; fully configured in under a week.

**Ethics/Risk:**
The chat interface must identify itself as an automated intake tool, not a human attorney. Intaker is configured to qualify facts and schedule a consultation, not answer questions about case merit or legal strategy.

---

#### Referral Network Management | Clio Grow

Systematic tracking of referral sources (chiropractors, ER physicians, body shops, attorneys) with automated thank-you workflows, case outcome updates, and referral source ROI tracking — all within Clio Grow.
For a solo PI attorney, referral relationships are the #1 case source; this makes them systematic and compounding rather than ad hoc.
**Tool:** Clio Grow (in stack if Clio is already active) | **Cost:** $0 incremental

---

### 2. Client Communication & Compliance

*The problem: failure to communicate is the #1 cause of bar complaints nationally.*

---

#### Client Communication | Case Status

**What it is:** Case Status is a client communication platform that gives each of your clients a branded mobile app for The Jewkes Firm. Clients see their case status in real time, receive automated milestone updates, and communicate with your office through a single channel. The platform includes 138-language AI translation, NPS tracking to measure client satisfaction, and automated Google review requests after case resolution.

**What it solves for you:** Failure to communicate is the number one source of bar complaints nationally. Clients don't leave attorneys because cases settle small — they leave (and file complaints) because they feel ignored. Case Status handles every routine touchpoint automatically: filing confirmations, discovery updates, deposition scheduling, settlement offer notifications. Clients who have the app stop calling your cell phone to ask "what's happening with my case?"

**The treatment check-in workflow:** One of the highest-value configurations I build into Case Status is a weekly treatment check-in: the system automatically sends a text — "Hi [Name], how was your pain level this week? Have you attended all your PT appointments?" The client's reply is timestamped and documented in the case file. A client's text saying "pain is still 7/10, had to miss PT Tuesday because I couldn't drive" is contemporaneous damages evidence that strengthens your demand. This is a billable workflow configuration, not a feature you set up in ten minutes — but once it's running, it generates documentation automatically on every active case.

**What Case Status won't automate:** Settlement negotiations, case strategy updates, bad news conversations, and any communication involving legal judgment must come from you directly. I build explicit guardrails into the platform: the automation is configured to never trigger on settlement-stage cases.

**Tool:** Case Status
**Monthly cost:** ~$99–149/mo
**ROI:** Case Status prevents the #1 cause of bar complaints nationally — and generates contemporaneous damages evidence on every active case through the treatment check-in workflow.
**Complexity:** Easy to medium — configuration required, no ongoing technical management.
**Speed to value:** 2 weeks — full client app rollout with milestone automation active.

---

#### AI Ethics Policy | Attorney Time

**What it is:** A written AI use policy for your firm, plus updated language in your engagement letter disclosing AI tool use to clients.

**What it solves for you:** Georgia has no official AI-specific bar guidance yet — but the ABA issued Opinion 512 in 2024, which establishes the framework most state bars will follow. Getting your policy in place now means you're ahead of the curve when Georgia does act, and you're protected if a client ever questions your use of these tools.

**Tool:** No third-party tool needed — I draft this for you.
**Monthly cost:** $0 (one-time setup)
**ROI:** Malpractice protection and bar compliance aren't line items — they're the foundation everything else sits on.
**Complexity:** Easy — review and approve language I draft for you.
**Speed to value:** 3–5 days.

**Ethics/Risk:**
ABA Opinion 512 requires attorneys to: (1) understand the AI tools they use, (2) supervise AI output, (3) maintain client confidentiality, and (4) disclose AI use when material to the representation. This policy covers all four.

---

#### Firm Technology Security Setup | Configuration Work

**What it is:** Security configuration across all firm accounts — not a subscription, just foundational setup work.

**What it solves for you:** MFA across every firm account (Clio, email, AI tools, cloud storage). Encrypted email configuration for privileged client communications. A written information security plan (Georgia Rule 1.1 competence extends to technology security). Password manager setup for the firm. None of this requires a new subscription — it's configuration that should happen before client data moves through any AI tool.

**Tool:** No subscription required — configuration work only.
**Monthly cost:** $0
**ROI:** A data breach involving privileged client communications is a bar complaint, a malpractice claim, and a reputational event.
**Complexity:** Easy — I configure, document, and walk you through it.
**Speed to value:** 2–3 days.

---

### 3. Demand Letters & Record Review

*The problem: demand letters take 5–15 hours and medical records take weeks to organize.*

---

#### AI Demand Letters | EvenUp

**What it is:** EvenUp is an AI platform built specifically for plaintiff personal injury attorneys. You upload medical records, bills, and incident documentation. EvenUp analyzes the records and produces a structured demand letter — organized by treatment chronology, supported by the right records, and formatted to maximize insurer response.

**What it solves for you:** Demand letter drafting is one of the most time-intensive tasks in a PI practice — attorneys report spending 5–15 hours per demand. EvenUp cuts that to minutes and organizes medical records in ways that support higher settlement values by ensuring nothing gets buried or missed. Their AI (Piai) is trained on over 250,000 verdicts and settlements.

You already know from the defense side what a well-organized demand looks like versus one that gives adjusters room to discount. EvenUp closes that gap on every case — not just the ones where you have time to be meticulous.

**One important caveat on Georgia venues:** EvenUp's settlement valuations are most accurate in data-dense jurisdictions like Fulton and DeKalb counties. For cases in Fayette, Coweta, Spalding, and Troup counties — where the bulk of your client base falls across your Tyrone, Griffin, and LaGrange offices — the dataset is sparser and valuations should be treated as directional, not definitive. Human judgment on rural Georgia case values still matters; EvenUp is a starting point, not a ceiling.

**Tool:** EvenUp
**Monthly cost:** $300–800 per demand (varies by case complexity — no subscription required)
**ROI:** Firms using EvenUp report 20–30% higher settlements from better-organized medical narratives and fewer missed treatment events.
**Complexity:** Easy — upload records, review output, customize, send.
**Speed to value:** First demand — immediate time savings on the first case you run through it.

**Ethics/Risk:**
Attorney review of every demand before it goes out is non-negotiable. EvenUp produces a draft, not a final work product. Some adjusters have started flagging AI-generated demands — human review and customization is what mitigates that risk and ensures the letter sounds like you, not a template.

---


**Demand letter tool alternatives compared:**

| Option | Cost | Best For | Limitation |
|--------|------|----------|------------|
| **EvenUp** *(recommended for high-value/med mal)* | $300–800/demand | Complex PI/med mal; high-value cases | Sparser rural Georgia venue data |
| Precedent | $100–275/demand | Straightforward soft-tissue auto cases | Less depth on med mal |
| Manual | Attorney time only | Full control; custom voice | 5–15 hrs per demand |

*EvenUp and Precedent aren't mutually exclusive — many firms use Precedent for routine soft-tissue auto cases and EvenUp for complex med mal and high-value matters. A reasonable cost management strategy if volume justifies both.*

---

#### Medical Record Review | Supio

**What it is:** Supio is an AI platform designed specifically for plaintiff attorneys to analyze medical records. It reads through hundreds of pages of records, identifies relevant treatment events, flags inconsistencies, and summarizes findings by injury type, causation, and damages. The platform is built for med mal complexity — it identifies deviations from standard of care, gaps in care, and contradictions across multiple providers' notes.

**What it solves for you:** Medical record review is where PI and med mal cases are won and lost, and it currently takes weeks. Supio reduces that to hours and surfaces things a manual review might miss — a missed diagnosis, a gap in treatment, a record that strengthens causation. Firms using Supio report 90% faster case prep and 30% higher average settlements. One firm saved 437 hours across just six cases.

**Tool:** Supio
**Monthly cost:** ~$500–1,000/mo (volume-based)
**ROI:** Supio is a capacity multiplier — take more cases at the same quality level. Two weeks of record review down to 20 minutes applies to every PI and med mal matter in the pipeline.
**Complexity:** Medium — integration with your record management process required.
**Speed to value:** First case — two weeks of record review down to 20 minutes immediately.

**Ethics/Risk:**
Supio is built for legal use with 97%+ verified accuracy and source linking on all outputs. Attorney supervision of all flagged findings is required — the tool surfaces issues, you decide what they mean for the case.

---


**Medical record review alternatives compared:**

| Option | Cost | Best For | Limitation |
|--------|------|----------|------------|
| **Supio** *(recommended)* | $500–1K/mo | Volume PI/med mal; complex causation; dental mal | Subscription model; requires volume to justify |
| CaseMetrix | Quote (enterprise) | High-volume plaintiff firms | Enterprise-priced; overkill for solo |
| Manual (attorney/paralegal) | Time cost | Full control | Weeks per case; prone to missed events |

---

#### Medical Bill Auditing | OrbDoc + Superinsight.ai

**What it is:** Reviewing the actual billing codes for errors — upcoding, unbundling, duplicate charges, CPT/ICD-10 mismatches — that inflate bills inaccurately or miss legitimate billable treatment that's been under-coded. Studies consistently find errors in 80–90% of medical bills.

**What it solves for you:** Two distinct problems on every case. First, on the lien side: inflated charges that Medicare and health insurers use to justify larger liens need to be identified and challenged — and Jordan has personal liability if a Medicare lien isn't addressed correctly. Second, on the damages side: under-coded or missed billing categories understate the client's economic damages, which flows directly into EvenUp's demand calculation.

**Tools:**
- **OrbDoc** (free) — compares bills against 3.3 million Medicare rules and NCCI edits. Upload the bill, get a flag report on unbundling, upcoding, and duplicates instantly.
- **Superinsight.ai** — PI-specific platform combining AI bill analysis with medical record cross-referencing. HIPAA compliant. Pricing requires contact; free trial available. **My recommendation: start with OrbDoc on your first several cases. If bill auditing proves consistently high-value, Superinsight.ai warrants a free trial — but evaluate on your own cases before committing.**

**Monthly cost:** $0 for OrbDoc; Superinsight.ai pricing on request
**ROI:** A single identified upcoding error that reduces a provider lien by $15,000 more than pays for years of service.
**Complexity:** Zero for OrbDoc — upload bills, read the report.
**Speed to value:** Same day — upload a bill, get results in minutes.

---

### 4. Case Management & Document Automation

*The problem: producing the same 10–15 document types over and over from scratch.*

---

#### Practice Management + Document Automation | Clio Advanced + Clio Draft

**What it is:** Clio Advanced ($119/mo) is the practice management foundation — case management, deadline calendaring, document management, billing, and the Clio Grow CRM (included). Clio Draft adds document automation: template-based generation that auto-populates client data, case details, and court-specific forms from your Clio case files.

**What it solves for you:** Every solo PI practice produces the same 10–15 document types repeatedly — retainer agreements, HIPAA authorizations, LORs, spoliation letters, discovery responses, status letters. Clio Draft automates the fill-in work. Templates are built once; subsequent documents pull from the case file automatically.

**Tool:** Clio Advanced ($119/mo) + Clio Draft (add-on, ~$49–$79/mo)
**Monthly cost:** ~$168–198/mo combined
**ROI:** If you produce 15 documents per case and Clio Draft cuts each to five minutes from thirty, you recover multiple hours per case on a straightforward matter.
**Complexity:** Medium — template setup required upfront, straightforward once configured.
**Speed to value:** 3–4 weeks — first auto-generated document from a template.

**Gavel — upgrade option if needed:**
If your practice's document variety demands more — different retainer clauses for auto wrecks vs. med mal, different HIPAA auth language by case type — Gavel (formerly Documate) adds rule-based conditional logic that Clio Draft's native fields can't match. Cost is ~$99/mo. My recommendation: implement Clio Draft first, test it across your case types for 30–60 days, then evaluate whether Gavel's conditional branching solves a problem you're actually hitting.

**Ethics/Risk:**
Attorney review of all generated documents is required before they go to clients or opposing counsel.

---


**Practice management platform alternatives compared:**

| Option | Cost | Strengths | Limitation |
|--------|------|-----------|------------|
| **Clio Advanced** *(recommended)* | $119/mo | Broadest legal tech integration ecosystem; strongest PI/med mal support | Higher cost than alternatives |
| MyCase | $89/mo | Budget-friendly; simpler UI | Fewer AI integrations |
| Smokeball | $99–149/mo | Auto-fill time tracking; document focus | Less CRM depth |
| Filevine | $65+/mo/user | High-volume plaintiff firm feature set | Steeper learning curve; overkill for solo |

*The integration argument for Clio is the strongest differentiator here: Smith.ai, Case Status, EvenUp, Supio, LawPay, and most tools in this stack have pre-built Clio integrations. Alternatives require more custom plumbing.*

---

#### Trust Accounting + IOLTA Compliance | Clio + LawPay

**What it is:** Full configuration of Clio's trust accounting module plus LawPay integration for compliant IOLTA management — account reconciliation automation, compliance monitoring, and disbursement tracking.

**What it solves for you:** Trust account violations are among the most common grounds for bar discipline in Georgia. Georgia Bar Rule 1.15 governs every dollar that moves through your IOLTA account. This configuration makes reconciliation systematic and automated, maintains an audit trail for every disbursement, and flags discrepancies before they become compliance issues.

**Tool:** Clio Advanced (already in stack if you have it) + LawPay (~$0–49/mo)
**Monthly cost:** ~$0–49/mo incremental
**ROI:** One avoided trust accounting violation is worth more than years of service cost.
**Complexity:** Medium — Clio trust module requires configuration; LawPay setup is straightforward.
**Speed to value:** 2 weeks — first reconciled IOLTA period.

---

#### Discovery Automation | Briefpoint

**What it is:** Briefpoint automates the drafting of discovery documents — interrogatories, requests for production, requests for admission — based on your case facts and prior discovery templates. Cuts drafting time by up to 95%.

**Tool:** Briefpoint
**Monthly cost:** ~$99/mo (solo plan)
**ROI:** If Briefpoint cuts 3 hours of discovery drafting per case, it pays for itself on the first case of the month.
**Complexity:** Easy — template-based, minimal configuration.
**Speed to value:** First discovery set you draft.

---

### 5. Deadline & Compliance Automation

*The problem: malpractice exposure from missed SOL deadlines, ante litem notices, and spoliation windows.*

---

#### Full Litigation Deadline Management | Clio Automation

Automated workflow on every new lead: conflict check, SOL deadline (PI: 2 years; med mal: 2-year discovery/5-year outer; minors: tolled to 18 + 2 years), ante litem notice (6 months for counties/municipalities; 12 months for State — jurisdictional, not procedural), plus the full litigation calendar: discovery response deadlines (30 days Georgia), motion hearing dates, expert disclosure deadlines, pre-trial order deadlines, and mediation deadlines. All with escalating 7/14/30-day calendar reminders.
Catastrophe insurance — one missed SOL is a malpractice claim, one missed ante litem is a permanent bar to recovery, and one missed discovery deadline can cost you the case.
**Tool:** Clio automations (in stack) | **Cost:** $0 incremental once Clio is configured
*Georgia-specific logic built for all defendant classes including government entities.*

---

#### Spoliation Letter Automation | Clio + AI

Clio trigger on new matter creation generates a customized spoliation letter per defendant type (individual, corporate, trucking, hospital, government entity) in Jordan's queue within minutes of case opening.
Preservation letters need to go out within 72 hours — automating the draft ensures the window is never missed even when Jordan is the only person in the firm.
**Tool:** Clio + AI (both in stack) | **Cost:** $0 incremental

---

#### Lien Tracking + Resolution Assistant | Clio + AI

Tracks all outstanding liens (Medicare, Medicaid, ERISA, provider), calculates running net-to-client at different settlement amounts, and auto-drafts negotiation and waiver letters.
Makes lien management systematic and correspondence automatic — critical given Jordan's personal liability exposure for missed Medicare liens.
**Tool:** Clio custom fields + AI drafting | **Cost:** $0 incremental | **Complexity:** High — builds on a custom Clio lien registry structure.

---

### 6. Legal Research & Case Intelligence

*The problem: research takes hours; you don't know what the case is worth until deep into it.*

---

#### AI Legal Research | Fastcase + CoCounsel

**What it is:** Fastcase is a legal research platform available free to all Georgia Bar members. CoCounsel (by Thomson Reuters) adds an AI layer that answers legal questions in plain language, drafts research memos, verifies citations, and can analyze uploaded documents including deposition transcripts.

**What it solves for you:** Research speed and coverage. CoCounsel can answer complex procedural questions, find analogous cases, and produce structured memos in a fraction of the time traditional research takes. For trial prep specifically: feed CoCounsel the complaint, answer, and key medical records and ask for a cross-examination outline targeting the defense's medical expert. This turns CoCounsel from a research tool into a trial prep tool — and it's a workflow I build into your training.

**Tool:** Fastcase (free via Georgia Bar) + CoCounsel ($65/mo)
**Monthly cost:** $0–65/mo
**ROI:** One hour of research time saved per week pays for CoCounsel in a month.
**Complexity:** Easy — both tools are designed for attorney use with minimal setup.
**Speed to value:** Days — first research query returns results immediately.

**Ethics/Risk:**
Citation verification through a traditional citator (Shepard's, KeyCite) is still required before any AI-generated citation goes into a filing. This is a Georgia Rule 3.3 issue.

---

#### Georgia Litigation Analytics | Trellis

**What it is:** Trellis indexes Georgia state court dockets and provides litigation intelligence specific to your venues: judge ruling patterns, opposing counsel tendencies, historical outcomes by case type, motion outcomes, and venue-level settlement data.

**What it solves for you:** Knowing how a specific Fayette County judge has ruled on summary judgment motions in PI cases, or how often a particular defense firm takes cases to trial vs. settling early, is strategic information that's currently locked in court records. A 20-minute Trellis search before filing tells you things about your judge that would take hours of manual research to find. You already know how defense firms think — Trellis adds the data layer that tells you exactly which firms in your venues are bluffing about trial readiness and which ones aren't.

**Tool:** Trellis
**Monthly cost:** ~$79–149/mo
**ROI:** One better-informed strategic decision per case — venue selection, pre-trial motion timing, settlement hold-out — justifies the monthly cost many times over.
**Complexity:** Easy — search interface, no configuration required.
**Speed to value:** Days — first Trellis search before a filing.

---

#### MVA Settlement Value Intelligence | CaseYak

Free AI settlement value predictor for motor vehicle accident cases. Enter the injury type, liability facts, and jurisdiction — get a settlement value range. Useful at intake to triage whether a case justifies the time investment before Supio's full medical analysis is complete.
**Tool:** CaseYak | **Monthly cost:** $0
*For internal intake triage only — do not share projections with clients as settlement predictions.*

---

#### Expert Witness Discovery + Vetting | Expert Institute

**What it is:** Expert Institute is a platform with over 1 million vetted experts across every specialty. Their **Expert Radar** AI tool analyzes a specific expert's complete litigation history — prior depositions, testimony transcripts, Daubert challenges, published opinions, and court decisions.

**High-value applications:**
- *New expert discovery*: specialty-specific search for med mal and dental mal cases requiring niche expertise — neuroradiology, hospital credentialing, OB/GYN standard of care, emergency medicine, oral and maxillofacial surgery, dental standard of care
- *Opposing expert vetting*: Expert Radar pulls everything on record about the defense's medical expert — known causation positions, prior Daubert challenges in Georgia and federal courts, internal contradictions across prior testimony
- *Certificate of merit preparation*: identify experts available for cert of merit before filing

**Tool:** Expert Institute / Expert Radar
**Monthly cost:** Quote-based; contingency-friendly billing available for plaintiff PI firms
**ROI:** One successfully identified Daubert vulnerability changes a case outcome. One correctly matched plaintiff expert avoids a dismissal.
**Complexity:** Low — Expert Institute's team handles the research.
**Speed to value:** First case — Expert Radar pulls a full profile on demand.

---

### 7. Investigation

*The problem: locating defendants, finding insurance layers, and tracking witnesses manually.*

---

#### Skip Tracing + Insurance Discovery | Tracers / TLOxp

**What it is:** AI-powered investigative data platforms that locate defendants, identify insurance carriers, find witnesses, and research assets — drawing from 120+ billion records across address history, phone numbers, employment, social media, criminal records, and insurance data.

**Practical applications:**
- *Auto/truck wreck*: locate uninsured defendants, find employer records for commercial vehicles, identify umbrella and commercial auto carrier layers
- *Premises liability*: locate property owners, LLC registered agents, and insurance carriers behind shell entities
- *Med mal*: locate departing physicians, identify hospital credentialing records and coverage history
- *Wrongful death*: locate heirs, estates, and insurance policies for damages recovery

**Tools:** Tracers (~$39/mo) · TLOxp (~$50–150/mo) for deeper asset and insurance data
**Monthly cost:** ~$39–150/mo depending on search volume
**ROI:** On a single truck wreck case, identifying the employer's commercial carrier rather than the driver's personal policy is the difference between a policy-limits recovery and a significant judgment.
**Complexity:** Zero — search interface with instant results.
**Speed to value:** Immediate — first search returns results in seconds.

**Ethics/Risk:**
Permissible use under Gramm-Leach-Bliley Act and FCRA for litigation purposes. Do not use results to make direct unsolicited contact with prospective clients in violation of Georgia Bar Rule 7.3.

---

#### Social Media Evidence + Client Monitoring | AI + Protocol

At case opening, documents all publicly available social profiles for opposing parties; at engagement, flags the client's public posts that could undermine the case before the defense finds them.
Defense firms routinely search plaintiff social media — this workflow ensures Jordan sees it first.
**Tool:** AI (in stack) + documented protocol | **Cost:** $0
*Public content only — absolute compliance with Georgia Bar Rules on deceptive evidence collection.*

---

### 8. Trial Preparation

*The problem: Jordan tries cases — prep is time-intensive and high-stakes.*

---

#### Deposition Capture + AI Transcripts | Skribe

**What it is:** Skribe provides AI-assisted digital deposition capture, replacing traditional court reporters at a fraction of the cost. A qualified live captionist monitors in real time while AI verifies and indexes the transcript — at ~$349/hr for live depositions vs. $350–500/hr plus $500–1,500 in per-page transcript fees for traditional reporters.

**What it solves for you:** Skribe cuts the all-in deposition cost roughly in half while delivering searchable, timestamped transcripts synced to video. Every statement is timestamped to the corresponding video frame — when you need to find what a defense expert testified about causation in prior depositions, you search instead of flipping pages.

**Tool:** Skribe
**Cost:** Starting at ~$349/hr live capture. No monthly subscription — pay per deposition.
**ROI:** On a complex med mal with five depositions, savings vs. traditional court reporters can exceed $2,000–4,000 per case.
**Complexity:** Low — Skribe manages the technical setup.
**Speed to value:** First deposition you schedule.

---

#### Trial Presentation | TrialPad

Industry-standard iPad app for courtroom evidence presentation. Annotate documents in real time during cross-examination, callout key passages, display case timeline exhibits, zoom into accident scene photos, and sync to a courtroom display — all from an iPad.
**Tool:** TrialPad | **Cost:** ~$130 one-time (no subscription)
*Jordan tries cases — this is the presentation layer that makes all other case prep visible to a judge and jury.*

---

#### Deposition Prep Workflow | CoCounsel + AI Prompting

Structured workflow using CoCounsel and custom prompt templates to generate cross-examination outlines, contradiction maps, and risk analyses from case documents and prior testimony.
Compresses 8–15 hours of deposition prep into under an hour — so prep time goes to strategy, not document review.
**Tool:** CoCounsel (already in stack) + custom prompts I build | **Cost:** $0 incremental

---

#### Voir Dire Preparation + Juror Research | AI + Trellis

AI analysis of juror questionnaire responses against bias indicators for PI/med mal cases, custom voir dire question library per case type, and Trellis venue data on historical jury behavior — output includes cause challenge flags and peremptory strike priority ranking.
Jury selection is where verdicts are often determined; data brings structure to one of trial's highest-leverage moments.
**Tool:** AI + Trellis (both in stack) + voir dire library I build per case type | **Cost:** $0 incremental

---

#### Case Timeline Exhibits | Supio + AI + Design Template

Supio's medical chronology and Clio case milestones assembled into a professional visual timeline exhibit — formatted for mediation presentations and trial, built once as a reusable template.
A timeline a mediator reads in 30 seconds communicates more than 10 pages of narrative.
**Tool:** Supio + Canva Pro (~$0–15/mo incremental)

---

### 9. Settlement & Closing

*The problem: mediation preparation is ad hoc; closing a case is still entirely manual.*

---

#### Settlement Authority Memo | AI + Trellis + EvenUp

Pre-mediation memo combining Trellis venue data, EvenUp damages analysis, and liability assessment into a data-supported authority range with low/mid/high scenarios.
Replaces gut-feel negotiation with comparable Georgia verdicts and structured damages projections — assembled in 20 minutes.
**Tool:** ChatGPT Pro + Trellis + EvenUp (all in stack) | **Cost:** $0 incremental

---

#### Mediation Brief Automation | Supio + Trellis + AI

AI-assisted workflow drafting a complete mediation brief from Supio's medical chronology, EvenUp's damages analysis, and Trellis comparable verdicts.
Cuts 4–8 hours of brief drafting to 90 minutes of AI assembly and 60 minutes of attorney review and customization.
**Tool:** AI + Supio + Trellis (all in stack) | **Cost:** $0 incremental

---

#### Low Offer Response Package | Trellis + AI

When an adjuster makes a low counteroffer, a formal written response supported by comparable Georgia verdicts, updated medical projections, and a point-by-point liability rebuttal — drafted and ready in under an hour.
You've been on the other side of this conversation. You know what a formal, data-supported written response does to an adjuster's posture versus a phone call. This workflow makes that response fast on every case, not just the ones with extra prep time.
**Tool:** Trellis + AI (both in stack) | **Cost:** $0 incremental

---

#### Settlement Disbursement Automation | Clio + Gavel

Gavel generates the disbursement statement and closing letter with calculated fields — gross settlement, attorney fee, costs, lien payoffs, net-to-client — and Clio trust accounting supports the disbursements. Every case closes; this applies to 100% of resolved matters.
**Tool:** Gavel + Clio Advanced | **Cost:** $0 incremental once Gavel is in stack
*Trust account transactions reviewed and executed by Jordan — workflow produces the paperwork, not the disbursement itself.*

---

### 10. Daily Productivity

*The problem: Outlook and Word eat 1–2 hours a day in tasks AI can handle in minutes.*

---

#### Email + Document AI | Microsoft Copilot

**What it is:** Microsoft Copilot ($30/mo) integrates AI directly into Outlook and Word — the tools Jordan likely already uses daily.

**High-value use cases:**
- *Email chain summarization*: before a client call, Copilot summarizes the last 20 emails on their matter so you walk in with context.
- *Correspondence drafting*: "Draft a letter to opposing counsel responding to their discovery objections on requests 3, 7, and 12" — Copilot drafts in your voice; you review and send.
- *Document review in Word*: paste in a settlement agreement or insurance coverage letter and ask Copilot to flag anything unusual.

**Tool:** Microsoft Copilot (~$30/mo add-on — requires Microsoft 365 Business, ~$6–22/mo separately if not already in place)
**ROI:** If Copilot saves 30 minutes per day in Outlook and Word, that's 10+ hours per month recovered in the workflow Jordan already lives in.
**Complexity:** Near zero — activates within the existing Office applications.
**Speed to value:** Days — active within existing Outlook and Word workflow.

---

#### Voice-to-Case-Memo Dictation | WisprFlow / Dragon Legal

AI voice dictation that captures post-meeting/post-hearing debriefs in real time, structures the output into a formatted case memo (key facts, action items, risk flags, next steps), and syncs to Clio as a case note.
Captures details while they're fresh — recovers 15 minutes of manual memo entry per client touchpoint, compounded across a full caseload.
**Tool:** WisprFlow (~$10/mo) recommended to start; Dragon Legal (~$50/mo) for highest accuracy on formal pleadings dictation

---

#### AI Call Transcription + Case Notes | Jamie

Automatically transcribes and summarizes calls and video meetings without joining as a visible bot — structured output syncs to Clio as a case note.
Every client call and expert consultation is documented without Jordan taking manual notes.
**Tool:** Jamie (~$24/mo) | *Georgia one-party consent applies; recording disclosure language included in the ethics policy build.*

---

### 11. Business Development

*The problem: reviews, content, and referral tracking all fall through the cracks in a solo practice.*

---

#### Google Review Management | Reviewly.ai

Monitors incoming Google reviews and generates professional, firm-branded response drafts for Jordan's approval. Also runs automated review request campaigns via SMS and email separate from Case Status's post-resolution trigger.
For a solo PI attorney, Google Business Profile is the primary trust signal for prospective clients — every unanswered review is a missed conversion.
**Tool:** Reviewly.ai (~$49–99/mo)

---

#### Marketing + Content | ChatGPT Pro

ChatGPT Pro ($20/mo) handles content drafting for blog posts, practice area pages, and social media. Clio Grow's intake tracking identifies which marketing channels drive qualified leads — so you know which content is working.
**Tool:** ChatGPT Pro (~$20/mo) | *All content must comply with Georgia Rules 7.1–7.5 on attorney advertising before publication.*

---

#### Incident + News Monitoring for Lead Awareness | Google Alerts + Mentionlytics

Monitors local news, web, and social media for accidents in Jordan's markets (Peachtree City, Fayette County, Coweta County, Spalding County / Griffin, Troup County / LaGrange, Newnan, Tyrone) before they appear in court filings — for referral network activation and targeted advertising.
Pre-filing awareness activates referral relationships before competitors know the case exists.
**Tool:** Google Alerts (free) or Mentionlytics (~$69/mo for social media coverage)

---

#### Warm Lead Nurture Sequences | Clio Grow

Case-type-specific SMS and email drip sequences for consultations that don't sign immediately — addressing common objections over 2–4 weeks before a personal follow-up from Jordan.
Recovers signed cases from leads who said "I need to think about it" without any manual effort.
**Tool:** Clio Grow (in stack) | **Cost:** $0 incremental once Clio is active

---

### 12. Additional Workflow Automations

*These are configurations built on tools already in your stack — no additional subscription required unless noted.*

| Automation | What It Replaces | Cost |
|---|---|---|
| Custom client onboarding packets | Manual per-case-type packet creation at engagement | $0 |
| Complaint first-draft workflow | 2–4 hours of complaint drafting per new filing | $0 |
| Insurance policy analysis | 45-minute manual policy review per case | $0 |
| Opposing counsel + expert research | Half-day pre-mediation manual research | $0 |
| Med mal viability pre-screen | Thousands in premature expert review costs | $0 |
| Future medical cost projection | $5K–15K life care planner on cases that don't need it | $0 |
| Deposition prep prompt library | 8–15 hours of deposition prep per complex witness | $0 |

---

## Section 4: What I Can Build For You

| # | Deliverable | Tools Involved | Timeline |
|---|-------------|---------------|----------|
| 1 | Smith.ai + Intaker + Clio Grow intake setup | Smith.ai, Intaker, Clio Grow | 2–3 weeks |
| 2 | Case Status build — milestone workflows, treatment check-ins, referral nurture, review trigger | Case Status, Clio | 1–2 weeks |
| 3 | Workflow automation — missed call text-back, appointment reminders, consultation follow-ups | Clio Grow | 1 week (bundled) |
| 4 | AI ethics policy + engagement letter update | Attorney time | 3–5 days |
| 5 | Firm technology security setup — MFA, encrypted email, WISP, password manager | Configuration only | 2–3 days |
| 6 | Clio practice management build — matter templates, custom fields, deadline rules, Clio Draft library | Clio Advanced, Clio Draft | 2–3 weeks |
| 7 | Trust accounting + IOLTA configuration — Clio trust module, LawPay integration | Clio, LawPay | 1 week |
| 8 | Tool onboarding + training — EvenUp, Supio, OrbDoc, CoCounsel, Expert Institute, Briefpoint, Tracers, Trellis, CaseYak, Reviewly.ai | All selected tools | 1–2 weeks |
| 9 | Marketing automation — ChatGPT content workflow, Reviewly.ai setup, Google Alerts keyword library | ChatGPT Pro, Reviewly.ai | 1–2 weeks |
| 10 | Advanced workflow buildout — any combination of the Section 3 workflow automations | Tools already in stack | 6–8 weeks total |
| 11 | Skribe setup + RAG transcript pipeline | Skribe, vector database | 1 week (bundled with RAG) |
| 12 | RAG system builds — expert witness DB, case library, medical literature (scoped separately) | Claude API, Pinecone/Chroma | Fixed-cost builds |
| 13 | Ongoing support + optimization — platform updates, troubleshooting, quarterly audits | All platforms | Ongoing |

---

---

## Selection Checklist

*Check off the items that match your practice's biggest pain points. No required order — pick whatever solves your most expensive problem first.*

| ☐ | Category | Tool / Service | Monthly Cost | Complexity | Speed to Value |
|---|----------|---------------|-------------|------------|----------------|
| ☐ | Intake | Smith.ai + Clio Grow | ~$285/mo | Medium | 2–3 weeks |
| ☐ | Intake | Intaker | ~$80/mo | Easy | Days |
| ☐ | Intake | Referral Network Management | $0 | Easy | 2–4 weeks |
| ☐ | Communication | Case Status | ~$99–149/mo | Easy–Med | 2 weeks |
| ☐ | Communication | AI Ethics Policy | $0 | Easy | 3–5 days |
| ☐ | Communication | Firm Security Setup | $0 | Easy | 2–3 days |
| ☐ | Demands & Records | EvenUp | $300–800/demand | Easy | First demand |
| ☐ | Demands & Records | Supio | $500–1,000/mo | Medium | First case |
| ☐ | Demands & Records | OrbDoc (bill auditing) | $0 | Easy | Same day |
| ☐ | Case Management | Clio Advanced + Draft | $168–198/mo | Medium | 3–4 weeks |
| ☐ | Case Management | Trust Accounting / LawPay | $0–49/mo | Medium | 2 weeks |
| ☐ | Case Management | Briefpoint (discovery) | ~$99/mo | Easy | First draft |
| ☐ | Deadlines | Full Litigation Deadline Management | $0 | Medium | 2–3 weeks |
| ☐ | Deadlines | Spoliation Letter Automation | $0 | Medium | 2–3 weeks |
| ☐ | Deadlines | Lien Tracking + Resolution | $0 | High | 4–6 weeks |
| ☐ | Research | Fastcase + CoCounsel | $0–65/mo | Easy | Days |
| ☐ | Research | Trellis (Georgia analytics) | $79–149/mo | Easy | Days |
| ☐ | Research | CaseYak (MVA value) | $0 | Easy | Same day |
| ☐ | Research | Expert Institute | Quote | Low | First case |
| ☐ | Investigation | Tracers / TLOxp | $39–150/mo | Easy | Immediate |
| ☐ | Investigation | Social Media Monitoring | $0 | Easy | Days |
| ☐ | Trial Prep | Skribe (deposition capture) | ~$349/hr | Low | First depo |
| ☐ | Trial Prep | TrialPad | $130 one-time | Easy | Days |
| ☐ | Trial Prep | Deposition Prep Workflow | $0 | Medium | 3–4 weeks |
| ☐ | Trial Prep | Voir Dire Library | $0 | Medium | 4–6 weeks |
| ☐ | Trial Prep | Case Timeline Exhibits | $0–15/mo | Low | 2–3 weeks |
| ☐ | Settlement | Settlement Authority Memo | $0 | Medium | 3–4 weeks |
| ☐ | Settlement | Mediation Brief Automation | $0 | Medium | 3–4 weeks |
| ☐ | Settlement | Low Offer Response Package | $0 | Easy | 2–3 weeks |
| ☐ | Settlement | Disbursement Automation | $0 | Medium | 4–6 weeks |
| ☐ | Productivity | Microsoft Copilot | ~$30/mo | Easy | Days |
| ☐ | Productivity | WisprFlow / Dragon Legal | $10–50/mo | Easy | Days |
| ☐ | Productivity | Jamie (call transcription) | ~$24/mo | Easy | Days |
| ☐ | Business Dev | Reviewly.ai | $49–99/mo | Easy | Days |
| ☐ | Business Dev | ChatGPT Pro (content) | $20/mo | Medium | 2–4 weeks |
| ☐ | Business Dev | Incident Monitoring | $0–69/mo | Easy | Days |
| ☐ | Business Dev | Warm Lead Nurture Sequences | $0 | Easy | 2–4 weeks |
| ☐ | Custom AI | Expert Witness Testimony Database | ~$15–30/mo + build | High | 2–3 months |
| ☐ | Custom AI | Personal Case Library RAG | ~$10–20/mo + build | Medium | 6–8 weeks |
| ☐ | Intelligence | NotebookLM | $0 | Easy | Days |
| ☐ | Custom AI | OpenClaw Legal Assistant | ~$50/mo | Medium | 3–4 weeks |
| ☐ | Custom AI | Medical Literature RAG | ~$10–20/mo + build | Medium | 6–8 weeks |
| ☐ | Custom AI | Georgia PJI RAG (NotebookLM) | $0 | Easy | Days |
| ☐ | Workflow | Client Onboarding Packets | $0 | Easy | 2–3 weeks |
| ☐ | Workflow | Complaint First-Draft Templates | $0 | Medium | 3–4 weeks |
| ☐ | Workflow | Insurance Policy Analysis | $0 | Easy | 2–3 weeks |
| ☐ | Workflow | Opposing Counsel Research | $0 | Low | 2–3 weeks |
| ☐ | Workflow | Med Mal Viability Pre-Screen | $0 | Medium | 3–4 weeks |
| ☐ | Workflow | Future Medical Cost Projection | $0 | Medium | 4–6 weeks |
| ☐ | Workflow | OpenClaw Legal Assistant | ~$50/mo | Medium | 4–6 weeks |


## Section 5: Monthly Cost Reference

| Tool | What It Does | Monthly Cost | Notes |
|------|-------------|-------------|-------|
| Clio Advanced | PM, CRM (Grow), calendaring, document management | $119/mo | Foundation for most automations |
| Clio Draft | Document template automation | ~$49–79/mo | Add-on; verify current pricing |
| Smith.ai | AI + human intake, 24/7 answering | ~$285/mo | 50-call plan; scales with volume |
| Intaker | Website AI chat + lead capture | ~$80/mo | PI-specific, Clio-integrated |
| Case Status | Client communication app, NPS, review automation | ~$99–149/mo | Branded client app |
| EvenUp | AI demand letters | $300–800/demand | Per-demand, not subscription |
| CoCounsel | AI legal research | $65/mo | Fastcase free via GA Bar |
| Supio | Medical record AI review | $500–1,000/mo | Volume-based |
| OrbDoc | Medical bill auditing | $0 | Free; Superinsight.ai for deeper analysis (quote) |
| LawPay | Trust accounting / IOLTA payments | $0–49/mo | Integrates with Clio |
| Expert Institute | Expert witness discovery + vetting | Quote | Contingency-friendly billing |
| Briefpoint | Discovery drafting | ~$99/mo | Solo plan |
| Tracers | Skip tracing + insurance discovery | ~$39–150/mo | |
| Skribe | Deposition capture + AI transcripts | ~$349/hr live | Per-deposition; no subscription |
| TrialPad | Courtroom evidence presentation | ~$130 one-time | iPad app |
| Trellis | Georgia litigation analytics | ~$79–149/mo | |
| CaseYak | MVA settlement value prediction | $0 | Free |
| ChatGPT Pro | Content drafting | $20/mo | |
| Reviewly.ai | Google review monitoring + AI responses | ~$49–99/mo | |
| Microsoft Copilot | Email + Word AI | ~$30/mo | Requires Microsoft 365 Business |
| Gavel | Advanced document automation | ~$99/mo | Only if Clio Draft proves insufficient |
| OpenClaw | AI legal assistant | ~$50/mo | Requires configuration |
| Jamie | Call transcription + case notes | ~$24/mo | |
| WisprFlow / Dragon Legal | Voice-to-case-memo dictation | ~$10–50/mo | |
| Mentionlytics | Social media incident monitoring | ~$69/mo | Google Alerts is free alternative |
| NotebookLM | Per-case document querying, Georgia PJIs | $0 | Free |
| Expert witness RAG | Searchable deposition transcript database | ~$15–30/mo running | One-time build fee separate |
| Personal case library RAG | Past demands, briefs, memos | ~$10–20/mo running | One-time build fee separate |
| Medical literature RAG | Standard-of-care literature for med mal | ~$10–20/mo running | One-time build fee separate |

**At average usage across the full stack, expect approximately $2,000–3,500/month in tool subscriptions.** This is roughly 30–40% of what a full-time paralegal costs, while covering intake, communication, record review, research, expert discovery, skip tracing, drafting, trial prep, deposition capture, and case closing automation.

**My engagement fee** covers setup, configuration, training, and optional ongoing support. We'll discuss scope and pricing based on which tools and services make sense for your practice — I'd rather build the right package for you than quote a number before we've talked.

---

## Section 6: Next Steps

1. **You decide what matters most.** Review Section 3 and flag the items that match your biggest pain points. No required starting point — pick what's most valuable to you right now.

2. **We agree on scope and timeline.** Based on what you want built, I put together a simple engagement agreement with deliverables, timeline, and payment terms. No surprises.

3. **I send the agreement.** One or two pages. Plain language. You sign, we start.

4. **Setup begins.** You give me access to Clio (or we create a new account), share your existing intake workflow, and provide branding assets (logo, firm colors, bio). I take it from there.

5. **30-day check-in.** We review what's working — lead capture rates, client communication volume, time saved on demands — and adjust anything that needs tuning.

6. **Add more when ready.** Once the first items are producing results and you're comfortable with the workflow, we layer in whatever's next on your list.

7. **After 90 days,** I'll share anonymized results from our work together — with your permission — as a case study for other plaintiff attorneys considering this path.

8. **If you know other attorneys** who could benefit from this kind of setup, I'm happy to offer a referral courtesy.

---

## Appendix: Questions to Ask Each Vendor

*Before committing to any of the top three tools, here are the questions worth asking during a discovery call. Each one surfaces something a vendor pitch won't tell you.*

---

### Smith.ai Discovery Questions

1. **Intake script configuration:** "Who builds the intake questions — do I write them and you configure, or does your team build them? How much control do I have over the script once it's live?"
2. **AI-to-human handoff:** "What specifically triggers a transfer to a live receptionist? Can I set my own handoff rules, and how does the warm transfer work?"
3. **Clio Grow integration:** "What does the integration setup look like — does your team handle it, and what data fields sync to Clio after each call?"
4. **True 24/7 coverage:** "Are your live receptionists available on holidays and overnight? Is there ever a gap in human coverage, and if so, what happens to those calls?"
5. **Conversion data:** "Can you share anonymized data on intake conversion rates for plaintiff PI firms on a 50-call plan? What percentage of after-hours calls result in a scheduled consultation?"

---

### EvenUp Discovery Questions

1. **Rural Georgia venue accuracy:** "Your AI is trained on verdict and settlement data. How dense is your dataset for Fayette, Spalding, Troup, and Coweta counties specifically? How does that affect valuation accuracy?"
2. **Turnaround time:** "What's your typical turnaround from record upload to demand draft — and does that change at high volume or during peak periods?"
3. **Output walkthrough:** "Can you walk me through a sample output on a soft-tissue auto case and a med mal case? I want to see what I'm reviewing before I send it."
4. **Quality disputes:** "If I'm not satisfied with a specific demand — disorganized records, wrong treatment emphasis — what's the revision process and does it cost extra?"
5. **Georgia plaintiff references:** "Do you have Georgia plaintiff PI references who practice in rural counties similar to my markets? I'd like to talk to one before we start."

---

### Supio Discovery Questions

1. **File formats and upload process:** "What formats do you accept for medical records? What's the upload process — portal, email, direct integration — and how do I track what's been submitted?"
2. **Multi-provider cross-referencing:** "When I have records from ER, treating physicians, specialists, and physical therapy, how does Supio identify inconsistencies and treatment gaps across all providers?"
3. **Med mal and dental mal depth:** "I do medical and dental malpractice in addition to PI. Can you walk me through how Supio handles standard-of-care analysis on a physician negligence matter versus a dental mal case?"
4. **Turnaround SLA:** "What's your turnaround time on a 500-page record set? Do you have an SLA, and what happens if a case is time-sensitive?"
5. **Security and HIPAA compliance:** "Do you sign a BAA? Where is PHI stored, who has access to it, and what's your breach notification protocol?"

---

---

*Prepared by Cayman Roden — AI Integration Consultant*
*cayman@openclaw.consulting | LinkedIn: /in/caymanroden*
*Specializing in AI implementation for legal practices — configuration, compliance, and workflow automation*
