# Streamlit Deployment Quick Reference

Copy-paste this during manual deployment at https://share.streamlit.io/

---

## App 1: AgentForge

```
Repository:     ChunkyTortoise/ai-orchestrator
Branch:         main
Main file:      app.py
App URL:        ct-agentforge
Python:         3.11
Secrets:        None required
```

**Target**: https://ct-agentforge.streamlit.app  
**Test**: Generate mock trace, verify visualization

---

## App 2: Prompt Lab

```
Repository:     ChunkyTortoise/prompt-engineering-lab
Branch:         main
Main file:      app.py
App URL:        ct-prompt-lab
Python:         3.11
Secrets:        None required
```

**Target**: https://ct-prompt-lab.streamlit.app  
**Test**: Browse pattern library, run evaluation

---

## App 3: LLM Starter

```
Repository:     ChunkyTortoise/llm-integration-starter
Branch:         main
Main file:      app.py
App URL:        ct-llm-starter
Python:         3.11
Secrets:        None required
```

**Target**: https://ct-llm-starter.streamlit.app  
**Test**: Test completions, view cost tracking

---

## After Deployment

### 1. Verify (Run in terminal)
```bash
cd /Users/cave/Documents/GitHub/EnterpriseHub
./docs/verify_deployments.sh
```

### 2. Publish Portfolio
```bash
cd /Users/cave/Documents/GitHub/chunkytortoise.github.io
git add projects.html
git commit -m "feat: add live demo URLs for 3 Streamlit apps"
git push origin main
```

### 3. Unblock Task #5
- Take screenshots of each app
- Mark task #2 as completed
- Proceed with cold outreach campaign

---

**Estimated Time**: 5-7 minutes per app (including build)

**Need help?** See `/Users/cave/Documents/GitHub/EnterpriseHub/docs/STREAMLIT_DEPLOY_GUIDE.md`
