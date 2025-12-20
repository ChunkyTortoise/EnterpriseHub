"""
data_source_faker.py

Generates simulated marketing campaign data to mimic real API responses
without requiring actual API keys or live connections.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_campaign_data(
    platform: str,
    start_date: str = "2023-01-01",
    days: int = 90,
    base_impressions: int = 100000,
    base_cpc: float = 0.5, # Cost Per Click
    base_ctr: float = 0.01, # Click Through Rate
    base_conversion_rate: float = 0.02,
    conversion_value: float = 50.0
) -> pd.DataFrame:
    """
    Generates simulated marketing campaign data for a given platform.

    Args:
        platform (str): 'Google Ads' or 'Meta Ads'.
        start_date (str): Start date of the campaign data (YYYY-MM-DD).
        days (int): Number of days to generate data for.
        base_impressions (int): Average daily impressions.
        base_cpc (float): Average cost per click.
        base_ctr (float): Average click-through rate.
        base_conversion_rate (float): Average conversion rate.
        conversion_value (float): Average value per conversion.

    Returns:
        pd.DataFrame: Simulated campaign data.
    """
    dates = [datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=i) for i in range(days)]
    
    data = []
    for date in dates:
        # Introduce daily variations
        impressions = max(0, base_impressions + np.random.normal(0, base_impressions * 0.1))
        clicks = impressions * (base_ctr + np.random.normal(0, base_ctr * 0.1))
        clicks = max(0, clicks)
        
        cost_per_click = base_cpc + np.random.normal(0, base_cpc * 0.1)
        cost_per_click = max(0.01, cost_per_click) # Ensure CPC is not zero
        
        spend = clicks * cost_per_click
        
        conversions = clicks * (base_conversion_rate + np.random.normal(0, base_conversion_rate * 0.1))
        conversions = max(0, conversions)
        
        revenue = conversions * conversion_value
        
        data.append({
            "Date": date,
            "Platform": platform,
            "Impressions": int(impressions),
            "Clicks": int(clicks),
            "Spend": round(spend, 2),
            "Conversions": int(conversions),
            "Revenue": round(revenue, 2),
            "CPC": round(cost_per_click, 2),
            "CTR": round(clicks / impressions if impressions > 0 else 0, 4),
            "Conversion_Rate": round(conversions / clicks if clicks > 0 else 0, 4),
            "ROAS": round(revenue / spend if spend > 0 else 0, 2)
        })

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    st.header("Marketing Data Faker Demo")
    
    platform_choice = st.selectbox("Select Platform", ["Google Ads", "Meta Ads"])
    start_date_choice = st.date_input("Start Date", value=datetime(2023, 1, 1))
    days_choice = st.slider("Number of Days", 30, 365, 90)
    
    if st.button("Generate Data"):
        simulated_data = generate_campaign_data(
            platform=platform_choice,
            start_date=start_date_choice.strftime("%Y-%m-%d"),
            days=days_choice
        )
        st.write(f"### Simulated {platform_choice} Data ({days_choice} Days)")
        st.dataframe(simulated_data)
        
        st.download_button(
            label="Download Data as CSV",
            data=simulated_data.to_csv(index=False).encode('utf-8'),
            file_name=f"{platform_choice.lower().replace(' ', '_')}_simulated_data.csv",
            mime="text/csv"
        )
