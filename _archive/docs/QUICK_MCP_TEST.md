# 🚀 Quick MCP Test Guide

## 📋 Copy This For Next Session

```
MCP setup complete for EnterpriseHub. All 6 servers configured: PostgreSQL, GoHighLevel (Jorge's account), GitHub, Firecrawl, Memory, Sequential Thinking.

Test priority: "Query Jorge's GHL leads and match with Rancho Cucamonga properties"

Config: .mcp.json has all API keys. Database: enterprisehub ready.
```

## ⚡ Quick Test Sequence

### **Step 1: Verify Tools (30 seconds)**
```
ToolSearch query="postgres"
ToolSearch query="ghl"
ToolSearch query="firecrawl"
```

### **Step 2: Test Database (30 seconds)**
```
mcp__postgres__query sql="SELECT current_database(), now() as timestamp;"
```

### **Step 3: Test Jorge's CRM (1 minute)**
```
"List recent contacts from Jorge's GoHighLevel account"
```

### **Step 4: Test Property Scraping (1 minute)**
```
"Use Firecrawl to find 2 Rancho Cucamonga properties under $600k"
```

### **Step 5: Full Workflow Test (2 minutes)**
```
"Query Jorge's GHL for leads, find matching Rancho Cucamonga properties, create follow-up plan using Sequential Thinking"
```

## 🎯 Expected Results

- **PostgreSQL**: Returns database name and timestamp
- **GoHighLevel**: Shows Jorge's actual leads/contacts
- **Firecrawl**: Returns Rancho Cucamonga property listings with details
- **Sequential Thinking**: Generates strategic real estate insights
- **Memory**: Stores conversation insights
- **GitHub**: Accesses EnterpriseHub repository files

## 📊 Jorge's Account Details

- **Location ID**: 3xt4qayAh35BIDLaUv7P
- **Realtor**: realtorjorgesalas@gmail.com
- **Access**: Full CRM permissions
- **Data Types**: Leads, opportunities, contacts, pipelines

## 🔧 If Something Doesn't Work

1. **Tool not found**: Restart Claude Code
2. **API error**: Check .mcp.json credentials
3. **Database error**: Verify PostgreSQL running
4. **Permission error**: Check API key scopes

## 🎉 Success = Full Real Estate AI Automation

Once working, you can:
- Automatically query Jorge's live CRM data
- Scrape current Rancho Cucamonga property market
- Generate AI-powered lead strategies
- Store insights in database
- Deploy code changes via GitHub

---

**Ready to revolutionize Jorge's real estate business!**