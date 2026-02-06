# Auto Claude Handoff Templates

## Master Template Structure

### Portfolio Project Handoff Prompt Format
```markdown
# High-Ticket Portfolio Project: [PROJECT_NAME]

**Project Type**: [SaaS/Enterprise Integration/Consulting Framework]
**Target Value**: $[X]k+ service demonstrations
**Timeline**: [X] weeks for MVP portfolio piece
**Success Metric**: Enable $[Y]k+ client conversations

## Strategic Context

### Business Objective
[Clear explanation of how this showcases expertise and generates revenue]

### Target Audience
- **Primary**: [Ideal client profile]
- **Technical Level**: [C-level/Technical/Mixed]
- **Pain Points**: [What problems this solves]

### Competitive Advantage
[What makes this approach unique and valuable]

## Technical Specification

### Core Requirements
[Must-have features for portfolio impact]

### Technology Stack
[Optimized based on project type and constraints]

### Integration Points
[Key systems, APIs, or platforms to showcase]

### Success Criteria
- [ ] [Measurable technical outcomes]
- [ ] [Business impact demonstrations]
- [ ] [Portfolio quality markers]

## Claude Code Configuration

### Recommended Agent Swarm
[Specific agents and coordination strategy]

### Skills Configuration
[Project-specific skills to enable]

### Hooks & Quality Gates
[Automated validation and standards enforcement]

### Model Strategy
[When to use Opus vs Sonnet vs Haiku]

## Development Approach

### Phase 1: Foundation
[Core architecture and setup tasks]

### Phase 2: Core Features
[MVP functionality implementation]

### Phase 3: Portfolio Polish
[Client-ready refinements and demo preparation]

### Phase 4: Deployment & Demo
[Production deployment and presentation materials]

## Deliverable Specifications

### Technical Deliverables
- [ ] [Production-ready codebase]
- [ ] [Comprehensive documentation]
- [ ] [Automated testing suite]
- [ ] [Deployment automation]

### Business Deliverables
- [ ] [Demo environment]
- [ ] [Client presentation materials]
- [ ] [ROI calculation tools]
- [ ] [Case study framework]

## Quality Standards
[Specific standards for portfolio-grade work]

---

**Auto Claude Instructions**:
Use the above specification to build a high-ticket portfolio asset that demonstrates [EXPERTISE_AREA] mastery and enables $[VALUE]k+ client conversations. Deploy agent swarms for complex tasks, maintain portfolio-grade code standards, and generate comprehensive demo materials suitable for client presentations.
```

## Template Variations

### SaaS Product Portfolio Template
```markdown
# SaaS Portfolio Project: [PRODUCT_NAME]

## Revenue Model Demonstration
**Show**: How you build scalable, recurring revenue products
**Target**: SaaS clients needing $50k-$500k+ product development

### Key Features to Showcase
- User onboarding and activation flows
- Subscription management and billing integration
- Analytics dashboard for business insights
- API design for third-party integrations
- Scalable architecture patterns

### Claude Code Configuration
**Primary Agents**:
- feature-dev:code-architect (system design)
- frontend-design:frontend-design (professional UI)
- pr-review-toolkit:code-reviewer (production standards)

**Skills**: user-experience-design, api-excellence, scalable-architecture

**Hooks**: client-ready-standards, demo-data-generation

### Success Metrics
- 90%+ uptime demonstration
- Sub-200ms response times
- Mobile-responsive professional design
- Complete user journey from signup to value realization
- Revenue attribution tracking

**Demo Scenarios**:
1. New user onboarding (0-to-value in <5 minutes)
2. Power user workflow (advanced features)
3. Admin dashboard (business intelligence)
4. API integration (developer experience)
```

### Enterprise Integration Portfolio Template
```markdown
# Enterprise Integration Project: [INTEGRATION_NAME]

## Integration Mastery Demonstration
**Show**: How you solve complex enterprise connectivity challenges
**Target**: Enterprise clients needing $100k-$1M+ integration projects

### Key Integrations to Showcase
- Legacy system modernization approach
- Real-time data synchronization
- Security and compliance implementation
- Error handling and monitoring
- Change management consideration

### Claude Code Configuration
**Primary Agents**:
- feature-dev:code-explorer (understand complex systems)
- feature-dev:code-architect (integration patterns)
- security-focused agents (compliance)

**Skills**: enterprise-architecture, security-compliance, system-integration

**Hooks**: security-validation, compliance-check, integration-testing

### Success Metrics
- Zero data loss during integration
- 99.9%+ reliability demonstration
- Comprehensive audit logging
- Security compliance validation
- Performance impact minimization

**Demo Scenarios**:
1. Legacy system data migration
2. Real-time synchronization handling
3. Error recovery and rollback
4. Security audit trail review
```

### Consulting Framework Portfolio Template
```markdown
# Consulting Framework: [FRAMEWORK_NAME]

## Methodology Demonstration
**Show**: How you systematize expertise into scalable frameworks
**Target**: Consulting clients needing $75k-$300k+ process optimization

### Framework Components to Showcase
- Assessment and diagnostic tools
- Step-by-step methodology implementation
- ROI measurement and reporting
- Knowledge transfer systems
- Process automation opportunities

### Claude Code Configuration
**Primary Agents**:
- general-purpose (research and methodology)
- feature-dev:code-architect (framework structure)
- plugin-dev:agent-creator (if AI-powered tools)

**Skills**: methodology-design, knowledge-transfer, process-automation

**Hooks**: framework-validation, roi-calculation, client-deliverable-check

### Success Metrics
- Clear before/after improvement demonstration
- Measurable ROI calculation tools
- Self-service capability for clients
- Scalable implementation approach
- Knowledge transfer effectiveness

**Demo Scenarios**:
1. Initial assessment and baseline establishment
2. Framework implementation walkthrough
3. Progress tracking and ROI calculation
4. Knowledge transfer and client enablement
```

## Context Optimization for Auto Claude

### Token-Efficient Handoff Strategies

#### Progressive Disclosure Structure
```markdown
## Immediate Context (Load First - 1-2k tokens)
Core project requirements and strategic goals

## Technical Architecture (Load Phase 2 - 3-5k tokens)
System design and implementation approach

## Quality Standards (Load Phase 3 - 2-3k tokens)
Portfolio-grade requirements and success criteria

## Demo Preparation (Load Phase 4 - 2-3k tokens)
Client presentation and business value articulation
```

#### Reference-Based Loading
```markdown
## Core Specification
[Essential requirements - always loaded]

## Implementation References
@reference/[PROJECT_TYPE]-patterns.md
@reference/portfolio-quality-standards.md
@reference/client-demo-requirements.md
@reference/[DOMAIN]-specific-considerations.md

## Scripts (Zero-Context Execution)
scripts/validate-portfolio-standards.sh
scripts/generate-demo-data.sh
scripts/calculate-project-roi.sh
scripts/create-presentation-materials.sh
```

## Auto Claude Optimization Instructions

### Model Selection Guidance
```markdown
**For Auto Claude Session**:
- Use Opus for strategic decisions and complex architecture
- Use Sonnet for core development and implementation
- Use Haiku for routine validations and formatting
- Always enable thinking mode for architectural decisions
- Deploy agent swarms for parallel, independent tasks

**Context Management**:
- Load specifications progressively
- Use zero-context scripts for routine operations
- Leverage agent isolation for complex analysis
- Maintain focus on portfolio-quality deliverables

**Quality Enforcement**:
- Enable portfolio-specific hooks for automated validation
- Use pr-review-toolkit agents before any commits
- Generate comprehensive documentation for client review
- Create demo scenarios that showcase business value
```