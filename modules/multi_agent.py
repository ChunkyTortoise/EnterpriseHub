"""
Multi-Agent Workflow Orchestrator.

This module acts as the central command center, coordinating specialized 'agents'
(logical units) to perform complex, multi-step analysis workflows.
"""

import os
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

import pandas as pd
import streamlit as st

import utils.ui as ui
from utils.data_loader import get_stock_data, calculate_indicators, get_company_info, get_news
from utils.exceptions import DataFetchError, InvalidTickerError
from utils.logger import get_logger
from utils.sentiment_analyzer import process_news_sentiment

# Conditional import for Claude API
try:
    from anthropic import (
        Anthropic,
        APIConnectionError,
        APIError,
        APITimeoutError,
        RateLimitError,
    )

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = get_logger(__name__)

# Constants for API
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
DEFAULT_MAX_TOKENS = 2048
MAX_RETRY_ATTEMPTS = 3
INITIAL_RETRY_DELAY = 1.0
RETRY_BACKOFF_FACTOR = 2.0
API_TIMEOUT = 30.0

# Default S&P 500 tickers for Market Scanner
DEFAULT_TICKERS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    "BRK.B",
    "JPM",
    "V",
    "JNJ",
    "WMT",
    "PG",
    "MA",
    "HD",
    "CVX",
    "MRK",
    "KO",
    "PEP",
    "ABBV",
]


def retry_with_exponential_backoff(
    max_attempts: int = MAX_RETRY_ATTEMPTS,
    initial_delay: float = INITIAL_RETRY_DELAY,
    backoff_factor: float = RETRY_BACKOFF_FACTOR,
) -> Callable:
    """
    Decorator to retry a function with exponential backoff on failure.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay after each retry

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    last_exception = e
                    logger.warning(
                        f"Rate limit hit on attempt {attempt}/{max_attempts}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    if attempt < max_attempts:
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        raise
                except (APIConnectionError, APITimeoutError) as e:
                    last_exception = e
                    logger.warning(
                        f"Connection/timeout error on attempt {attempt}/{max_attempts}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    if attempt < max_attempts:
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        raise
                except APIError as e:
                    logger.error(f"Non-retryable API error: {str(e)}")
                    raise
                except Exception as e:
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
                    raise

            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def render() -> None:
    """Render the Multi-Agent Orchestrator interface."""
    ui.section_header("🤖 Multi-Agent Workflows", "Autonomous Analysis Teams")

    # Workflow Selection
    workflow = st.selectbox(
        "Select Workflow",
        [
            "💰 Stock Deep Dive (4 Agents)",
            "📊 Market Scanner (4 Agents)",
            "📢 Content Generator (4 Agents)",
        ],
    )

    if workflow == "💰 Stock Deep Dive (4 Agents)":
        _render_stock_deep_dive()
    elif workflow == "📊 Market Scanner (4 Agents)":
        _render_market_scanner()
    elif workflow == "📢 Content Generator (4 Agents)":
        _render_content_generator()


def _render_stock_deep_dive() -> None:
    """Execute the Stock Deep Dive workflow."""
    st.markdown("""
    **Mission:** Comprehensive analysis of a target asset.

    **The Team:**
    - 🕵️ **DataBot:** Fetches raw price action and fundamental data.
    - 📈 **TechBot:** Analyzes technical indicators (RSI, MACD, Trends).
    - 📰 **NewsBot:** Scouts recent news and analyzes sentiment.
    - 🎓 **ChiefBot:** Synthesizes all intelligence into a final verdict.
    """)

    col1, col2 = st.columns([1, 4])
    with col1:
        ticker = st.text_input("Target Asset", value="NVDA").upper()

    start_btn = st.button("🚀 Launch Workflow", type="primary")

    if start_btn and ticker:
        _run_deep_dive_logic(ticker)


def _run_deep_dive_logic(ticker: str) -> None:
    """Orchestrate the deep dive agents."""

    # Container for live updates
    status_container = st.container()

    results: Dict[str, Any] = {}

    try:
        # --- AGENT 1: DATABOT ---
        with status_container:
            with st.spinner("🕵️ DataBot: Infiltrating exchanges..."):
                time.sleep(0.5)  # UX pause
                df = get_stock_data(ticker, period="1y", interval="1d")
                info = get_company_info(ticker)

                if df is None or df.empty:
                    st.error(f"❌ DataBot: Mission Failed. No data for {ticker}.")
                    return

                results["price"] = df.iloc[-1]["Close"]
                results["info"] = info
                st.success(
                    f"🕵️ DataBot: Data secured. Price: ${results['price']:.2f} | "
                    f"Sector: {info.get('sector', 'Unknown')}"
                )

        # --- AGENT 2: TECHBOT ---
        with status_container:
            with st.spinner("📈 TechBot: Crunching numbers..."):
                time.sleep(0.5)
                df = calculate_indicators(df)

                last_row = df.iloc[-1]
                rsi = last_row["RSI"]
                macd = last_row["MACD"]
                signal = last_row["Signal_Line"]

                results["rsi"] = rsi
                results["macd_signal"] = "BULLISH" if macd > signal else "BEARISH"

                rsi_status = (
                    "OVERSOLD (Buy Signal)"
                    if rsi < 30
                    else "OVERBOUGHT (Sell Signal)"
                    if rsi > 70
                    else "NEUTRAL"
                )

                st.success(
                    f"📈 TechBot: Analysis complete. RSI: {rsi:.1f} ({rsi_status}) | "
                    f"MACD: {results['macd_signal']}"
                )

        # --- AGENT 3: NEWSBOT ---
        with status_container:
            with st.spinner("📰 NewsBot: Scanning global wires..."):
                time.sleep(0.5)
                news = get_news(ticker)
                sentiment = process_news_sentiment(news)

                results["sentiment_score"] = sentiment["average_score"]
                results["sentiment_verdict"] = sentiment["verdict"]

                st.success(
                    f"📰 NewsBot: {sentiment['article_count']} intel reports analyzed. "
                    f"Verdict: {sentiment['verdict']} "
                    f"(Score: {sentiment['average_score']:.2f})"
                )

        # --- AGENT 4: CHIEFBOT (Synthesis) ---
        st.markdown("---")
        st.subheader(f"🎓 ChiefBot Executive Summary: {ticker}")

        # Scoring Logic
        score = 0
        reasons = []

        # Technical Score
        if results["rsi"] < 35:
            score += 1
            reasons.append("Asset is Oversold (RSI < 35)")
        elif results["rsi"] > 65:
            score -= 1
            reasons.append("Asset is Overbought (RSI > 65)")

        if results["macd_signal"] == "BULLISH":
            score += 1
            reasons.append("MACD Momentum is Bullish")
        else:
            score -= 1
            reasons.append("MACD Momentum is Bearish")

        # Sentiment Score
        if results["sentiment_score"] > 0.15:
            score += 1
            reasons.append("News Sentiment is Positive")
        elif results["sentiment_score"] < -0.15:
            score -= 1
            reasons.append("News Sentiment is Negative")

        # Final Verdict
        if score >= 2:
            verdict = "STRONG BUY"
            color = "success"
        elif score == 1:
            verdict = "BUY"
            color = "success"
        elif score == 0:
            verdict = "HOLD"
            color = "warning"
        elif score == -1:
            verdict = "SELL"
            color = "danger"
        else:
            verdict = "STRONG SELL"
            color = "danger"

        # Display Final Card
        st.markdown(
            f"""
        <div style="padding: 20px; border-radius: 10px;
                    border: 2px solid #e0e0e0; background-color: #f9f9f9;">
            <h2 style="text-align: center; margin-top: 0;">RECOMMENDATION:
                <span style="color: {ui.THEME.get(color, "black")}">{verdict}</span></h2>
            <p style="text-align: center; font-size: 1.2em;">
                Confidence Score: {score}/3 Factors</p>
            <hr>
            <h4>📋 Key Drivers:</h4>
            <ul>
                {"".join([f"<li>{r}</li>" for r in reasons])}
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Expandable Data details
        with st.expander("🔍 Inspect Raw Intelligence"):
            st.write(results)

    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        st.error(f"❌ Mission Aborted: {str(e)}")


def _render_market_scanner() -> None:
    """Execute the Market Scanner workflow."""
    st.markdown("""
    **Mission:** Scan multiple stocks to find top opportunities.

    **The Team:**
    - 📋 **TickerBot:** Collects target ticker list from user or defaults.
    - 📊 **DataBot:** Fetches OHLCV data for all tickers in parallel.
    - 🔍 **ScreenerBot:** Applies technical filters (RSI, MA, Volume).
    - 🏆 **RankerBot:** Scores and ranks top 10 opportunities.
    """)

    # User input for tickers
    col1, col2 = st.columns([2, 1])
    with col1:
        ticker_input = st.text_area(
            "Enter Tickers (comma-separated)",
            value=", ".join(DEFAULT_TICKERS[:10]),
            height=100,
            help="Enter stock symbols separated by commas. Leave default for top S&P 500 stocks.",
        )
    with col2:
        st.markdown("**Quick Examples:**")
        st.markdown("- Tech: AAPL, MSFT, GOOGL")
        st.markdown("- Finance: JPM, BAC, GS")
        st.markdown("- Energy: XOM, CVX, COP")

    # Filter settings
    st.markdown("### 🔧 Filter Settings")
    col1, col2, col3 = st.columns(3)
    with col1:
        rsi_threshold = st.slider("RSI < (Oversold)", 20, 40, 30)
    with col2:
        volume_multiplier = st.slider("Volume > Avg (x)", 1.0, 3.0, 1.5)
    with col3:
        price_above_ma = st.checkbox("Price > MA20", value=True)

    start_btn = st.button("🚀 Launch Scanner", type="primary")

    if start_btn and ticker_input:
        _run_market_scanner_logic(ticker_input, rsi_threshold, volume_multiplier, price_above_ma)


def _run_market_scanner_logic(
    ticker_input: str, rsi_threshold: int, volume_multiplier: float, price_above_ma: bool
) -> None:
    """
    Orchestrate the market scanner agents.

    Args:
        ticker_input: Comma-separated ticker symbols
        rsi_threshold: Maximum RSI for oversold filter
        volume_multiplier: Minimum volume multiplier vs average
        price_above_ma: Whether to filter for price above MA20
    """
    status_container = st.container()
    results: Dict[str, Any] = {}

    try:
        # --- AGENT 1: TICKERBOT ---
        with status_container:
            with st.status("📋 TickerBot: Collecting target list...", expanded=True) as status:
                time.sleep(0.3)
                tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
                tickers = list(set(tickers))  # Remove duplicates

                results["tickers"] = tickers
                status.update(
                    label=f"📋 TickerBot: {len(tickers)} tickers collected", state="complete"
                )
                ticker_preview = f"Target list: {', '.join(tickers[:10])}"
                if len(tickers) > 10:
                    ticker_preview += "..."
                st.success(ticker_preview)

        # --- AGENT 2: DATABOT ---
        with status_container:
            with st.status("📊 DataBot: Fetching market data...", expanded=True) as status:
                ticker_data = {}
                failed_tickers = []
                progress_bar = st.progress(0)

                for i, ticker in enumerate(tickers):
                    try:
                        df = get_stock_data(ticker, period="3mo", interval="1d")
                        if df is not None and not df.empty:
                            df = calculate_indicators(df)
                            ticker_data[ticker] = df
                        else:
                            failed_tickers.append(ticker)
                    except (InvalidTickerError, DataFetchError) as e:
                        logger.warning(f"Failed to fetch {ticker}: {e}")
                        failed_tickers.append(ticker)
                    except Exception as e:
                        logger.error(f"Unexpected error fetching {ticker}: {e}")
                        failed_tickers.append(ticker)

                    progress_bar.progress((i + 1) / len(tickers))
                    time.sleep(0.1)  # Rate limiting

                results["ticker_data"] = ticker_data
                results["failed_tickers"] = failed_tickers

                status.update(
                    label=f"📊 DataBot: {len(ticker_data)}/{len(tickers)} datasets secured",
                    state="complete",
                )
                if failed_tickers:
                    st.warning(f"⚠️ Failed to fetch: {', '.join(failed_tickers)}")
                st.success(f"Successfully loaded {len(ticker_data)} stocks")

        # --- AGENT 3: SCREENERBOT ---
        with status_container:
            with st.status("🔍 ScreenerBot: Applying filters...", expanded=True) as status:
                time.sleep(0.3)
                screened_stocks = []

                for ticker, df in ticker_data.items():
                    try:
                        last_row = df.iloc[-1]
                        avg_volume = df["Volume"].tail(20).mean()

                        # Apply filters
                        passes = True
                        reasons = []

                        # RSI filter
                        rsi = last_row["RSI"]
                        if rsi >= rsi_threshold:
                            passes = False
                        else:
                            reasons.append(f"RSI {rsi:.1f} < {rsi_threshold}")

                        # Volume filter
                        current_volume = last_row["Volume"]
                        if current_volume < avg_volume * volume_multiplier:
                            passes = False
                        else:
                            reasons.append(
                                f"Volume {current_volume / 1e6:.1f}M > {volume_multiplier}x avg"
                            )

                        # MA20 filter
                        if price_above_ma:
                            ma20 = last_row["MA20"]
                            price = last_row["Close"]
                            if price <= ma20:
                                passes = False
                            else:
                                reasons.append(f"Price ${price:.2f} > MA20 ${ma20:.2f}")

                        if passes:
                            screened_stocks.append(
                                {
                                    "Ticker": ticker,
                                    "Price": last_row["Close"],
                                    "RSI": rsi,
                                    "Volume": current_volume,
                                    "MA20": last_row["MA20"],
                                    "Reasons": " | ".join(reasons),
                                }
                            )
                    except Exception as e:
                        logger.warning(f"Error screening {ticker}: {e}")
                        continue

                results["screened_stocks"] = screened_stocks
                status.update(
                    label=f"🔍 ScreenerBot: {len(screened_stocks)} stocks passed filters",
                    state="complete",
                )
                st.success(f"{len(screened_stocks)} opportunities identified")

        # --- AGENT 4: RANKERBOT ---
        with status_container:
            with st.status("🏆 RankerBot: Ranking opportunities...", expanded=True) as status:
                time.sleep(0.3)

                if not screened_stocks:
                    status.update(label="🏆 RankerBot: No opportunities found", state="error")
                    st.error("❌ No stocks passed the filters. Try adjusting criteria.")
                    return

                # Score each stock (lower RSI = better, higher volume = better)
                for stock in screened_stocks:
                    # Scoring: Inverse RSI (lower is better) + volume rank
                    rsi_score = (rsi_threshold - stock["RSI"]) / rsi_threshold
                    volume_score = stock["Volume"] / max([s["Volume"] for s in screened_stocks])
                    stock["Score"] = rsi_score * 0.6 + volume_score * 0.4

                # Sort by score descending
                screened_stocks.sort(key=lambda x: x["Score"], reverse=True)
                top_10 = screened_stocks[:10]

                results["top_opportunities"] = top_10
                status.update(label="🏆 RankerBot: Ranking complete", state="complete")
                st.success(f"Top {len(top_10)} opportunities ranked")

        # Display Results
        st.markdown("---")
        st.subheader("🎯 Top Opportunities")

        # Create DataFrame for display
        display_df = pd.DataFrame(top_10)
        display_df = display_df[["Ticker", "Price", "RSI", "Score", "Reasons"]]
        display_df["Price"] = display_df["Price"].apply(lambda x: f"${x:.2f}")
        display_df["RSI"] = display_df["RSI"].apply(lambda x: f"{x:.1f}")
        display_df["Score"] = display_df["Score"].apply(lambda x: f"{x:.3f}")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Summary stats
        st.markdown("### 📊 Scan Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Scanned", len(tickers))
        with col2:
            st.metric("Data Fetched", len(ticker_data))
        with col3:
            st.metric("Passed Filters", len(screened_stocks))
        with col4:
            st.metric("Top Ranked", len(top_10))

        # Expandable raw data
        with st.expander("🔍 View All Screened Stocks"):
            all_screened_df = pd.DataFrame(screened_stocks)
            if not all_screened_df.empty:
                all_screened_df = all_screened_df[["Ticker", "Price", "RSI", "Score"]]
                st.dataframe(all_screened_df, use_container_width=True)

    except Exception as e:
        logger.error(f"Market scanner workflow failed: {e}", exc_info=True)
        st.error(f"❌ Scanner Aborted: {str(e)}")


def _render_content_generator() -> None:
    """Execute the Content Generator workflow."""
    st.markdown("""
    **Mission:** Generate professional blog content from stock analysis.

    **The Team:**
    - 🔬 **ResearchBot:** Gathers stock data, news, and technical analysis.
    - 📝 **OutlineBot:** Creates article structure using Claude AI.
    - ✍️ **WriterBot:** Generates full blog post with sections.
    - 📚 **EditorBot:** Reviews for quality and adds citations.
    """)

    if not ANTHROPIC_AVAILABLE:
        st.error("⚠️ Anthropic package not installed. Run: `pip install anthropic`")
        st.info(
            "The Content Generator requires Claude AI for article generation. "
            "Install the anthropic package to use this feature."
        )
        return

    # Check for API key
    api_key = _get_api_key()

    if not api_key:
        st.warning("🔑 **API Key Required**")
        st.markdown("""
        To use the Content Generator, you need an Anthropic API key:

        1. Get your API key at [console.anthropic.com](https://console.anthropic.com/)
        2. Set it as an environment variable: `ANTHROPIC_API_KEY=sk-ant-...`
        3. Or enter it in the Content Engine module first

        The key will be used to generate article outlines and content.
        """)
        return

    # User input
    col1, col2 = st.columns([2, 1])
    with col1:
        ticker = st.text_input(
            "Target Stock", value="NVDA", help="Stock to analyze and write about"
        ).upper()
    with col2:
        article_type = st.selectbox(
            "Article Type",
            ["Analysis & Insights", "Investment Thesis", "Technical Breakdown", "Market Update"],
        )

    col1, col2 = st.columns(2)
    with col1:
        target_words = st.slider("Target Word Count", 300, 1000, 600, step=100)
    with col2:
        tone = st.selectbox("Tone", ["Professional", "Educational", "Analytical", "Storytelling"])

    start_btn = st.button("🚀 Generate Article", type="primary")

    if start_btn and ticker and api_key:
        _run_content_generator_logic(ticker, article_type, target_words, tone, api_key)


def _get_api_key() -> Optional[str]:
    """
    Get Anthropic API key from environment or session state.

    Returns:
        API key string if found, None otherwise
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        return api_key

    if "anthropic_api_key" in st.session_state:
        api_key = st.session_state.anthropic_api_key
        if api_key:
            return api_key

    return None


@retry_with_exponential_backoff()
def _call_claude_api(client: Anthropic, prompt: str) -> str:
    """
    Make API call to Claude with retry logic.

    Args:
        client: Initialized Anthropic client
        prompt: The prompt to send to Claude

    Returns:
        Generated text from Claude

    Raises:
        APIError: For API-related errors
        RateLimitError: When rate limits are exceeded
    """
    logger.debug(f"Calling Claude API with model: {DEFAULT_MODEL}")

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
        timeout=API_TIMEOUT,
    )

    if not message.content or len(message.content) == 0:
        logger.error("API returned empty content")
        raise ValueError("API returned empty response")

    if not hasattr(message.content[0], "text"):
        logger.error(f"API returned unexpected content type: {type(message.content[0])}")
        raise ValueError("API returned malformed response")

    generated_text: str = str(message.content[0].text)
    logger.debug(f"API call successful, received {len(generated_text)} characters")

    return generated_text


def _run_content_generator_logic(
    ticker: str, article_type: str, target_words: int, tone: str, api_key: str
) -> None:
    """
    Orchestrate the content generator agents.

    Args:
        ticker: Stock ticker symbol
        article_type: Type of article to generate
        target_words: Target word count for article
        tone: Writing tone (Professional, Educational, etc.)
        api_key: Anthropic API key
    """
    status_container = st.container()
    results: Dict[str, Any] = {}

    try:
        # Initialize Claude client
        client = Anthropic(api_key=api_key)

        # --- AGENT 1: RESEARCHBOT ---
        with status_container:
            with st.status("🔬 ResearchBot: Gathering intelligence...", expanded=True) as status:
                time.sleep(0.3)

                # Fetch stock data
                df = get_stock_data(ticker, period="6mo", interval="1d")
                if df is None or df.empty:
                    st.error(f"❌ No data found for {ticker}. Please verify ticker symbol.")
                    return

                df = calculate_indicators(df)
                info = get_company_info(ticker)
                news = get_news(ticker)
                sentiment = process_news_sentiment(news)

                # Calculate key metrics
                last_row = df.iloc[-1]
                price_change_pct = (
                    (df.iloc[-1]["Close"] - df.iloc[-30]["Close"]) / df.iloc[-30]["Close"]
                ) * 100

                research_summary = {
                    "ticker": ticker,
                    "company": info.get("longName", ticker),
                    "sector": info.get("sector", "Unknown"),
                    "industry": info.get("industry", "Unknown"),
                    "current_price": last_row["Close"],
                    "price_change_30d": price_change_pct,
                    "rsi": last_row["RSI"],
                    "ma20": last_row["MA20"],
                    "macd_signal": (
                        "BULLISH" if last_row["MACD"] > last_row["Signal_Line"] else "BEARISH"
                    ),
                    "sentiment_score": sentiment["average_score"],
                    "sentiment_verdict": sentiment["verdict"],
                    "news_count": sentiment["article_count"],
                }

                results["research"] = research_summary
                status.update(label="🔬 ResearchBot: Research complete", state="complete")
                st.success(
                    f"Data gathered: {research_summary['company']} - "
                    f"${research_summary['current_price']:.2f} "
                    f"({price_change_pct:+.1f}% 30D)"
                )

        # --- AGENT 2: OUTLINEBOT ---
        with status_container:
            with st.status("📝 OutlineBot: Creating article structure...", expanded=True) as status:
                time.sleep(0.3)

                # Create outline prompt
                company = research_summary["company"]
                outline_prompt = f"""
Create a detailed outline for a {article_type.lower()} blog post about {ticker} ({company}).

Context:
- Current Price: ${research_summary["current_price"]:.2f} ({price_change_pct:+.1f}% in 30 days)
- Sector: {research_summary["sector"]}
- RSI: {research_summary["rsi"]:.1f}
- MACD: {research_summary["macd_signal"]}
- News Sentiment: {research_summary["sentiment_verdict"]} \
({research_summary["news_count"]} articles)

Requirements:
- Target length: {target_words} words
- Tone: {tone}
- Structure: Introduction, 3-4 main sections, conclusion

Return ONLY the outline with section headings and 2-3 bullet points per section.
"""

                try:
                    outline = _call_claude_api(client, outline_prompt)
                    results["outline"] = outline
                    status.update(label="📝 OutlineBot: Outline created", state="complete")
                    st.success("Article structure designed")
                except Exception as e:
                    logger.error(f"Failed to generate outline: {e}")
                    status.update(label="📝 OutlineBot: Failed to create outline", state="error")
                    st.error(f"❌ Outline generation failed: {str(e)}")
                    return

        # --- AGENT 3: WRITERBOT ---
        with status_container:
            with st.status("✍️ WriterBot: Writing article...", expanded=True) as status:
                time.sleep(0.5)

                # Create content prompt
                content_prompt = f"""
Write a {article_type.lower()} blog post about {ticker} ({company}) following this outline:

{outline}

Key Data Points to Include:
- Current Price: ${research_summary["current_price"]:.2f}
- 30-Day Performance: {price_change_pct:+.1f}%
- Sector: {research_summary["sector"]} / {research_summary["industry"]}
- Technical Analysis: RSI={research_summary["rsi"]:.1f}, MACD={research_summary["macd_signal"]}
- Market Sentiment: {research_summary["sentiment_verdict"]}

Requirements:
- Target: {target_words} words
- Tone: {tone}
- Use specific data points and metrics
- Include actionable insights
- Write complete paragraphs with transitions
- DO NOT use markdown headers (I'll add them)

Return ONLY the article text, no titles or metadata.
"""

                try:
                    article = _call_claude_api(client, content_prompt)
                    results["article"] = article
                    word_count = len(article.split())
                    status.update(
                        label=f"✍️ WriterBot: Article complete ({word_count} words)",
                        state="complete",
                    )
                    st.success(f"Draft written: {word_count} words")
                except Exception as e:
                    logger.error(f"Failed to generate article: {e}")
                    status.update(label="✍️ WriterBot: Failed to write article", state="error")
                    st.error(f"❌ Article generation failed: {str(e)}")
                    return

        # --- AGENT 4: EDITORBOT ---
        with status_container:
            with st.status("📚 EditorBot: Reviewing and polishing...", expanded=True) as status:
                time.sleep(0.3)

                # Create editor prompt
                editor_prompt = f"""
Review and improve this blog post about {ticker}. Make it more engaging and professional.

Original Article:
{article}

Tasks:
1. Fix any factual inconsistencies
2. Improve flow and transitions
3. Add a compelling opening hook
4. Strengthen the conclusion with clear takeaways
5. Ensure tone is {tone.lower()}

Return ONLY the edited article text.
"""

                try:
                    edited_article = _call_claude_api(client, editor_prompt)
                    results["final_article"] = edited_article
                    status.update(label="📚 EditorBot: Review complete", state="complete")
                    st.success("Article polished and ready")
                except Exception as e:
                    logger.warning(f"Editor review failed, using original: {e}")
                    results["final_article"] = article
                    status.update(label="📚 EditorBot: Using original version", state="complete")
                    st.warning("Editor review skipped, using original draft")

        # Display Final Article
        st.markdown("---")
        st.subheader(f"📄 Generated Article: {research_summary['company']}")

        # Metadata
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Word Count", len(results["final_article"].split()))
        with col2:
            st.metric("Article Type", article_type)
        with col3:
            st.metric("Tone", tone)
        with col4:
            st.metric("Target Stock", ticker)

        # Article Content
        st.markdown("### Article Preview")
        st.markdown(results["final_article"])

        # Data Sources
        st.markdown("---")
        st.markdown("### 📊 Data Sources")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Market Data:**")
            st.markdown(f"- Price: ${research_summary['current_price']:.2f}")
            st.markdown(f"- 30D Change: {price_change_pct:+.1f}%")
            st.markdown(f"- RSI: {research_summary['rsi']:.1f}")
            st.markdown(f"- MACD: {research_summary['macd_signal']}")
        with col2:
            st.markdown("**Sentiment Analysis:**")
            st.markdown(f"- Verdict: {research_summary['sentiment_verdict']}")
            st.markdown(f"- Articles Analyzed: {research_summary['news_count']}")
            st.markdown(f"- Sentiment Score: {research_summary['sentiment_score']:.2f}")

        # Expandable sections
        with st.expander("📝 View Article Outline"):
            st.markdown(results["outline"])

        with st.expander("🔍 View Research Summary"):
            st.json(research_summary)

        # Copy button
        st.markdown("---")
        st.text_area(
            "Copy Article (Plain Text)",
            value=results["final_article"],
            height=200,
            help="Select all and copy to use elsewhere",
        )

    except Exception as e:
        logger.error(f"Content generator workflow failed: {e}", exc_info=True)
        st.error(f"❌ Generation Aborted: {str(e)}")
        if st.checkbox("Show error details", key="cg_error_details"):
            st.exception(e)
