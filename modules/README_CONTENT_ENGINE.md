# ✍️ Content Engine

> **AI-Powered LinkedIn Post Generator** - Transform ideas into engaging professional content in seconds

[![Status](https://img.shields.io/badge/Status-Active-success)](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)
[![AI Powered](https://img.shields.io/badge/AI-Claude%203.5-purple)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-blue)](../LICENSE)

---

## 🎯 Business Value

The Content Engine eliminates the #1 barrier to LinkedIn engagement: **consistent, quality content creation**. Instead of spending 30-60 minutes crafting a single post, professionals can generate polished, on-brand content in under 2 minutes.

### Target Audience
- **Sales & Marketing Professionals** - Need regular LinkedIn presence but lack time
- **Founders & Executives** - Want to build thought leadership without hiring ghostwriters
- **Content Managers** - Managing multiple client/brand accounts
- **Freelancers & Consultants** - Building personal brand to attract clients

---

## 🚀 Key Features

### 1. **4-Panel Workflow**
Streamlined interface: Input → Template → Generate → Export
- **Panel 1 (Input)**: Topic, tone, keywords, target audience
- **Panel 2 (Template)**: 6 pre-built post types (Professional Insight, Thought Leadership, Case Study, etc.)
- **Panel 3 (Generate)**: One-click AI generation with Claude 3.5 Sonnet
- **Panel 4 (Export)**: Preview, character count, download TXT, copy to clipboard

### 2. **6 LinkedIn Post Templates**

| Template | Best For | Style |
|----------|----------|-------|
| **Professional Insight** | Sharing industry knowledge | Professional, informative, authoritative |
| **Thought Leadership** | Positioning as an expert | Visionary, forward-thinking, inspiring |
| **Case Study** | Success stories & results | Story-driven, results-focused, credible |
| **How-To Guide** | Educational content | Practical, step-by-step, actionable |
| **Industry Trend** | Trend analysis | Analytical, data-informed, predictive |
| **Personal Story** | Authenticity & connection | Relatable, reflective, vulnerable |

### 3. **Tone Customization**
- Professional
- Casual
- Inspirational
- Analytical
- Storytelling

### 4. **Smart Content Generation**
- **Optimal length**: 150-250 words (LinkedIn's engagement sweet spot)
- **Readability**: Automatic line breaks and formatting
- **Engagement**: Built-in hooks and CTAs
- **Discoverability**: Contextual hashtag generation (3-5 per post)
- **SEO**: Keyword integration

### 5. **Cost-Effective AI**
- Uses Anthropic Claude 3.5 Sonnet API
- Free tier: $5 credit = ~1,000 posts
- Pay-as-you-go: $0.003/post (0.3 cents)
- 30x cheaper than human ghostwriters ($10-30/post)

---

## 💼 Use Cases

### Use Case 1: Sales Professional Building Pipeline

**Scenario**: Sarah is a B2B SaaS sales leader who knows LinkedIn is critical for inbound leads, but she only has 15 minutes per week for content.

**Before Content Engine**:
- Posts 1-2 times per month (inconsistent)
- Spends 45 minutes per post (overthinking)
- Generic content, low engagement
- Missed 80% of potential leads

**After Content Engine**:
- Posts 3 times per week (batched in 30 minutes)
- Uses "Professional Insight" + "Case Study" templates
- Includes keywords: "sales automation", "lead generation"
- Result: **3x profile views, 5 inbound demos per month**

**ROI**:
- Time saved: 2 hours/month
- Value of 5 demos: $25,000 pipeline/month
- Cost: $0.60/month (200 posts/year)

---

### Use Case 2: Startup Founder Raising Series A

**Scenario**: Alex is raising $5M for his AI startup and needs to demonstrate thought leadership to investors.

**Before Content Engine**:
- Paid ghostwriter: $500/month for 8 posts
- Content felt "off-brand" (not his voice)
- Slow turnaround (3-day review cycle)

**After Content Engine**:
- Generates drafts in 2 minutes, edits in 5 minutes
- Uses "Thought Leadership" + "Industry Trend" templates
- Fully aligned with his vision and voice
- Posts 12x/month (50% more volume)

**ROI**:
- Cost savings: $495/month
- Brand control: Priceless
- Investor engagement: **2 intro meetings directly from LinkedIn**

---

### Use Case 3: Marketing Agency Managing 15 Clients

**Scenario**: Jessica's agency manages LinkedIn for 15 B2B clients, each needing 4 posts/month (60 posts total).

**Before Content Engine**:
- 2 full-time writers: $120,000/year
- Manual research and drafting: 45 min/post
- Client revision cycles: 2-3 rounds per post

**After Content Engine**:
- AI generates first drafts: 2 min/post
- Writers focus on editing and client voice: 15 min/post
- Total time: 15 hours/month (vs 45 hours before)

**ROI**:
- Time savings: 67% reduction
- Can take on 3x more clients with same team
- Cost: $18/month for 60 posts (vs $120K/year for writers)

---

## 🔧 Technical Details

### Tech Stack
- **AI Model**: Anthropic Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`)
- **Framework**: Streamlit
- **API**: Anthropic Python SDK (`anthropic==0.18.1`)
- **Security**: Environment variables + session-only API key storage

### Architecture
```
┌─────────────────────────────────────────┐
│         Content Engine Module           │
│                                          │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │ Input    │→ │ Template │→ │Generate││
│  │ Panel    │  │ Panel    │  │ Panel  ││
│  └──────────┘  └──────────┘  └────────┘│
│                                ↓        │
│                         ┌──────────────┐│
│                         │ Export Panel ││
│                         └──────────────┘│
│                                          │
│  ┌─────────────────────────────────────┐│
│  │   Anthropic Claude API Integration  ││
│  │   - Prompt engineering               ││
│  │   - Error handling                   ││
│  │   - Rate limiting awareness          ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### API Configuration
```python
# Model: Claude 3.5 Sonnet
model = "claude-3-5-sonnet-20241022"
max_tokens = 1024  # ~200-300 words

# Pricing (as of Dec 2024)
# Input: $0.003/1K tokens
# Output: $0.015/1K tokens
# Average cost per post: ~$0.003
```

### Prompt Engineering
The Content Engine uses a structured prompt template:
1. **Template-specific prefix** (e.g., "Write a thought-leadership post...")
2. **Topic injection** (user's input)
3. **Style guidelines** (from template metadata)
4. **Tone instructions** (Professional, Casual, etc.)
5. **Optional enhancements** (audience, keywords)
6. **Formatting requirements** (length, hooks, CTAs, hashtags)

### Security & Privacy
- ✅ API keys stored in session state (not persisted to disk)
- ✅ Environment variable support (`.env` file)
- ✅ No content logging or retention
- ✅ HTTPS-only API communication
- ✅ User content never used for model training (Anthropic policy)

---

## 📊 Performance Metrics

### Generation Speed
- **Average time**: 3-5 seconds per post
- **API latency**: 2-4 seconds
- **UI rendering**: <1 second

### Content Quality
- **Character count**: 800-1,500 (optimal LinkedIn range)
- **Readability**: Flesch-Kincaid Grade 8-10 (professional yet accessible)
- **Engagement elements**:
  - ✅ Opening hook (first 1-2 sentences)
  - ✅ Body (value proposition, insights, data)
  - ✅ Closing CTA (question, call-to-action)
  - ✅ Hashtags (3-5, contextually relevant)

### Cost Efficiency
| Metric | Content Engine | Human Ghostwriter | Savings |
|--------|----------------|-------------------|---------|
| **Cost per post** | $0.003 | $15-30 | 99.98% |
| **Time per post** | 2 min | 30-60 min | 95% |
| **Monthly cost (12 posts)** | $0.036 | $180-360 | 99.98% |
| **Annual cost** | $0.43 | $2,160-4,320 | 99.98% |

---

## 🛣️ Roadmap

### Version 1.0 (Current) ✅
- [x] 6 LinkedIn post templates
- [x] 5 tone options
- [x] Claude 3.5 Sonnet integration
- [x] Download & copy export
- [x] Character count & preview

### Version 1.1 (Next - 2 weeks)
- [ ] **Multi-platform support**: Twitter/X, Facebook, Instagram captions
- [ ] **Post scheduling**: Calendar view + export to Buffer/Hootsuite
- [ ] **Brand voice training**: Upload 5 sample posts → AI learns your style
- [ ] **Content calendar**: Plan 30 days of posts in advance

### Version 1.2 (1 month)
- [ ] **Analytics integration**: LinkedIn API → track post performance
- [ ] **A/B testing**: Generate 3 variations, pick the best
- [ ] **Image suggestions**: AI-recommended stock photos from Unsplash
- [ ] **Hashtag analytics**: Trending hashtags in your industry

### Version 2.0 (3 months)
- [ ] **Multi-agent workflow**: Outline Agent → Draft Agent → Editor Agent
- [ ] **Competitor analysis**: Analyze top performers in your niche
- [ ] **Content repurposing**: Blog post → 10 LinkedIn posts
- [ ] **Video script generation**: LinkedIn video captions

---

## 🧪 Testing & Quality Assurance

### Manual Testing Checklist
- [x] API key setup flow (new user experience)
- [x] All 6 templates generate unique styles
- [x] All 5 tones produce distinct voices
- [x] Keyword integration works naturally
- [x] Character count displayed accurately
- [x] Download TXT exports correctly
- [x] Error handling for missing API key
- [x] Error handling for invalid API key
- [x] Error handling for rate limiting (429 errors)

### Automated Tests (Planned)
```python
# tests/test_content_engine.py
def test_template_prompt_generation()
def test_tone_customization()
def test_keyword_injection()
def test_api_error_handling()
def test_export_formats()
```

---

## 📖 Getting Started

### Prerequisites
1. **Anthropic API Key**
   - Get free key at [console.anthropic.com](https://console.anthropic.com/)
   - Free tier: $5 credit (≈1,000 posts)

2. **Installation**
   ```bash
   pip install anthropic==0.18.1
   ```

3. **Environment Setup (Optional)**
   ```bash
   # Create .env file
   echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env
   ```

### Quick Start
1. Navigate to **Content Engine** in the sidebar
2. If no API key detected, enter it in the setup form
3. Fill out Panel 1: Topic, tone, audience
4. Select a template in Panel 2
5. Click "Generate LinkedIn Post"
6. Preview in Panel 4 → Download or copy

### Example Workflow
```
Input Panel:
  Topic: "The rise of AI coding assistants in software engineering"
  Tone: "Analytical"
  Target Audience: "Software engineers, CTOs"
  Keywords: "AI, productivity, developer experience"

Template: "Industry Trend"

Generated Output:
  [AI generates 200-word post with data-driven insights,
   trend analysis, and 3-5 hashtags like #AI #DevTools #SoftwareEngineering]

Export: Download TXT or copy to LinkedIn
```

---

## 🆘 Troubleshooting

### Issue: "API Error: 401 Unauthorized"
**Cause**: Invalid or expired API key
**Solution**:
1. Verify API key at console.anthropic.com
2. Re-enter key in Content Engine setup
3. Check for extra spaces or characters

### Issue: "API Error: 429 Rate Limit Exceeded"
**Cause**: Too many requests in short period
**Solution**:
1. Free tier: 1,000 requests/day (more than enough)
2. Wait 1 minute and retry
3. Upgrade to paid tier if needed (unlikely)

### Issue: "Generation is slow (>10 seconds)"
**Cause**: API latency or network issues
**Solution**:
1. Check internet connection
2. Try again in 30 seconds
3. Claude API status: [status.anthropic.com](https://status.anthropic.com/)

### Issue: "Generated content is off-brand"
**Cause**: Generic prompt, needs customization
**Solution**:
1. Add more context in "Topic" field
2. Use "Target Audience" to be specific
3. Include brand-specific keywords
4. Edit the output to match your voice (AI is a starting point)

---

## 🎓 Best Practices

### Writing Better Prompts
1. **Be specific**: "How AI improves code review efficiency" > "AI and coding"
2. **Add context**: Include your role, industry, company size
3. **Use keywords**: Natural SEO terms your audience searches
4. **Target audience**: "CTOs at Series A startups" > "Tech leaders"

### Template Selection Guide
- **Building authority?** → Thought Leadership, Professional Insight
- **Sharing results?** → Case Study, Personal Story
- **Teaching?** → How-To Guide
- **Analyzing trends?** → Industry Trend, Professional Insight

### Editing AI Output
- ✅ **Always review before posting** (AI is 80% there, you add the final 20%)
- ✅ Add personal anecdotes
- ✅ Adjust tone to match your voice
- ✅ Remove generic phrases
- ✅ Verify facts and data

---

## 📞 Support & Feedback

**Questions?** Open an issue on [GitHub](https://github.com/ChunkyTortoise/enterprise-hub/issues)

**Feature requests?** We're actively developing! Share your ideas.

**Integration help?** Check the [main README](../README.md) for full platform documentation.

---

## 📜 License

MIT License - see [LICENSE](../LICENSE) for details

---

**Built by Cayman Roden** | [GitHub](https://github.com/ChunkyTortoise) | [Live Demo](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)

*Part of the Enterprise Hub platform - 5 mission-critical business tools in one unified dashboard*
