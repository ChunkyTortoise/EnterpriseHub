"""
ROI Calculator Service
Provides detailed financial modeling for real estate investments.
Calculates cash flow, tax benefits, and long-term appreciation.
"""

from typing import Dict, List, Any
from pydantic import BaseModel

class InvestmentProjection(BaseModel):
    year: int
    cash_flow: float
    equity: float
    tax_savings: float
    roi_annual: float

class ROICalculatorService:
    def calculate_10yr_projection(
        self, 
        purchase_price: float, 
        down_payment_pct: float,
        monthly_rent: float,
        annual_expenses: float,
        appreciation_rate: float = 0.04
    ) -> List[InvestmentProjection]:
        """Generates a 10-year investment projection."""
        projections = []
        loan_amount = purchase_price * (1 - down_payment_pct)
        current_value = purchase_price
        
        for year in range(1, 11):
            current_value *= (1 + appreciation_rate)
            annual_rent = monthly_rent * 12 * (1.03 ** (year-1)) # 3% rent growth
            
            # Simplified cash flow
            mortgage_payment = (loan_amount * 0.07) # 7% interest simplified
            cash_flow = annual_rent - annual_expenses - mortgage_payment
            
            equity = current_value - loan_amount # Simplified (no principal paydown)
            
            projections.append(InvestmentProjection(
                year=year,
                cash_flow=round(cash_flow, 2),
                equity=round(equity, 2),
                tax_savings=round(annual_expenses * 0.25, 2), # 25% tax bracket
                roi_annual=round((cash_flow / (purchase_price * down_payment_pct)) * 100, 2)
            ))
            
        return projections

roi_calculator = ROICalculatorService()
