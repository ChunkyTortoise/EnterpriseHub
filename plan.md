# Plan for "Financial Analyst" Module Overhaul

I have analyzed `modules/financial_analyst.py` and its tests. The module is functional but mixes calculation logic with UI rendering, making it harder to maintain and test rigorously.

## Proposed Improvements

1.  **Refactor Logic**:
    *   Extract the **DCF Valuation** logic into a standalone, pure function/class `DCFModel`. This separates financial math from Streamlit widgets.
    *   Extract **YoY Growth** and **Profitability** calculations into dedicated helper functions.
2.  **Type Safety**:
    *   Introduce `TypedDict` or `dataclass` definitions for `CompanyInfo` and `FinancialData` to replace loose dictionaries. This ensures we know exactly what data fields to expect.
3.  **Robustness**:
    *   Improve the "Column Detection" logic (finding "Revenue", "Net Income", "Free Cash Flow" in dataframes) with a more robust, centralized utility instead of repeated ad-hoc string matching.
4.  **AI Integration**:
    *   Externalize the Anthropic prompt construction to a clearer `PromptBuilder` pattern, making it easier to iterate on the AI persona without touching the rendering code.
5.  **Documentation**:
    *   Add comprehensive docstrings and type hints to all new functions.

## Verification
*   I will run the existing `tests/unit/test_financial_analyst.py` to ensure no regressions.
*   I may need to slightly adjust the tests to align with the refactored structure (e.g., testing the new `DCFModel` class directly).

**Goal**: A cleaner, more professional module where the financial engine is distinct from the dashboard display.

Shall I proceed with this plan?
