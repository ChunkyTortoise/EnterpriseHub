---
title: CSV to Dashboard in 10 Minutes with Streamlit
published: false
tags: python, streamlit, datascience, tutorial
---

# CSV to Dashboard in 10 Minutes with Streamlit

Business asks for a dashboard. You have a CSV. Building it with Tableau takes 2 hours. Writing HTML/CSS/JavaScript takes 2 days.

Streamlit takes 10 minutes.

I've built 7 production dashboards with Streamlit for a real estate AI platform. Here's the fastest path from CSV to interactive dashboard.

## The Challenge

You have messy data. You need:
- Summary statistics
- Interactive charts
- Filters and controls
- Shareable link
- Zero infrastructure

Traditional BI tools are overkill. Writing a web app from scratch is too slow.

Streamlit solves this: write Python, get a web app.

## Why Streamlit?

**Python-native**: No HTML, CSS, or JavaScript. Just Python.

**Interactive**: Widgets automatically trigger reruns. State management is handled for you.

**Fast iteration**: Save your file, see changes instantly.

**Free deployment**: Streamlit Community Cloud hosts public apps for free.

**Rich components**: Charts, maps, dataframes, metrics, layouts—all built-in.

## The 10-Minute Blueprint

Here's a complete working dashboard. Each step takes ~1 minute.

### Step 1: Setup (1 min)

```bash
pip install streamlit pandas plotly
touch app.py
```

### Step 2: Load Data (1 min)

```python
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sales Dashboard", layout="wide")
st.title("Sales Dashboard")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("sales.csv")
    df['date'] = pd.to_datetime(df['date'])
    return df

df = load_data()
```

The `@st.cache_data` decorator caches the result. Load once, reuse on every interaction.

### Step 3: Show Summary Stats (1 min)

```python
# Metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Revenue",
        f"${df['revenue'].sum():,.0f}",
        delta=f"{df['revenue'].pct_change().iloc[-1]*100:.1f}%"
    )

with col2:
    st.metric(
        "Total Orders",
        f"{len(df):,}",
        delta=f"{(len(df) - len(df[df['date'] < df['date'].max() - pd.Timedelta(days=30)])):,}"
    )

with col3:
    st.metric(
        "Avg Order Value",
        f"${df['revenue'].mean():,.2f}"
    )

with col4:
    st.metric(
        "Top Product",
        df.groupby('product')['revenue'].sum().idxmax()
    )
```

Four metrics in a row. Streamlit handles the layout.

### Step 4: Add Visualizations (2 min)

```python
import plotly.express as px

# Revenue over time
st.subheader("Revenue Trend")
daily_revenue = df.groupby('date')['revenue'].sum().reset_index()
fig = px.line(
    daily_revenue,
    x='date',
    y='revenue',
    title='Daily Revenue'
)
st.plotly_chart(fig, use_container_width=True)

# Revenue by product
st.subheader("Revenue by Product")
product_revenue = df.groupby('product')['revenue'].sum().sort_values(ascending=False)
fig = px.bar(
    product_revenue,
    x=product_revenue.index,
    y=product_revenue.values,
    labels={'x': 'Product', 'y': 'Revenue'},
    title='Top Products'
)
st.plotly_chart(fig, use_container_width=True)
```

Plotly charts are interactive by default. Hover, zoom, pan—all free.

### Step 5: Add Filters (2 min)

```python
# Sidebar filters
st.sidebar.header("Filters")

# Date range
date_range = st.sidebar.date_input(
    "Date Range",
    value=(df['date'].min(), df['date'].max()),
    min_value=df['date'].min(),
    max_value=df['date'].max()
)

# Product filter
products = st.sidebar.multiselect(
    "Products",
    options=df['product'].unique(),
    default=df['product'].unique()
)

# Apply filters
filtered_df = df[
    (df['date'] >= pd.to_datetime(date_range[0])) &
    (df['date'] <= pd.to_datetime(date_range[1])) &
    (df['product'].isin(products))
]

# Update all visualizations to use filtered_df instead of df
```

Sidebar controls keep the main view clean. Every interaction triggers a rerun with new filters.

### Step 6: Show Raw Data (1 min)

```python
# Data table
st.subheader("Raw Data")
st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "revenue": st.column_config.NumberColumn("Revenue", format="$%d"),
        "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD")
    }
)
```

Interactive table with sorting, searching, and custom formatting.

### Step 7: Add Download Button (1 min)

```python
# Download filtered data
st.download_button(
    label="Download CSV",
    data=filtered_df.to_csv(index=False),
    file_name="filtered_sales.csv",
    mime="text/csv"
)
```

Users can export filtered data for further analysis.

### Step 8: Run Locally (1 min)

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Make changes, see them instantly.

## Complete Code

Here's the full dashboard in ~60 lines:

```python
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sales Dashboard", layout="wide")
st.title("Sales Dashboard")

@st.cache_data
def load_data():
    df = pd.read_csv("sales.csv")
    df['date'] = pd.to_datetime(df['date'])
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("Filters")
date_range = st.sidebar.date_input(
    "Date Range",
    value=(df['date'].min(), df['date'].max())
)
products = st.sidebar.multiselect(
    "Products",
    options=df['product'].unique(),
    default=df['product'].unique()
)

# Apply filters
filtered_df = df[
    (df['date'] >= pd.to_datetime(date_range[0])) &
    (df['date'] <= pd.to_datetime(date_range[1])) &
    (df['product'].isin(products))
]

# Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${filtered_df['revenue'].sum():,.0f}")
col2.metric("Total Orders", f"{len(filtered_df):,}")
col3.metric("Avg Order Value", f"${filtered_df['revenue'].mean():,.2f}")
col4.metric("Top Product", filtered_df.groupby('product')['revenue'].sum().idxmax())

# Charts
st.subheader("Revenue Trend")
daily = filtered_df.groupby('date')['revenue'].sum().reset_index()
fig = px.line(daily, x='date', y='revenue')
st.plotly_chart(fig, use_container_width=True)

st.subheader("Revenue by Product")
by_product = filtered_df.groupby('product')['revenue'].sum().sort_values(ascending=False)
fig = px.bar(by_product, x=by_product.index, y=by_product.values)
st.plotly_chart(fig, use_container_width=True)

# Data table
st.subheader("Raw Data")
st.dataframe(filtered_df, use_container_width=True)

# Download
st.download_button(
    "Download CSV",
    filtered_df.to_csv(index=False),
    "sales.csv",
    "text/csv"
)
```

## Advanced Features

Once the basic dashboard works, add these:

### 1. Multiple Pages

```python
# pages/home.py
import streamlit as st
st.title("Home")

# pages/analytics.py
import streamlit as st
st.title("Analytics")
```

Streamlit automatically creates a sidebar navigation for files in `pages/`.

### 2. Custom Themes

```toml
# .streamlit/config.toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

### 3. Session State

```python
# Persist data across interactions
if 'counter' not in st.session_state:
    st.session_state.counter = 0

if st.button("Increment"):
    st.session_state.counter += 1

st.write(f"Counter: {st.session_state.counter}")
```

### 4. File Upload

```python
uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success(f"Loaded {len(df)} rows")
```

Users can upload their own data without code changes.

### 5. Authentication (Streamlit Cloud)

```python
# Restrict to certain users
if st.experimental_user.email not in ["admin@company.com"]:
    st.error("Access denied")
    st.stop()
```

Built-in auth for deployed apps.

## Real-World Example

Here's a dashboard I built for real estate lead analysis:

```python
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Lead Dashboard", layout="wide")

@st.cache_data
def load_leads():
    return pd.read_csv("leads.csv", parse_dates=['created_at'])

df = load_leads()

# Filters
st.sidebar.header("Filters")
temperature = st.sidebar.multiselect(
    "Lead Temperature",
    ["Hot", "Warm", "Cold"],
    default=["Hot", "Warm", "Cold"]
)
date_range = st.sidebar.slider(
    "Days Back",
    1, 90, 30
)

# Filter data
cutoff = pd.Timestamp.now() - pd.Timedelta(days=date_range)
filtered = df[
    (df['created_at'] >= cutoff) &
    (df['temperature'].isin(temperature))
]

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Leads", len(filtered))
col2.metric("Hot Leads", len(filtered[filtered['temperature'] == 'Hot']))
col3.metric("Conversion Rate", f"{(filtered['converted'].mean() * 100):.1f}%")
col4.metric("Avg Response Time", f"{filtered['response_minutes'].mean():.0f}m")

# Lead volume over time
st.subheader("Lead Volume")
daily = filtered.groupby(filtered['created_at'].dt.date).size()
fig = px.area(daily, x=daily.index, y=daily.values)
st.plotly_chart(fig, use_container_width=True)

# Conversion funnel
st.subheader("Conversion Funnel")
funnel_data = pd.DataFrame({
    'Stage': ['Leads', 'Qualified', 'Contacted', 'Converted'],
    'Count': [
        len(filtered),
        len(filtered[filtered['qualified']]),
        len(filtered[filtered['contacted']]),
        len(filtered[filtered['converted']])
    ]
})
fig = px.funnel(funnel_data, x='Count', y='Stage')
st.plotly_chart(fig, use_container_width=True)

# Top sources
st.subheader("Lead Sources")
sources = filtered['source'].value_counts()
fig = px.pie(values=sources.values, names=sources.index)
st.plotly_chart(fig, use_container_width=True)
```

This dashboard helped us identify that:
- 73% of hot leads came from Zillow
- Response time >15min dropped conversion by 40%
- Cold leads had 2% conversion (stopped spending on them)

Those insights drove $180K in revenue optimization.

## Deployment

Deploy to Streamlit Community Cloud in 3 steps:

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo, select `app.py`, click Deploy

Your dashboard is now live at `your-app.streamlit.app`.

For private deployments, use:
- **Streamlit Cloud** (Teams plan, $250/mo)
- **AWS/GCP**: Run with Docker
- **Heroku**: One-click deploy

## Tips for Production Dashboards

1. **Cache everything**: Use `@st.cache_data` for data loading, `@st.cache_resource` for model loading
2. **Add error handling**: Wrap data operations in try/except
3. **Show loading states**: Use `st.spinner("Loading...")` for slow operations
4. **Optimize queries**: Filter data before loading, use indexes
5. **Add tooltips**: Use `help` parameter to explain metrics
6. **Test on mobile**: Streamlit is responsive but test layout on small screens
7. **Monitor usage**: Add analytics to track which features users actually use

## Common Mistakes

**Don't:** Load data on every interaction
```python
df = pd.read_csv("big_file.csv")  # Loads on every click!
```

**Do:** Cache it
```python
@st.cache_data
def load_data():
    return pd.read_csv("big_file.csv")
```

**Don't:** Store large objects in session_state
```python
st.session_state.df = huge_dataframe  # Slows down app
```

**Do:** Cache and reference
```python
@st.cache_data
def get_df():
    return huge_dataframe
```

## When NOT to Use Streamlit

Streamlit is great for dashboards. It's not great for:
- Complex multi-step workflows (use Flask/FastAPI)
- Real-time updates (use WebSockets)
- Mobile apps (use React Native)
- Pixel-perfect designs (use custom frontend)

## Try It Yourself

I've built 7 production Streamlit dashboards:

- **InsightEngine**: ML model observatory ([ct-insight-engine.streamlit.app](https://ct-insight-engine.streamlit.app))
- **DocQA**: Document Q&A with RAG ([ct-document-engine.streamlit.app](https://ct-document-engine.streamlit.app))
- **Scrape & Serve**: Web scraping monitor ([ct-scrape-and-serve.streamlit.app](https://ct-scrape-and-serve.streamlit.app))

All repos are on GitHub: [ChunkyTortoise](https://github.com/ChunkyTortoise)

Want a starter kit? I packaged the blueprint above with:
- Multi-page template
- 10 chart types
- Auth integration
- Deployment config
- $50 one-time

## Questions?

- What dashboards have you built with Streamlit?
- What features would you add to the blueprint?
- What BI tools are you replacing?

Share in the comments!

---

*Building data tools that don't suck. Follow for more Python, dashboards, and practical data engineering.*
