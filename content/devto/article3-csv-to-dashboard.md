---
title: From CSV to Dashboard in 30 Seconds with Python
published: false
tags: python, streamlit, datascience, tutorial
---

# From CSV to Dashboard in 30 Seconds with Python

Business wants a dashboard. You have a CSV. Building it with Tableau takes hours. Writing React takes days.

Streamlit takes 30 seconds.

I've built 7 production dashboards with Streamlit. Here's the fastest path from CSV to interactive dashboard.

## The 30-Second Blueprint

```python
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard", layout="wide")

# 1. Load data (2 seconds)
df = pd.read_csv("data.csv")

# 2. Show metrics (5 seconds)
cols = st.columns(4)
cols[0].metric("Total", df.shape[0])
cols[1].metric("Revenue", f"${df['revenue'].sum():,.0f}")
cols[2].metric("Avg Order", f"${df['revenue'].mean():,.2f}")
cols[3].metric("Top Product", df['product'].mode()[0])

# 3. Add chart (10 seconds)
fig = px.bar(df.groupby('product')['revenue'].sum(), title="Revenue by Product")
st.plotly_chart(fig, use_container_width=True)

# 4. Show data (5 seconds)
st.dataframe(df, use_container_width=True)

# 5. Add filter (5 seconds)
selected = st.selectbox("Filter by Product", df['product'].unique())
st.dataframe(df[df['product'] == selected])
```

That's it. 30 seconds from CSV to dashboard.

## Why Streamlit?

| Feature | Streamlit | Tableau | Custom React |
|---------|-----------|---------|--------------|
| Setup time | 1 minute | 1 hour | 1 day |
| Code required | 10 lines | GUI | 500+ lines |
| Deployment | Free cloud | $$$ | Infrastructure |
| Customization | Python | Limited | Complete |
| Learning curve | 1 hour | 4 hours | 40 hours |

## Auto-Profiling with Pandas Profiling

For faster exploration, use pandas profiling:

```python
import streamlit as st
from pandas_profiling import ProfileReport
from streamlit_pandas_profiling import st_profile_report

# Load data
df = pd.read_csv("data.csv")

# Generate profile
profile = ProfileReport(df, explorative=True)

# Show in Streamlit
st_profile_report(profile)
```

This automatically generates:
- Summary statistics
- Correlation matrices
- Histograms and distributions
- Missing value analysis
- Data type detection

## Chart Detection

Automatically suggest charts based on data types:

```python
import streamlit as st
import pandas as pd
import plotly.express as px

def suggest_charts(df):
    """Auto-suggest charts based on data types."""
    charts = []
    
    numeric_cols = df.select_dtypes(include=['number']).columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    datetime_cols = df.select_dtypes(include=['datetime']).columns
    
    # Numeric vs Numeric → Scatter
    if len(numeric_cols) >= 2:
        charts.append({
            'type': 'scatter',
            'x': numeric_cols[0],
            'y': numeric_cols[1],
            'title': f"{numeric_cols[0]} vs {numeric_cols[1]}"
        })
    
    # Categorical vs Numeric → Bar
    if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
        charts.append({
            'type': 'bar',
            'x': categorical_cols[0],
            'y': numeric_cols[0],
            'title': f"{numeric_cols[0]} by {categorical_cols[0]}"
        })
    
    # Datetime vs Numeric → Line
    if len(datetime_cols) >= 1 and len(numeric_cols) >= 1:
        charts.append({
            'type': 'line',
            'x': datetime_cols[0],
            'y': numeric_cols[0],
            'title': f"{numeric_cols[0]} over Time"
        })
    
    return charts

# Auto-generate charts
df = pd.read_csv("data.csv")
suggestions = suggest_charts(df)

for chart in suggestions:
    if chart['type'] == 'scatter':
        fig = px.scatter(df, x=chart['x'], y=chart['y'], title=chart['title'])
    elif chart['type'] == 'bar':
        fig = px.bar(df, x=chart['x'], y=chart['y'], title=chart['title'])
    elif chart['type'] == 'line':
        fig = px.line(df, x=chart['x'], y=chart['title'])
    
    st.plotly_chart(fig, use_container_width=True)
```

## Complete Dashboard Template

Here's a production-ready template:

```python
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="Analytics Dashboard",
    layout="wide",
    page_icon="📊"
)

# Cache data loading
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df['date'] = pd.to_datetime(df['date'])
    return df

# Load data
df = load_data()

# Sidebar filters
st.sidebar.header("Filters")

# Date range
date_range = st.sidebar.date_input(
    "Date Range",
    value=(df['date'].min(), df['date'].max()),
    min_value=df['date'].min(),
    max_value=df['date'].max()
)

# Category filter
categories = st.sidebar.multiselect(
    "Categories",
    options=df['category'].unique(),
    default=df['category'].unique()
)

# Apply filters
filtered = df[
    (df['date'] >= pd.to_datetime(date_range[0])) &
    (df['date'] <= pd.to_datetime(date_range[1])) &
    (df['category'].isin(categories))
]

# Main content
st.title("📊 Analytics Dashboard")

# KPI row
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    "Total Revenue",
    f"${filtered['revenue'].sum():,.0f}",
    delta=f"{(filtered['revenue'].sum() / df['revenue'].sum() - 1) * 100:.1f}%"
)

kpi2.metric(
    "Orders",
    f"{len(filtered):,}",
    delta=f"{(len(filtered) / len(df) - 1) * 100:.1f}%"
)

kpi3.metric(
    "Avg Order Value",
    f"${filtered['revenue'].mean():,.2f}"
)

kpi4.metric(
    "Best Category",
    filtered.groupby('category')['revenue'].sum().idxmax()
)

# Charts row
st.subheader("📈 Trends")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Revenue Over Time")
    daily = filtered.groupby(filtered['date'].dt.date)['revenue'].sum()
    fig = px.line(
        daily,
        x=daily.index,
        y=daily.values,
        labels={'x': 'Date', 'y': 'Revenue'},
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Revenue by Category")
    cat_rev = filtered.groupby('category')['revenue'].sum()
    fig = px.pie(
        cat_rev,
        values=cat_rev.values,
        names=cat_rev.index,
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

# Data table
st.subheader("📋 Raw Data")

with st.expander("Show raw data"):
    st.dataframe(
        filtered,
        use_container_width=True,
        column_config={
            "revenue": st.column_config.NumberColumn(
                "Revenue",
                format="$%d"
            ),
            "date": st.column_config.DateColumn(
                "Date",
                format="YYYY-MM-DD"
            )
        }
    )

# Download
st.download_button(
    label="Download Filtered Data",
    data=filtered.to_csv(index=False),
    file_name="filtered_data.csv",
    mime="text/csv"
)
```

## Advanced Features

### 1. Auto-Refresh

```python
import streamlit as st
from time import sleep

refresh_interval = st.slider("Refresh interval (seconds)", 30, 300, 60)

placeholder = st.empty()

for _ in range(100):  # Refresh 100 times
    df = load_data()
    placeholder.metric("Total", df.shape[0])
    sleep(refresh_interval)
```

### 2. Session State

```python
if 'counter' not in st.session_state:
    st.session_state.counter = 0

def increment():
    st.session_state.counter += 1

st.button("Increment", on_click=increment)
st.write(f"Count: {st.session_state.counter}")
```

### 3. File Upload

```python
uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success(f"Loaded {len(df)} rows")
    st.dataframe(df)
```

### 4. Caching

```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data_from_api():
    return pd.read_csv("https://api.example.com/data.csv")

@st.cache_resource
def load_model():
    return load_my_ml_model()
```

### 5. Authentication

```python
if st.experimental_user.email not in ["admin@company.com"]:
    st.error("Access denied")
    st.stop()
```

## Performance Tips

### 1. Cache Everything

```python
@st.cache_data
def load_data():
    return pd.read_csv("large_file.csv")
```

### 2. Use Column Configuration

```python
st.dataframe(
    df,
    column_config={
        "revenue": st.column_config.NumberColumn(format="$%d"),
        "date": st.column_config.DateColumn(format="YYYY-MM-DD")
    }
)
```

### 3. Limit Rows

```python
st.dataframe(df.head(100))  # Show first 100 only
```

### 4. Use @st.fragment

```python
@st.fragment
def filter_section():
    category = st.selectbox("Category", df['category'].unique())
    st.dataframe(df[df['category'] == category])

filter_section()  # Updates independently
```

## Deployment

Deploy to Streamlit Community Cloud in 3 steps:

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo, select `app.py`, click Deploy

Your dashboard is now live at `your-app.streamlit.app`.

## Real-World Examples

Here are dashboards I've built:

| Dashboard | Use Case | Tech |
|-----------|----------|------|
| [ct-insight-engine.streamlit.app](https://ct-insight-engine.streamlit.app) | Auto-dashboard from CSV | Streamlit + Pandas Profiling |
| [ct-document-engine.streamlit.app](https://ct-document-engine.streamlit.app) | Document Q&A | Streamlit + RAG |
| [ct-agentforge.streamlit.app](https://ct-agentforge.streamlit.app) | Agent testing | Streamlit + AgentForge |

## When NOT to Use Streamlit

Streamlit is great for dashboards. Not for:

- **Complex workflows**: Use FastAPI
- **Real-time updates**: Use WebSockets
- **Mobile apps**: Use React Native
- **Pixel-perfect designs**: Use custom frontend

## Try It Yourself

**Starter kit** with:
- Multi-page template
- 10 chart types
- Auth integration
- Deployment config

Get it on Gumroad: [insight-engine starter kit](https://gumroad.com/l/insight-engine)

---

*Building AI tools that actually work. Follow for more posts on Streamlit, dashboards, and data engineering.*