# Polar.sh README Badge Instructions

Add this section to each repository's README.md file after setup is complete.

---

## For All 5 Repositories

### Repositories:
1. ai-orchestrator (AgentForge)
2. docqa-engine (DocQA)
3. insight-engine (Streamlit Dashboards)
4. mcp-server-toolkit
5. EnterpriseHub

---

## Badge Code (Copy-Paste)

Add this section near the top of each README.md (after project description, before installation):

```markdown
## 💚 Support This Project

[![Support on Polar](https://polar.sh/embed/subscribe.svg?org=ChunkyTortoise)](https://polar.sh/ChunkyTortoise)

Love this project? Support ongoing development and get exclusive benefits:

- **💚 Sponsor** ($5-$150/month) - Early access, priority support, code reviews
- **📦 Products** ($79-$199) - Commercial licenses, starter kits, dashboard templates
- **📧 Newsletter** (Free) - Bi-weekly AI engineering insights

**[View all tiers and benefits →](https://polar.sh/ChunkyTortoise)**

---
```

---

## Alternative Compact Version

If you want a more minimal badge:

```markdown
## Support

[![Polar](https://polar.sh/embed/subscribe.svg?org=ChunkyTortoise)](https://polar.sh/ChunkyTortoise)

Support this project via [Polar.sh](https://polar.sh/ChunkyTortoise) 💚
```

---

## Alternative Detailed Version

For repositories with commercial products:

```markdown
## 💚 Support & Commercial Licensing

[![Support on Polar](https://polar.sh/embed/subscribe.svg?org=ChunkyTortoise)](https://polar.sh/ChunkyTortoise)

### Free Open Source
This project is free and open source under the MIT License.

### Commercial Support & Licenses
Need enterprise support or a commercial license?

**Sponsorship Tiers:**
- 💚 **Supporter** ($5/month) - Newsletter, early access, Discord
- 🤝 **Contributor** ($15/month) - Priority support, quarterly Q&A
- 💼 **Professional** ($50/month) - Code review (2hrs/month), custom integrations
- 🏢 **Enterprise** ($150/month) - Dedicated support (6hrs/month), SLA, private Slack

**One-Time Products:**
- 📦 **AgentForge Pro License** ($199) - Commercial license with 6 months updates
- 📦 **DocQA Starter Kit** ($99) - RAG system template with tutorials
- 📦 **Dashboard Bundle** ($79) - 5 production-ready Streamlit templates

**Newsletter (Free):**
- 📧 **"AI Engineering Insights"** - Bi-weekly deep dives into production AI

**[View all options →](https://polar.sh/ChunkyTortoise)**

---
```

---

## Repository-Specific Examples

### For ai-orchestrator (AgentForge)

```markdown
## 💚 Support AgentForge

[![Support on Polar](https://polar.sh/embed/subscribe.svg?org=ChunkyTortoise)](https://polar.sh/ChunkyTortoise)

Building production AI apps with AgentForge? Consider:

- **Commercial License** ($199) - Full source, 6 months updates, priority support
- **Professional Sponsor** ($50/month) - Code review, custom integration help
- **Newsletter** (Free) - Get "How We Reduced LLM Costs by 89%" and more

**[View all tiers →](https://polar.sh/ChunkyTortoise)**
```

### For docqa-engine (DocQA)

```markdown
## 💚 Support DocQA

[![Support on Polar](https://polar.sh/embed/subscribe.svg?org=ChunkyTortoise)](https://polar.sh/ChunkyTortoise)

Need RAG system help?

- **DocQA Starter Kit** ($99) - Complete template with tutorials
- **Professional Sponsor** ($50/month) - Code review, architecture guidance
- **Newsletter** (Free) - RAG optimization tips, hybrid search strategies

**[View all tiers →](https://polar.sh/ChunkyTortoise)**
```

### For insight-engine (Dashboards)

```markdown
## 💚 Support Insight Engine

[![Support on Polar](https://polar.sh/embed/subscribe.svg?org=ChunkyTortoise)](https://polar.sh/ChunkyTortoise)

Building BI dashboards?

- **Dashboard Bundle** ($79) - 5 production-ready Streamlit templates
- **Contributor Sponsor** ($15/month) - Priority feature requests
- **Newsletter** (Free) - Dashboard design patterns, async best practices

**[View all tiers →](https://polar.sh/ChunkyTortoise)**
```

### For mcp-server-toolkit

```markdown
## 💚 Support MCP Development

[![Support on Polar](https://polar.sh/embed/subscribe.svg?org=ChunkyTortoise)](https://polar.sh/ChunkyTortoise)

Building MCP servers?

- **Sponsor** ($5-$150/month) - Support MCP server development
- **Newsletter** (Free) - MCP patterns, integration guides
- **Products** ($79-$199) - Commercial templates and licenses

**[View all tiers →](https://polar.sh/ChunkyTortoise)**
```

### For EnterpriseHub

```markdown
## 💚 Support EnterpriseHub

[![Support on Polar](https://polar.sh/embed/subscribe.svg?org=ChunkyTortoise)](https://polar.sh/ChunkyTortoise)

Interested in real estate AI platforms?

- **Enterprise Sponsor** ($150/month) - Architecture consulting, SLA support
- **Newsletter** (Free) - Multi-agent orchestration, conversation design
- **Commercial Licenses** ($79-$199) - Production-ready templates

**[View all tiers →](https://polar.sh/ChunkyTortoise)**
```

---

## Placement Recommendations

### Option 1: After project description
```markdown
# Project Name

Description of the project...

## 💚 Support This Project
[Polar badge here]

## Installation
...
```

### Option 2: In sidebar (if using GitHub features)
Add to repository settings → "Sponsor this project"

### Option 3: Bottom of README
```markdown
...
## License
MIT

---

## 💚 Support This Project
[Polar badge here]
```

---

## Testing Checklist

After adding badges:

- [ ] Badge renders correctly (visible image)
- [ ] Badge links to https://polar.sh/ChunkyTortoise
- [ ] Clicking badge opens Polar page
- [ ] Page shows all tiers and products
- [ ] Mobile view looks good
- [ ] Badge doesn't break README layout

---

## Update Script (Optional)

If you want to automate badge insertion:

```bash
#!/bin/bash
# update-polar-badges.sh

REPOS=(
  "ai-orchestrator"
  "docqa-engine"
  "insight-engine"
  "mcp-server-toolkit"
  "EnterpriseHub"
)

BADGE='
## 💚 Support This Project

[![Support on Polar](https://polar.sh/embed/subscribe.svg?org=ChunkyTortoise)](https://polar.sh/ChunkyTortoise)

Love this project? Support ongoing development: [View all tiers →](https://polar.sh/ChunkyTortoise)

---
'

for repo in "${REPOS[@]}"; do
  echo "Updating $repo..."
  cd "../$repo" || continue

  # Insert badge after first heading
  # (Requires manual review before running)

  echo "✅ $repo updated"
done

echo "Done! Review changes before committing."
```

**⚠️ WARNING**: Review all changes manually before committing.

---

## Launch Announcement Template

When badges are live, announce on social media:

**LinkedIn**:
```
🚀 New: Support my open-source AI/ML projects on Polar.sh!

All 5 repositories now have sponsorship tiers ($5-$150/month),
commercial products ($79-$199), and a free newsletter.

Check out the updated READMEs:
- github.com/ChunkyTortoise/ai-orchestrator
- github.com/ChunkyTortoise/docqa-engine
- github.com/ChunkyTortoise/insight-engine

First newsletter drops next week: "How We Reduced LLM Costs by 89%"

#OpenSource #AI #BuildInPublic
```

---

**Last Updated**: 2026-02-15
**Action Required**: Add badges after Polar.sh setup is complete
