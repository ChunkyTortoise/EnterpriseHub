"""
ROI Logic Utility
Centralized math for ROI calculations to ensure consistency and testability.
"""


def calculate_automation_roi(leads_day: float, hours_per_lead: float, hourly_rate: float, automation_pct: float):
    """
    Calculates ROI for automation scenarios (Service 4).
    """
    total_weekly_hours = (leads_day * 5) * hours_per_lead
    hours_saved = total_weekly_hours * (automation_pct / 100)
    weekly_savings = hours_saved * hourly_rate
    annual_savings = weekly_savings * 52
    return {
        "total_weekly_hours": total_weekly_hours,
        "hours_saved": hours_saved,
        "weekly_savings": weekly_savings,
        "annual_savings": annual_savings,
    }


def calculate_data_roi(arr_m: float, churn_rate: float, ai_reduction: float):
    """
    Calculates ROI for data/churn reduction scenarios (Service 8).
    """
    arr = arr_m * 1_000_000
    churn_loss = arr * (churn_rate / 100)
    recovered_revenue = churn_loss * (ai_reduction / 100)
    return {"arr": arr, "churn_loss": churn_loss, "recovered_revenue": recovered_revenue}


def calculate_marketing_roi(posts_count: int, traffic_per_post: float, conv_rate: float, ltv: float):
    """
    Calculates ROI for programmatic SEO scenarios (Service 12).
    """
    total_traffic = posts_count * traffic_per_post
    conversions = total_traffic * (conv_rate / 100)
    monthly_value = conversions * ltv
    annualized_value = monthly_value * 12
    return {
        "total_traffic": total_traffic,
        "conversions": conversions,
        "monthly_value": monthly_value,
        "annualized_value": annualized_value,
    }


def calculate_strategic_roi(budget: float, waste_pct: float):
    """
    Calculates ROI for strategic oversight scenarios (Service 25).
    """
    prevented_waste = budget * (waste_pct / 100)
    return {"prevented_waste": prevented_waste}
