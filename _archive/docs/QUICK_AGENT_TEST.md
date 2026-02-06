# 🤖 Quick Agent Test - 5 Minutes

## 📋 Copy This for Next Session
```
Agent & skill testing for EnterpriseHub. All MCP tools ready. Goal: Deploy specialized real estate agents and test Jorge's GHL integration.

Quick tests: Market Intelligence Agent → Austin properties, Lead Analysis → Jorge's data, Agent swarm coordination.
```

## ⚡ 60-Second Agent Status Check

```bash
# 1. List available agents (10 seconds)
ls .claude/agents/ | grep -E "(market|performance|security|chatbot)"

# 2. List real estate skills (10 seconds)
ls .claude/skills/real-estate-ai/

# 3. Test MCP tools (30 seconds)
ToolSearch query="postgres"
ToolSearch query="ghl"
ToolSearch query="firecrawl"

# 4. Quick database test (10 seconds)
mcp__postgres__query sql="SELECT 'Agents ready!' as status, now() as timestamp;"
```

## 🎯 Priority Agent Tests (2 minutes each)

### **1. Market Intelligence Agent**
```
Task subagent_type="market-intelligence-specialist" "Find 3 Austin luxury properties under $700k in West Lake Hills with highest appreciation potential"
```
**Expected**: Property analysis with price predictions and investment insights.

### **2. Lead Analysis with Jorge's Data**
```
"Use lead analysis skills to query Jorge's GoHighLevel for recent leads and generate qualification scores"
```
**Expected**: Lead list with scores and qualification analysis.

### **3. Performance Monitoring**
```
Task subagent_type="performance-optimizer" "Analyze current EnterpriseHub system performance and identify optimization opportunities"
```
**Expected**: System metrics and performance recommendations.

## 🔥 Power Test: Agent Swarm (3 minutes)

```
Task subagent_type="market-intelligence-specialist" "Analyze Austin market for luxury buyers with $500k-1M budget"
Task subagent_type="general-purpose" "Query Jorge's GHL for leads matching luxury buyer profile and generate personalized outreach strategies using Sequential Thinking"
```

**Expected**: Coordinated real estate intelligence with market analysis + lead matching + strategic recommendations.

## 🎖️ Success Indicators

- ✅ Agents deploy without errors
- ✅ Jorge's GHL data accessible
- ✅ Austin property data retrieved
- ✅ AI reasoning generates insights
- ✅ Parallel agent coordination works
- ✅ Skills integrate with MCP tools

## 🚨 Quick Troubleshooting

| Issue | Quick Fix |
|-------|-----------|
| Agent not found | Check `.claude/agents/` directory |
| Skill command fails | Verify `.claude/skills/real-estate-ai/` structure |
| GHL data error | Test `ToolSearch query="gohl"` |
| Property scraping fails | Test `ToolSearch query="firecrawl"` |

## 🚀 Success = Autonomous Real Estate AI

Once working:
- Market intelligence automation ✅
- Lead qualification optimization ✅
- Multi-agent task coordination ✅
- Jorge's CRM integration ✅
- Austin property analysis ✅

---

**Ready for real estate AI domination in 5 minutes!**