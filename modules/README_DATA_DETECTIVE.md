# 🔍 Data Detective - AI-Powered Data Analysis

> Transform raw CSV data into actionable insights in minutes, not hours

## Overview

Data Detective is an AI-powered data analysis module that combines automated data profiling, quality assessment, and Claude AI insights to help you understand any dataset instantly. Perfect for business analysts, data scientists, and consultants who need quick, intelligent data exploration.

### Business Value

| Metric | Traditional Approach | Data Detective | Improvement |
|--------|---------------------|----------------|-------------|
| **Initial Data Assessment** | 30-60 min (manual Excel) | 2-3 min (automated) | **95% faster** |
| **Quality Audit** | 2-4 hours (manual checks) | 5 min (AI-powered) | **97% faster** |
| **Insights Generation** | 1-2 days (analyst review) | 30 sec (AI insights) | **99.7% faster** |
| **Cost Per Analysis** | $100-200 (2-4 hours @ $50/hr) | $0.10 (API costs) | **99.9% cheaper** |

**Annual Savings**: $48,000 for teams doing 10 analyses per week

---

## Key Features

### 1. 📊 Automated Data Profiling

**No coding required** - Upload a CSV and instantly get:

- **Dataset Overview**: Row count, column count, memory usage, duplicates
- **Column-Level Statistics**:
  - Data types and null value analysis
  - Unique value counts
  - Numeric columns: min, max, mean, distribution
  - Categorical columns: top values and frequencies
- **Visual Distributions**:
  - Interactive histograms for numeric data
  - Box plots for outlier detection
  - Bar charts for categorical frequencies
- **Correlation Matrix Heatmap**:
  - Visualize relationships between all numeric variables
  - Color-coded heatmap showing correlation coefficients (-1 to +1)
  - Automatically highlights strong correlations (|r| ≥ 0.7)
  - **Value proposition**: Instantly identify which variables are related, perfect for feature selection and understanding data dependencies

**Example Output:**
```
Dataset: sales_data.csv
- 125,483 rows × 12 columns
- 15.3 MB memory usage
- 47 duplicate rows detected
- Quality Score: 87%
```

### 2. 🤖 AI-Powered Insights

Leverage Claude 3.5 Sonnet to automatically detect:

- **Trend Analysis**: Seasonal patterns, growth rates, cyclical behavior
- **Anomaly Detection**: Outliers, data spikes, unusual patterns
- **Quality Assessment**: Missing value patterns, data consistency issues
- **Business Recommendations**: Actionable next steps based on findings
- **Relationship Discovery**: Correlations and dependencies between variables

**Example Insight:**
> "💡 **Revenue Trend**: Revenue shows 23% quarter-over-quarter growth with strong seasonality in Q4 (avg +40% vs other quarters). Consider increasing inventory procurement in September to meet Q4 demand."

**Cost**: ~$0.01-0.03 per analysis (depending on dataset size)

### 3. 🧹 Data Quality Assessment

Automated detection and one-click fixes for:

#### Missing Values
- **Detection**: Identifies columns with nulls and calculates percentage
- **Impact**: Assesses severity (High >10%, Medium 5-10%, Low <5%)
- **Fix**: One-click removal or smart imputation suggestions

#### Duplicate Rows
- **Detection**: Identifies exact duplicate records
- **Impact**: Percentage of dataset affected
- **Fix**: One-click deduplication with optional review

#### Outliers
- **Detection**: IQR method (Q1 - 1.5×IQR, Q3 + 1.5×IQR)
- **Impact**: Number of outliers per numeric column
- **Recommendations**: Winsorization, removal, or manual review

#### Data Type Issues
- **Detection**: Numeric data stored as text, date parsing issues
- **Impact**: Affects calculations and visualizations
- **Fix**: Automated type conversion suggestions

### 4. 💬 Natural Language Queries

**Ask questions in plain English** - No SQL or Python required!

Example questions:
- "What are the top 5 customers by revenue?"
- "Is there a correlation between price and sales volume?"
- "Show me the average order value by region"
- "Are there any outliers in the refund_amount column?"
- "What percentage of orders were returned?"

Claude AI translates your questions into data analysis and provides clear answers.

### 5. 📥 Export Capabilities

Download processed data in multiple formats:

- **CSV Export**: Cleaned data ready for Excel/Google Sheets
- **Excel Export**: Professional .xlsx format with formatting
- **Analysis Report**: Summary statistics and insights (coming soon)
- **Timestamp Naming**: Auto-generated filenames prevent overwrites

---

## Use Cases

### 1. **Client Data Audits** (Consultants)

**Scenario**: New client engagement - need to assess their sales data quality

**Traditional Approach**:
- Manual Excel inspection: 2 hours
- Quality documentation: 1 hour
- Insights summary: 2 hours
- **Total**: 5 hours @ $75/hr = $375

**With Data Detective**:
1. Upload client CSV (30 seconds)
2. Run AI insights (1 minute)
3. Export quality report (30 seconds)
4. **Total**: 2 minutes @ $75/hr = $2.50

**Savings**: 99.3% time reduction, $372.50 per audit

### 2. **Pre-Modeling Data Assessment** (Data Scientists)

**Scenario**: Starting new ML project - need to understand dataset before feature engineering

**Traditional Workflow**:
```python
# 30+ lines of pandas code for basic profiling
import pandas as pd
df = pd.read_csv('data.csv')
print(df.info())
print(df.describe())
print(df.isnull().sum())
# ... more manual exploration
```

**With Data Detective**:
1. Upload CSV
2. Review automated profiling
3. Ask AI: "What features would be good predictors for [target]?"
4. Get instant feature importance suggestions

**Savings**: 1-2 hours of manual profiling per project

### 3. **Exploratory Data Analysis** (Business Analysts)

**Scenario**: Marketing team wants insights from campaign performance data

**Traditional Approach**:
- Create pivot tables: 1 hour
- Build charts: 1 hour
- Write insights: 1 hour
- **Total**: 3 hours

**With Data Detective**:
1. Upload campaign CSV
2. AI generates insights automatically
3. Export visualizations
4. **Total**: 5 minutes

**Result**: Can analyze 36x more campaigns in same time

---

## Technical Specifications

### Input Requirements

- **Format**: CSV (.csv) and Excel files (.xlsx, .xls)
- **Size**: Up to 50 MB recommended (larger files supported but may be slow)
- **Rows**: Up to 1 million rows (10k rows recommended for AI insights)
- **Encoding**: UTF-8 preferred (auto-detection supported)
- **Dependencies**: Excel file support requires openpyxl library (included in requirements.txt)

### AI Integration

- **Model**: Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
- **API Provider**: Anthropic
- **Cost**: ~$0.003-0.030 per analysis (token-based pricing)
- **Latency**: 2-5 seconds for insights generation
- **Privacy**: Data never stored; API key in session only

### Technology Stack

```python
streamlit==1.28.0      # Web framework
pandas==2.1.3          # Data manipulation
numpy==1.26.2          # Numerical computing
plotly==5.17.0         # Interactive visualizations
anthropic==0.18.1      # Claude AI integration
openpyxl==3.1.2        # Excel import/export
```

---

## Getting Started

### 1. Setup

Ensure you have the required dependencies:

```bash
pip install -r requirements.txt
```

Get your Anthropic API key:
1. Visit https://console.anthropic.com/
2. Sign up or log in
3. Generate API key from settings
4. Copy key for use in the app

### 2. Basic Usage

**Step 1: Upload Data**
- Click "Choose a CSV or Excel file" button
- Select your CSV or Excel file from local storage
- Wait for upload confirmation

**Step 2: Explore Profile**
- Review automatic statistics in "Data Profile" tab
- Check distribution visualizations
- Identify column types and missing values

**Step 3: Generate AI Insights**
- Switch to "AI Insights" tab
- Paste your Anthropic API key
- Click "Generate AI Insights"
- Review automated findings

**Step 4: Assess Quality**
- Go to "Data Quality" tab
- Review detected issues
- Apply one-click fixes if needed
- Preview cleaned data

**Step 5: Ask Questions**
- Navigate to "Ask Questions" tab
- Type natural language query
- Get AI-powered answers

**Step 6: Export Results**
- Switch to "Export" tab
- Choose format (CSV or Excel)
- Download cleaned data

### 3. Advanced Tips

**For Large Datasets**:
- Use data profiling on full dataset
- Sample random subset for AI insights (faster + cheaper)
- Export cleaned data for further analysis

**For Sensitive Data**:
- Use data profiling (no API calls)
- Skip AI insights if privacy is a concern
- All processing happens locally except AI features

**Cost Optimization**:
- AI insights: ~$0.01-0.03 per analysis
- Use sparingly on large datasets
- Cache results by saving insights as text

---

## ROI Calculator

### Small Business Analyst (10 analyses/month)

| Method | Time | Cost | Monthly Total |
|--------|------|------|---------------|
| **Manual** | 3 hrs/analysis | $50/hr | $1,500 |
| **Data Detective** | 5 min/analysis | $0.10 | $8.33 |
| **Savings** | 29.5 hrs | - | **$1,491.67/mo** |

**Annual Savings**: $17,900

### Consulting Team (50 analyses/month)

| Method | Time | Cost | Monthly Total |
|--------|------|------|---------------|
| **Manual** | 5 hrs/analysis | $75/hr | $18,750 |
| **Data Detective** | 5 min/analysis | $0.10 | $41.67 |
| **Savings** | 245.8 hrs | - | **$18,708.33/mo** |

**Annual Savings**: $224,500

### Enterprise Data Team (200 analyses/month)

| Method | Time | Cost | Monthly Total |
|--------|------|------|---------------|
| **Manual** | 3 hrs/analysis | $60/hr | $36,000 |
| **Data Detective** | 5 min/analysis | $0.10 | $166.67 |
| **Savings** | 583.3 hrs | - | **$35,833.33/mo** |

**Annual Savings**: $430,000

---

## Certification Showcase

This module demonstrates expertise from:

### ✅ Microsoft Generative AI for Data Analysis
- AI-powered data insights
- Natural language to SQL concepts
- GenAI integration in analytics workflows
- Automated insight generation

### ✅ Google Data Analytics
- Data profiling and exploration
- Statistical analysis fundamentals
- Data visualization best practices
- Quality assessment methodologies

### ✅ IBM Business Intelligence Analyst
- Data quality frameworks
- Automated reporting concepts
- Dashboard design principles
- ETL thinking (clean → analyze → export)

### ✅ Vanderbilt Generative AI Strategic Leader
- Prompt engineering for data analysis
- AI-augmented decision making
- Business value communication
- Strategic AI implementation

---

## Comparison: Data Detective vs Alternatives

| Feature | Data Detective | Tableau Prep | Alteryx | Excel |
|---------|----------------|--------------|---------|-------|
| **Setup Time** | 0 min (cloud) | 30 min | 2 hrs | 0 min |
| **Cost** | $0.10/analysis | $70/user/mo | $5,195/yr | Included |
| **AI Insights** | ✅ Claude 3.5 | ❌ | ⚠️ Limited | ❌ |
| **Natural Language** | ✅ | ❌ | ❌ | ❌ |
| **Code Required** | ❌ | ❌ | ⚠️ Some | ⚠️ Formulas |
| **Export Formats** | CSV, Excel | Multiple | Multiple | Excel |
| **Learning Curve** | 5 min | 2-4 hrs | 8-16 hrs | 30 min |
| **Max Dataset Size** | 1M rows | 15M rows | Unlimited | 1M rows |

**Best For**: Quick insights, client audits, exploratory analysis, non-technical users

---

## Roadmap

### ✅ Launched (Current)
- CSV and Excel upload and parsing
- Automated data profiling
- Correlation matrix heatmap visualization
- AI insights with Claude
- Data quality assessment
- Natural language queries
- CSV/Excel export

### 🔜 Coming Soon (Phase 2)
- **PDF Report Generation**: Professional analysis reports
- **Multiple File Upload**: Compare datasets side-by-side
- **Advanced Visualizations**: Pair plots, scatter matrix plots
- **Scheduled Analysis**: Auto-analyze files on upload
- **Data Catalog**: Save and revisit past analyses

### 🔮 Future (Phase 3)
- **Database Connections**: Direct SQL database integration
- **API Data Sources**: Pull data from REST APIs
- **Collaborative Features**: Share insights with team
- **Custom AI Prompts**: Define your own insight templates
- **Predictive Analytics**: Basic forecasting and trend projection

---

## FAQ

### Q: Is my data safe?
**A**: Yes. All processing happens in your browser/server session. Only data summaries are sent to Claude API for insights (never raw data). API keys are session-only (never persisted).

### Q: How much does it cost?
**A**: Data Detective itself is free. You pay only for Claude API usage (~$0.01-0.03 per analysis). No subscription needed.

### Q: What size files can I upload?
**A**: Up to 50 MB recommended. Larger files work but may be slower. For AI insights, we recommend <10,000 rows for optimal speed.

### Q: Do I need coding skills?
**A**: No! Data Detective is designed for non-technical users. Upload CSV or Excel, click buttons, get insights.

### Q: Can I use it without AI features?
**A**: Yes! Data profiling, quality checks, and export work without API key. AI features are optional.

### Q: What about sensitive data?
**A**: For sensitive data, skip AI features (no external API calls). Use local profiling and quality checks only.

### Q: How accurate are AI insights?
**A**: Claude 3.5 Sonnet is highly capable, but always review insights. Use as a starting point, not final answer.

---

## Support & Resources

- **Documentation**: This README
- **GitHub Issues**: https://github.com/ChunkyTortoise/enterprise-hub/issues
- **Claude API Docs**: https://docs.anthropic.com/
- **Video Tutorial**: Coming soon

---

## Example Datasets for Testing

Try Data Detective with these sample datasets:

1. **Retail Sales**: https://www.kaggle.com/datasets/rohitsahoo/sales-forecasting
2. **Customer Data**: https://www.kaggle.com/datasets/blastchar/telco-customer-churn
3. **Marketing Campaigns**: https://www.kaggle.com/datasets/jackdaoud/marketing-data

Or use your own CSV files from:
- CRM exports (Salesforce, HubSpot)
- E-commerce platforms (Shopify, WooCommerce)
- Survey results (Google Forms, Typeform)
- Financial systems (QuickBooks, Xero)

---

## Conclusion

Data Detective transforms the tedious, hours-long process of manual data exploration into a **2-minute AI-powered experience**. Whether you're a consultant auditing client data, a data scientist starting a new project, or a business analyst exploring campaign performance, Data Detective delivers professional-grade insights in seconds.

**Start analyzing smarter, not harder.**

---

*Built by Cayman Roden | Powered by Claude 3.5 Sonnet | Part of Enterprise Hub*
