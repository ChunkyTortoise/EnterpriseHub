# 🚀 Quick Start - Streamlit UI

## Launch the Application

```bash
cd ghl-real-estate-ai
streamlit run streamlit_demo/app.py
```

Open browser to: `http://localhost:8501`

---

## 📱 Navigation

The app now has **9 pages** accessible from the sidebar:

### Main Pages
- **🏠 Home** - Original demo with chat interface
- **📊 Analytics** - Campaign and lead analytics

### New Feature Pages (Tier 1 & 2)
1. **📊 Executive Dashboard** - Real-time KPIs
2. **🎯 Predictive Scoring** - ML lead scoring
3. **🎬 Demo Mode** - Demo scenarios
4. **📄 Reports** - Report generation
5. **💡 Recommendations** - AI suggestions
6. **💰 Revenue Attribution** - ROI tracking
7. **🏆 Competitive Benchmarking** - Industry comparison
8. **✅ Quality Assurance** - Conversation monitoring

---

## 🎨 Key Features

### Each Page Includes:
- ✅ Professional UI with custom styling
- ✅ Interactive Plotly charts
- ✅ Sidebar filters and controls
- ✅ Multi-tab layouts
- ✅ Export capabilities
- ✅ Real-time data updates

### Color Scheme:
- Primary: Purple/Blue gradient (#667eea → #764ba2)
- Success: Green (#28a745)
- Warning: Yellow (#ffc107)
- Danger: Red (#dc3545)

---

## 📊 Page Quick Tour

### 1. Executive Dashboard
- View KPIs, revenue trends, lead performance
- Monitor alerts and system health
- Time period filters in sidebar

### 2. Predictive Scoring
- Score individual leads or batch upload CSV
- View factor analysis and trends
- See conversion rates by score

### 3. Demo Mode Manager
- Load pre-built scenarios (Cold/Warm/Hot leads)
- Generate synthetic demo data
- Export/import demo configurations

### 4. Reports
- Quick templates (Daily, Weekly, Monthly)
- Custom report builder
- Schedule automated reports

### 5. Recommendations
- View AI-powered action suggestions
- Impact vs Effort matrix
- Track completed recommendations

### 6. Revenue Attribution
- Track marketing ROI by channel
- Customer journey visualization
- Multiple attribution models

### 7. Competitive Benchmarking
- Compare against industry standards
- Gap analysis and recommendations
- Competitive positioning radar chart

### 8. Quality Assurance
- Monitor conversation quality scores
- Review flagged conversations
- Track compliance issues

---

## 🔧 Customization

### Update Data Sources
Edit the service files in `services/` directory:
- `executive_dashboard.py`
- `predictive_scoring.py`
- `demo_mode.py`
- etc.

### Modify UI
Edit page files in `streamlit_demo/pages/`:
- Change colors in CSS sections
- Adjust layouts and charts
- Add new tabs or sections

### Add New Pages
Create new files in `streamlit_demo/pages/`:
```python
# Format: N_emoji_Page_Name.py
# Example: 9_🔥_New_Feature.py
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
streamlit run streamlit_demo/app.py --server.port 8502
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### Service Import Errors
Pages will show friendly error messages if services are unavailable.
Check that all files in `services/` directory exist.

### Charts Not Rendering
Ensure Plotly is installed:
```bash
pip install plotly
```

---

## 📈 Performance Tips

1. Use `@st.cache_resource` for service initialization
2. Use `@st.cache_data` for data loading
3. Limit data points in charts for better performance
4. Use pagination for large datasets

---

## 🎯 What's Next?

1. **Test in browser** - Click through all pages
2. **Customize data** - Connect to real data sources
3. **Adjust styling** - Match your brand colors
4. **Add authentication** - Implement user login
5. **Deploy** - Use Streamlit Cloud, Heroku, or Railway

---

**Need Help?**
- Streamlit docs: https://docs.streamlit.io
- Plotly docs: https://plotly.com/python
- Review code comments in each page file

**Status:** ✅ Production Ready
