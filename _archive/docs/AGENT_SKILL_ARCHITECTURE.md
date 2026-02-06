# 🤖 Agent & Skill Architecture - EnterpriseHub

## 🎯 Session Objective
Create specialized Claude Code agents and skills for real estate AI automation.

## 📋 COPY THIS PROMPT FOR NEXT SESSION:

```
I'm continuing EnterpriseHub development with focus on Claude Code agents and skills. MCP setup is complete (PostgreSQL, GoHighLevel, GitHub, Firecrawl, Memory, Sequential Thinking).

PRIORITY: Create specialized agents and skills for real estate AI automation:
- Market Intelligence Agent (Austin property analysis)
- Lead Qualification Agent (Jorge's GHL pipeline optimization)
- Performance Monitoring Agent (BI dashboard insights)
- Security Audit Agent (compliance and data protection)

Goal: Deploy agent swarm for complex real estate tasks and create reusable skills for common operations.

Key files: AGENT_SKILL_ARCHITECTURE.md, .claude/agents/, .claude/skills/
Context: EnterpriseHub real estate AI with Jorge's GoHighLevel integration
```

## 🏗️ Agent Architecture

### **Specialized Agents Needed**

#### 1. **Market Intelligence Agent**
- **Purpose**: Austin real estate market analysis and property intelligence
- **Tools**: Firecrawl, Sequential Thinking, Memory, PostgreSQL
- **Capabilities**:
  - Scrape and analyze Austin property listings
  - Identify market trends and opportunities
  - Generate comparative market analysis (CMA)
  - Track price movements and inventory levels
- **Triggers**: Market analysis requests, property matching tasks
- **File**: `.claude/agents/market-intelligence-specialist.md`

#### 2. **Lead Qualification Agent**
- **Purpose**: Jorge's GHL pipeline optimization and lead scoring
- **Tools**: GoHighLevel, PostgreSQL, Sequential Thinking, Memory
- **Capabilities**:
  - Analyze lead quality and conversion potential
  - Optimize qualification workflows
  - Generate lead scoring models
  - Identify high-value prospects
- **Triggers**: Lead analysis, pipeline optimization, CRM tasks
- **File**: `.claude/agents/lead-qualification-specialist.md`

#### 3. **Performance Monitoring Agent**
- **Purpose**: BI dashboard insights and system performance
- **Tools**: PostgreSQL, Memory, Sequential Thinking
- **Capabilities**:
  - Monitor system performance metrics
  - Generate BI dashboard insights
  - Identify optimization opportunities
  - Track business KPIs
- **Triggers**: Performance analysis, BI requests, monitoring tasks
- **File**: `.claude/agents/performance-optimizer.md`

#### 4. **Security Audit Agent**
- **Purpose**: Compliance, data protection, and security analysis
- **Tools**: GitHub, PostgreSQL, Memory
- **Capabilities**:
  - Audit code for security vulnerabilities
  - Review data handling compliance (TREC, GDPR)
  - Monitor API security and access patterns
  - Generate security reports
- **Triggers**: Security reviews, compliance checks, audit requests
- **File**: `.claude/agents/security-auditor.md`

#### 5. **Documentation Agent**
- **Purpose**: Maintain project documentation and knowledge base
- **Tools**: GitHub, Memory, Sequential Thinking
- **Capabilities**:
  - Update project documentation
  - Generate API documentation
  - Create user guides and tutorials
  - Maintain knowledge base
- **Triggers**: Documentation updates, knowledge management
- **File**: `.claude/agents/documentation-specialist.md`

## 🛠️ Skill Architecture

### **Core Real Estate Skills**

#### 1. **Lead Analysis Skill**
- **Path**: `.claude/skills/real-estate-ai/lead-analysis/`
- **Commands**:
  - `/analyze-lead` - Deep lead qualification analysis
  - `/score-lead` - Generate lead score with reasoning
  - `/lead-report` - Comprehensive lead assessment
- **Integration**: GoHighLevel MCP, PostgreSQL analytics

#### 2. **Property Intelligence Skill**
- **Path**: `.claude/skills/real-estate-ai/property-intelligence/`
- **Commands**:
  - `/find-properties` - Search Austin properties with criteria
  - `/market-analysis` - Generate CMA and market insights
  - `/property-match` - Match leads to property inventory
- **Integration**: Firecrawl MCP, market data APIs

#### 3. **Pipeline Optimization Skill**
- **Path**: `.claude/skills/real-estate-ai/pipeline-optimization/`
- **Commands**:
  - `/optimize-pipeline` - Analyze and improve GHL pipelines
  - `/conversion-analysis` - Lead conversion analytics
  - `/workflow-audit` - Review and optimize workflows
- **Integration**: GoHighLevel MCP, Sequential Thinking

#### 4. **BI Dashboard Skill**
- **Path**: `.claude/skills/real-estate-ai/bi-analytics/`
- **Commands**:
  - `/generate-dashboard` - Create BI dashboard components
  - `/performance-metrics` - Key performance indicators
  - `/revenue-attribution` - Track revenue sources
- **Integration**: PostgreSQL MCP, Streamlit components

#### 5. **Market Intelligence Skill**
- **Path**: `.claude/skills/real-estate-ai/market-intelligence/`
- **Commands**:
  - `/austin-market` - Austin market analysis and trends
  - `/opportunity-scan` - Identify investment opportunities
  - `/competitor-analysis` - Market competitive intelligence
- **Integration**: Firecrawl MCP, external data sources

## 🚀 Agent Coordination Patterns

### **Sequential Agent Workflow**
```
Lead Analysis Agent → Property Intelligence Agent → Performance Monitor
   ↓                      ↓                          ↓
Jorge's GHL Data    →   Austin Properties    →    BI Metrics
```

### **Parallel Agent Swarm**
```
┌─ Market Intelligence Agent ─┐
│  (Austin property analysis) │
├─ Lead Qualification Agent ──┤ → Strategic Recommendations
│  (Jorge's pipeline optimization) │
├─ Performance Monitor Agent ──┤
│  (BI insights)             │
└─ Security Audit Agent ──────┘
```

### **Agent Trigger Patterns**
- **User Request**: Direct agent invocation
- **Event-Driven**: MCP data changes trigger analysis
- **Scheduled**: Periodic market scans and performance reviews
- **Conditional**: Threshold-based automation

## 🔧 Implementation Tasks

### **Phase 1: Core Agents (Priority)**
1. **Create Market Intelligence Agent**
   - Austin property expertise
   - Firecrawl integration patterns
   - Market trend analysis capabilities

2. **Create Lead Qualification Agent**
   - Jorge's GHL specialization
   - Lead scoring algorithms
   - Pipeline optimization logic

### **Phase 2: Support Agents**
3. **Create Performance Monitoring Agent**
   - BI dashboard integration
   - Performance metric tracking
   - System health monitoring

4. **Create Security Audit Agent**
   - Real estate compliance focus
   - Data protection validation
   - Code security analysis

### **Phase 3: Skills Development**
5. **Real Estate Analysis Skills**
   - Lead qualification commands
   - Property intelligence tools
   - Market analysis utilities

6. **Business Intelligence Skills**
   - Dashboard generation
   - Performance analytics
   - Revenue tracking

## 📊 Agent Success Metrics

### **Market Intelligence Agent**
- Property analysis accuracy >90%
- Market trend prediction reliability
- Lead-property match quality score

### **Lead Qualification Agent**
- Lead score correlation with conversion
- Pipeline optimization improvements
- Jorge's CRM efficiency gains

### **Performance Monitoring Agent**
- System uptime and response times
- BI dashboard data freshness
- Performance bottleneck identification

### **Security Audit Agent**
- Vulnerability detection rate
- Compliance score improvements
- Data protection validation coverage

## 🎯 Agent Deployment Strategy

### **Agent Selection Logic**
```python
# Example agent routing
if task_type == "property_analysis":
    deploy_agent("market-intelligence-specialist")
elif task_type == "lead_scoring":
    deploy_agent("lead-qualification-specialist")
elif task_type == "performance_review":
    deploy_agent("performance-optimizer")
elif task_type == "security_audit":
    deploy_agent("security-auditor")
else:
    deploy_swarm(["market-intelligence", "lead-qualification"])
```

### **Coordination Patterns**
- **Single Agent**: Simple, focused tasks
- **Sequential Chain**: Multi-step analysis workflows
- **Parallel Swarm**: Complex, multi-domain problems
- **Hierarchical**: Agent supervision and coordination

## 📋 Next Session Tasks

1. **Create Agent Files**: Market intelligence and lead qualification agents
2. **Develop Core Skills**: Lead analysis and property intelligence
3. **Test Agent Deployment**: Task tool with specialized agents
4. **Validate Integration**: MCP tool access and data flow
5. **Performance Testing**: Agent response times and accuracy

---

**🎖️ Ready to deploy intelligent agent swarms for Jorge's real estate empire!**