# 🧪 Streamlit UI Testing Guide

Complete testing checklist for all 8 Tier 1 & Tier 2 feature pages.

---

## 📋 Quick Start Testing

### 1. Launch the App
```bash
cd ghl-real-estate-ai
streamlit run streamlit_demo/app.py
```

### 2. Open Browser
Navigate to: `http://localhost:8501`

### 3. Check Sidebar
Verify you see all pages listed in the sidebar navigation.

---

## ✅ Page-by-Page Testing Checklist

### 🏠 Home Page (Main App)

**Expected Features:**
- [ ] Chat interface loads
- [ ] Scenario selector works (Cold/Warm/Hot lead)
- [ ] "Reset Conversation" button clears chat
- [ ] User can type messages
- [ ] AI responses generate
- [ ] Lead dashboard shows on right side
- [ ] Property matches display at bottom

**Test Actions:**
1. Click "Apply Scenario" with "Hot Lead Example"
2. Verify pre-filled conversation appears
3. Type a custom message
4. Verify response generates
5. Click "Reset Conversation"
6. Verify chat clears

**Expected Results:**
- ✅ Chat interface functional
- ✅ Lead scoring updates
- ✅ Property cards display

---

### 📊 Page 1: Executive Dashboard

**URL:** Click "📊 Executive Dashboard" in sidebar

**Expected Features:**
- [ ] Top 4 KPI cards display (Revenue, Leads, Conversion, Deal Size)
- [ ] Revenue trend chart renders
- [ ] Revenue breakdown pie chart shows
- [ ] Lead stage distribution bar chart displays
- [ ] Conversion funnel chart renders
- [ ] Performance alerts section visible
- [ ] System health metrics show

**Test Actions:**
1. Change time period in sidebar (Last 7 Days → Last 30 Days)
2. Select different locations from filter
3. Adjust alert threshold slider
4. Click "🔄 Refresh Dashboard"

**Test Filters:**
- [ ] Time period dropdown works
- [ ] Location multiselect functions
- [ ] Alert threshold slider updates
- [ ] Refresh button reloads data

**Expected Charts:**
- ✅ Line chart: 30-Day Revenue Trend
- ✅ Pie chart: Revenue Breakdown
- ✅ Bar chart: Lead Stage Distribution
- ✅ Funnel chart: Conversion Funnel

**Performance Check:**
- [ ] Page loads in < 3 seconds
- [ ] Charts render smoothly
- [ ] No console errors

---

### 🎯 Page 2: Predictive Scoring

**URL:** Click "🎯 Predictive Scoring" in sidebar

**Expected Features:**
- [ ] Lead input form in sidebar
- [ ] Three score cards display (Lead Score, Deal Probability, Confidence)
- [ ] Score interpretation with recommendations
- [ ] Factor analysis bar chart
- [ ] 30-day score trend chart
- [ ] Score distribution chart
- [ ] Conversion by score chart

**Test Actions:**
1. Enter lead information in sidebar:
   - Name: "Test User"
   - Budget: $400,000
   - Timeline: "Immediate"
   - Engagement Score: 85
2. Click "🎯 Calculate Score"
3. Switch to "Factor Analysis" tab
4. Switch to "Trends" tab
5. Switch to "Batch Scoring" tab
6. Try uploading CSV (check sample format)

**Test Tabs:**
- [ ] Score Overview tab displays
- [ ] Factor Analysis tab shows breakdown
- [ ] Trends tab renders charts
- [ ] Batch Scoring tab shows upload option

**Expected Results:**
- ✅ Score updates based on inputs
- ✅ High scores (70+) show "High Priority" badge
- ✅ Recommendations change based on score
- ✅ All charts render correctly

---

### 🎬 Page 3: Demo Mode Manager

**URL:** Click "🎬 Demo Mode" in sidebar

**Expected Features:**
- [ ] Demo mode toggle in sidebar
- [ ] 4 scenario cards display
- [ ] Data statistics show (Total Leads, Conversations, etc.)
- [ ] Data type selector works
- [ ] Settings tab functional
- [ ] Usage guide tab displays

**Test Actions:**
1. Toggle "Enable Demo Mode" on/off
2. Click "▶️ Load" on "Cold Lead Journey"
3. Switch data type dropdown (Leads → Conversations → Properties)
4. Click "🔄 Reset All Data"
5. Click "🎲 Generate New Data"
6. Go to Settings tab and adjust sliders
7. Click "💾 Save Settings"

**Test Scenarios:**
- [ ] Cold Lead Journey loads
- [ ] Warm Lead Nurture loads
- [ ] Hot Lead Conversion loads
- [ ] Full Pipeline Demo loads

**Expected Results:**
- ✅ Scenarios load successfully
- ✅ Data previews display
- ✅ Settings save confirmation shows

---

### 📄 Page 4: Reports

**URL:** Click "📄 Reports" in sidebar

**Expected Features:**
- [ ] 4 quick report cards display
- [ ] Date range selector in sidebar
- [ ] Report format options work
- [ ] Custom report builder functional
- [ ] Saved reports list displays
- [ ] Scheduled reports section shows

**Test Actions:**
1. Click "Generate Daily Report"
2. Verify report preview appears
3. Try different date presets (Today, Last 7 Days, etc.)
4. Select custom date range
5. Go to "Custom Builder" tab
6. Check various metrics and charts
7. Click "🔨 Build Custom Report"
8. Go to "Saved Reports" tab
9. Go to "Scheduled Reports" tab

**Test Tabs:**
- [ ] Quick Reports generates previews
- [ ] Custom Builder allows selections
- [ ] Saved Reports lists items
- [ ] Scheduled shows active schedules

**Expected Results:**
- ✅ Reports generate successfully
- ✅ Charts display in preview
- ✅ Export buttons appear
- ✅ Custom builder builds report

---

### 💡 Page 5: Recommendations

**URL:** Click "💡 Recommendations" in sidebar

**Expected Features:**
- [ ] Summary metrics (High/Medium/Low Priority, Total Impact)
- [ ] Recommendation cards with actions
- [ ] Impact vs Effort matrix chart
- [ ] Category pie chart
- [ ] Completed recommendations list
- [ ] Settings page

**Test Actions:**
1. Change priority filter (select only High)
2. Change category filter
3. Click "▶️ Take Action" on a recommendation
4. Click action buttons ("View leads", "Send email", etc.)
5. Click "✅ Complete" on a recommendation
6. Click "❌ Dismiss" on a recommendation
7. Go to "Impact Analysis" tab
8. Go to "Completed" tab
9. Go to "Settings" tab

**Test Tabs:**
- [ ] Active recommendations display
- [ ] Impact Analysis shows matrix
- [ ] Completed shows past actions
- [ ] Settings allows configuration

**Expected Results:**
- ✅ Recommendations filter correctly
- ✅ Action buttons respond
- ✅ Impact matrix displays properly
- ✅ Completed items tracked

---

### 💰 Page 6: Revenue Attribution

**URL:** Click "💰 Revenue Attribution" in sidebar

**Expected Features:**
- [ ] Top 4 metrics (Revenue, Spend, ROI, Attribution Rate)
- [ ] Revenue waterfall chart
- [ ] Channel pie chart
- [ ] Stacked area trend chart
- [ ] Channel performance cards
- [ ] Customer journey visualization
- [ ] Sankey diagram

**Test Actions:**
1. Change time range (Last 30 Days → Last 90 Days)
2. Select attribution model (Last Touch → Linear)
3. Filter by channels
4. Filter by campaigns
5. Go to "Channels" tab
6. Click "📊 Details" on a channel
7. Go to "Customer Journey" tab
8. View sample journey flow
9. Go to "ROI Analysis" tab

**Test Tabs:**
- [ ] Overview shows attribution data
- [ ] Channels tab displays performance
- [ ] Customer Journey shows flow
- [ ] ROI Analysis provides insights

**Expected Results:**
- ✅ Attribution model changes affect display
- ✅ Waterfall chart shows revenue build-up
- ✅ Sankey diagram flows correctly
- ✅ ROI recommendations appear

---

### 🏆 Page 7: Competitive Benchmarking

**URL:** Click "🏆 Competitive Benchmarking" in sidebar

**Expected Features:**
- [ ] Overall rank card
- [ ] Performance metrics (Above Avg, Percentile, Score)
- [ ] Performance badges
- [ ] Radar chart comparison
- [ ] Quick insights (Strengths/Improvements)
- [ ] Detailed metrics table
- [ ] Gap analysis charts
- [ ] Competitive insights

**Test Actions:**
1. Change industry filter
2. Change market size
3. Change region
4. Toggle metric comparisons
5. Go to "Performance Metrics" tab
6. Review each metric card and progress bar
7. Go to "Gap Analysis" tab
8. Click "📋 Create Plan" on an improvement
9. Go to "Insights" tab

**Test Tabs:**
- [ ] Overview shows comparison
- [ ] Performance Metrics detailed
- [ ] Gap Analysis shows improvements
- [ ] Insights provide recommendations

**Expected Results:**
- ✅ Radar chart displays correctly
- ✅ Metrics show percentiles
- ✅ Gap analysis identifies opportunities
- ✅ Competitive positioning clear

---

### ✅ Page 8: Quality Assurance

**URL:** Click "✅ Quality Assurance" in sidebar

**Expected Features:**
- [ ] Overall quality score card
- [ ] Pass rate, issues count metrics
- [ ] Quality metrics breakdown bar chart
- [ ] Quality score trend line chart
- [ ] Conversation review list
- [ ] Issue alerts with severity
- [ ] Report generation options

**Test Actions:**
1. Adjust quality score threshold slider
2. Toggle quality filters (Passed/Failed/Warnings)
3. Toggle compliance checks
4. Click "🔄 Run QA Check"
5. Go to "Conversation Review" tab
6. Click "👁️" to view a conversation
7. Go to "Issues" tab
8. Click "🔍 Review" on an issue
9. Click "✅ Resolve" on an issue
10. Go to "Reports" tab
11. Click "Generate Daily Report"

**Test Tabs:**
- [ ] Overview shows quality metrics
- [ ] Conversation Review lists items
- [ ] Issues displays alerts
- [ ] Reports generates outputs

**Expected Results:**
- ✅ Quality score displays prominently
- ✅ Conversations filterable
- ✅ Issues categorized by severity
- ✅ Reports generate successfully

---

## 🎨 Visual/UI Testing

### Color Scheme
- [ ] Primary gradient (Purple/Blue) consistent across pages
- [ ] Success messages in green
- [ ] Warning messages in yellow
- [ ] Error/danger messages in red
- [ ] All emojis display correctly

### Responsiveness
Test on different screen sizes:
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

### Charts
- [ ] All charts load without errors
- [ ] Tooltips appear on hover
- [ ] Charts are interactive (zoom, pan)
- [ ] Legends display correctly
- [ ] Colors are consistent

### Layout
- [ ] Sidebar always visible
- [ ] Content doesn't overflow
- [ ] Cards properly aligned
- [ ] Spacing consistent
- [ ] No overlapping elements

---

## 🐛 Common Issues & Solutions

### Issue: "ModuleNotFoundError"
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: Charts not displaying
**Solution:**
```bash
pip install plotly --upgrade
streamlit cache clear
```

### Issue: Page loads slowly
**Solution:**
- Check data caching
- Reduce chart data points
- Clear browser cache

### Issue: Sidebar not showing pages
**Solution:**
- Check file naming (must be `N_emoji_Name.py`)
- Ensure files are in `pages/` folder
- Restart Streamlit

### Issue: Styles not applying
**Solution:**
- Check CSS syntax in markdown blocks
- Verify `unsafe_allow_html=True`
- Clear browser cache

---

## 📊 Performance Testing

### Load Times (Target)
- [ ] Initial page load: < 3 seconds
- [ ] Tab switch: < 1 second
- [ ] Chart render: < 2 seconds
- [ ] Filter update: < 1 second

### Memory Usage
Monitor in browser DevTools:
- [ ] No memory leaks
- [ ] Stays under 500MB
- [ ] GC runs periodically

### Network Requests
Check in DevTools Network tab:
- [ ] No unnecessary requests
- [ ] API calls cached where appropriate
- [ ] Static assets load quickly

---

## 🔐 Security Testing

### Input Validation
- [ ] Text inputs handle special characters
- [ ] Number inputs reject invalid values
- [ ] Date pickers enforce valid ranges
- [ ] File uploads validate types/sizes

### Error Handling
- [ ] Missing services show friendly errors
- [ ] Invalid data doesn't crash app
- [ ] API errors handled gracefully
- [ ] User gets helpful error messages

### Data Protection
- [ ] No sensitive data in URLs
- [ ] No API keys in client code
- [ ] Environment variables used correctly
- [ ] User input sanitized

---

## 📱 Mobile Testing

### Navigation
- [ ] Sidebar menu accessible
- [ ] Touch targets large enough
- [ ] Swipe gestures work
- [ ] Back button functions

### Display
- [ ] Text readable without zoom
- [ ] Charts fit screen width
- [ ] No horizontal scrolling
- [ ] Forms usable

### Performance
- [ ] Pages load on 3G
- [ ] Interactive within 5 seconds
- [ ] Smooth scrolling
- [ ] No jank/lag

---

## ✅ Final Checklist

Before considering testing complete:

### Functionality
- [ ] All 8 pages load successfully
- [ ] All charts render correctly
- [ ] All filters work
- [ ] All buttons respond
- [ ] All tabs switch properly
- [ ] All forms submit

### User Experience
- [ ] Navigation intuitive
- [ ] Load times acceptable
- [ ] Error messages helpful
- [ ] Visual hierarchy clear
- [ ] Consistent styling

### Cross-Browser
- [ ] Works in Chrome
- [ ] Works in Firefox
- [ ] Works in Safari
- [ ] Works in Edge

### Documentation
- [ ] All features documented
- [ ] Code comments present
- [ ] README updated
- [ ] Deployment guide ready

---

## 🚀 Automated Testing Script

Create `test_streamlit_ui.py`:

```python
#!/usr/bin/env python3
"""
Automated UI test script for Streamlit pages
"""
import subprocess
import time
import requests
from pathlib import Path

def test_streamlit_pages():
    """Test all Streamlit pages load without errors"""
    
    print("🧪 Starting Streamlit UI Tests...")
    print("=" * 60)
    
    # Check pages exist
    pages_dir = Path("streamlit_demo/pages")
    expected_pages = [
        "1_📊_Executive_Dashboard.py",
        "2_🎯_Predictive_Scoring.py",
        "3_🎬_Demo_Mode.py",
        "4_📄_Reports.py",
        "5_💡_Recommendations.py",
        "6_💰_Revenue_Attribution.py",
        "7_🏆_Competitive_Benchmarking.py",
        "8_✅_Quality_Assurance.py"
    ]
    
    print("\n📁 Checking page files...")
    all_exist = True
    for page in expected_pages:
        exists = (pages_dir / page).exists()
        status = "✅" if exists else "❌"
        print(f"{status} {page}")
        if not exists:
            all_exist = False
    
    if not all_exist:
        print("\n❌ Some pages missing!")
        return False
    
    print("\n✅ All page files present!")
    
    # Start Streamlit in background
    print("\n🚀 Starting Streamlit server...")
    process = subprocess.Popen(
        ["streamlit", "run", "streamlit_demo/app.py", "--server.port", "8501"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(5)
    
    # Test health endpoint
    print("\n🏥 Testing server health...")
    try:
        response = requests.get("http://localhost:8501/_stcore/health")
        if response.status_code == 200:
            print("✅ Server is healthy!")
        else:
            print(f"❌ Server returned status {response.status_code}")
            process.terminate()
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        process.terminate()
        return False
    
    # Cleanup
    print("\n🧹 Stopping server...")
    process.terminate()
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_streamlit_pages()
    exit(0 if success else 1)
```

Run with:
```bash
python test_streamlit_ui.py
```

---

## 📝 Test Report Template

After testing, document results:

```markdown
# Streamlit UI Test Report

**Date:** [Date]
**Tester:** [Name]
**Environment:** [Local/Staging/Production]

## Summary
- Total Pages: 8
- Pages Tested: X/8
- Issues Found: X
- Critical Issues: X
- Status: ✅ PASS / ❌ FAIL

## Page Results

### 1. Executive Dashboard
- Status: ✅ PASS
- Load Time: X seconds
- Issues: None

### 2. Predictive Scoring
- Status: ✅ PASS
- Load Time: X seconds
- Issues: None

[... continue for all pages ...]

## Issues Found

### Issue #1: [Title]
- **Severity:** Critical/High/Medium/Low
- **Page:** [Page Name]
- **Description:** [Details]
- **Steps to Reproduce:** [Steps]
- **Expected:** [Expected behavior]
- **Actual:** [Actual behavior]
- **Screenshot:** [If applicable]

## Recommendations

1. [Recommendation 1]
2. [Recommendation 2]

## Sign-off
- [ ] All critical issues resolved
- [ ] Ready for deployment
```

---

## 🎯 Testing Priority

### High Priority (Must Test)
1. All pages load without errors
2. All charts render correctly
3. Navigation works between pages
4. Filters affect data display
5. No console errors

### Medium Priority (Should Test)
1. Mobile responsiveness
2. Cross-browser compatibility
3. Load times acceptable
4. Error messages appropriate

### Low Priority (Nice to Test)
1. Exact color matching
2. Animation smoothness
3. Keyboard navigation
4. Accessibility features

---

**Testing Status:** Ready to begin ✅  
**Last Updated:** January 4, 2026
