"""
Agent handler implementations for the EnterpriseHub Agent Swarm.

This module provides execution logic for all 7 specialized agents, integrating
with existing EnterpriseHub utilities (data_loader, sentiment_analyzer, validators).
"""

import os
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from utils.data_loader import (
    calculate_indicators,
    get_company_info,
    get_news,
    get_stock_data,
)
from utils.exceptions import APIError, DataFetchError, DataProcessingError
from utils.logger import get_logger
from utils.sentiment_analyzer import (
    analyze_sentiment_with_claude,
    process_news_sentiment,
)
from utils.validators import ConfidenceScorer, ContradictionDetector, SchemaValidator

# Conditional import for Claude API
try:
    from anthropic import (
        APIConnectionError,
        APIError as AnthropicAPIError,
        APITimeoutError,
        RateLimitError,
    )

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    # Define dummy exceptions for type consistency
    RateLimitError = Exception
    APIConnectionError = Exception
    APITimeoutError = Exception
    AnthropicAPIError = Exception

# Initialize logger
logger = get_logger(__name__)

# Constants for retry logic
MAX_RETRY_ATTEMPTS = 3
INITIAL_RETRY_DELAY = 1.0
RETRY_BACKOFF_FACTOR = 2.0


# ============================================================================
# Retry Decorator (from multi_agent.py)
# ============================================================================


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
                except (AnthropicAPIError, APIError) as e:
                    logger.error(f"Non-retryable API error: {str(e)}")
                    raise
                except Exception as e:
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
                    raise

            if last_exception:
                raise last_exception

        return wrapper

    return decorator


# ============================================================================
# Helper Functions
# ============================================================================


def calculate_data_quality(
    df: Optional[pd.DataFrame], info: Dict[str, Any], news: List[Any]
) -> float:
    """
    Calculate overall data quality score.

    Args:
        df: Stock OHLCV data
        info: Company information
        news: News articles

    Returns:
        Quality score [0.0, 1.0]
    """
    scorer = ConfidenceScorer()
    scores = []

    # 1. DataFrame quality
    if df is not None and not df.empty:
        df_quality = scorer.score_data_quality(df)
        scores.append(df_quality)
    else:
        scores.append(0.0)

    # 2. Company info completeness
    if info:
        # Check key fundamental fields
        key_fields = ["marketCap", "sector", "industry", "currentPrice"]
        present = sum(1 for field in key_fields if field in info and info[field])
        info_score = present / len(key_fields)
        scores.append(info_score)
    else:
        scores.append(0.0)

    # 3. News availability
    if news and len(news) >= 3:
        news_score = min(1.0, len(news) / 10.0)  # 10 articles = perfect
        scores.append(news_score)
    elif news:
        scores.append(0.5)  # Some news but <3 articles
    else:
        scores.append(0.0)

    # Aggregate using harmonic mean
    quality = scorer.aggregate_confidence(scores)
    logger.info(f"Data quality score: {quality:.3f}")

    return quality


# ============================================================================
# Agent 1: DataBot Handler
# ============================================================================


@retry_with_exponential_backoff()
def data_bot_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    DataBot execution logic: Fetch market data, company info, and news.

    Args:
        inputs: {"ticker": str, "period": str}
        context: Shared workflow context

    Returns:
        {
            "df": pd.DataFrame,
            "info": dict,
            "news": list,
            "quality_score": float
        }
    """
    ticker = inputs["ticker"]
    period = inputs.get("period", "1y")

    logger.info(f"DataBot: Fetching data for {ticker} (period={period})")

    # Fetch stock data
    df = get_stock_data(ticker, period=period)

    # Fetch company info
    try:
        info = get_company_info(ticker)
    except DataFetchError:
        logger.warning(f"DataBot: Could not fetch company info for {ticker}")
        info = {}

    # Fetch news
    news = get_news(ticker)

    # Calculate data quality
    quality_score = calculate_data_quality(df, info, news)

    logger.info(
        f"DataBot: Success - {len(df) if df is not None else 0} rows, "
        f"{len(news)} news, quality={quality_score:.2f}"
    )

    return {"df": df, "info": info, "news": news, "quality_score": quality_score}


# ============================================================================
# Agent 2: TechBot Handler
# ============================================================================


def tech_bot_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    TechBot execution logic: Calculate technical indicators and generate signals.

    Args:
        inputs: {"df": pd.DataFrame}
        context: Shared workflow context

    Returns:
        {
            "df": pd.DataFrame,  # With indicators
            "signal": str,       # BULLISH, BEARISH, NEUTRAL
            "confidence": float,
            "macd_signal": str,
            "rsi_value": float
        }
    """
    df = inputs["df"]

    if df is None or df.empty:
        raise DataProcessingError("TechBot: Empty DataFrame provided")

    logger.info(f"TechBot: Calculating indicators for {len(df)} rows")

    # Calculate indicators
    df = calculate_indicators(df)

    # Extract latest values
    latest = df.iloc[-1]
    rsi = latest.get("RSI", 50.0)
    macd = latest.get("MACD", 0.0)
    signal_line = latest.get("Signal", 0.0)
    close = latest.get("Close", 0.0)
    ma20 = latest.get("MA20", 0.0)

    # Generate MACD signal
    if macd > signal_line:
        macd_signal = "BULLISH"
    elif macd < signal_line:
        macd_signal = "BEARISH"
    else:
        macd_signal = "NEUTRAL"

    # Generate overall signal with confidence
    signals = []

    # RSI analysis
    if rsi > 70:
        signals.append(("BEARISH", 0.7))  # Overbought
    elif rsi > 60:
        signals.append(("BULLISH", 0.5))
    elif rsi < 30:
        signals.append(("BULLISH", 0.7))  # Oversold
    elif rsi < 40:
        signals.append(("BEARISH", 0.5))
    else:
        signals.append(("NEUTRAL", 0.5))

    # MACD analysis
    if macd_signal == "BULLISH":
        signals.append(("BULLISH", 0.8))
    elif macd_signal == "BEARISH":
        signals.append(("BEARISH", 0.8))
    else:
        signals.append(("NEUTRAL", 0.5))

    # MA20 analysis
    if close > ma20 * 1.02:
        signals.append(("BULLISH", 0.6))
    elif close < ma20 * 0.98:
        signals.append(("BEARISH", 0.6))
    else:
        signals.append(("NEUTRAL", 0.5))

    # Aggregate signals
    bullish_conf = sum(conf for sig, conf in signals if sig == "BULLISH")
    bearish_conf = sum(conf for sig, conf in signals if sig == "BEARISH")
    neutral_conf = sum(conf for sig, conf in signals if sig == "NEUTRAL")

    total_conf = bullish_conf + bearish_conf + neutral_conf
    if bullish_conf > bearish_conf and bullish_conf > neutral_conf:
        signal = "BULLISH"
        confidence = bullish_conf / total_conf
    elif bearish_conf > bullish_conf and bearish_conf > neutral_conf:
        signal = "BEARISH"
        confidence = bearish_conf / total_conf
    else:
        signal = "NEUTRAL"
        confidence = neutral_conf / total_conf

    logger.info(
        f"TechBot: Signal={signal}, Confidence={confidence:.2f}, "
        f"RSI={rsi:.1f}, MACD={macd_signal}"
    )

    return {
        "df": df,
        "signal": signal,
        "confidence": confidence,
        "macd_signal": macd_signal,
        "rsi_value": rsi,
    }


# ============================================================================
# Agent 3: SentimentBot Handler
# ============================================================================


@retry_with_exponential_backoff()
def sentiment_bot_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    SentimentBot execution logic: Analyze news sentiment.

    Args:
        inputs: {"news": list, "ticker": str}
        context: Shared workflow context

    Returns:
        {
            "verdict": str,       # Positive, Negative, Neutral
            "confidence": float,
            "themes": list,
            "article_count": int
        }
    """
    news = inputs["news"]
    ticker = inputs["ticker"]

    if not news or len(news) < 3:
        logger.warning(f"SentimentBot: Insufficient news ({len(news)} articles)")
        return {
            "verdict": "Neutral",
            "confidence": 0.3,
            "themes": [],
            "article_count": len(news) if news else 0,
        }

    logger.info(f"SentimentBot: Analyzing {len(news)} articles for {ticker}")

    # Try Claude API if available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if ANTHROPIC_AVAILABLE and api_key:
        try:
            result = analyze_sentiment_with_claude(news, ticker, api_key)
            # Map Claude verdict to expected format
            verdict_map = {
                "Bullish 🐂": "Positive",
                "Bearish 🐻": "Negative",
                "Neutral 😐": "Neutral",
            }
            verdict = verdict_map.get(result.get("verdict", "Neutral"), "Neutral")

            # Calculate confidence from score
            avg_score = result.get("average_score", 0.0)
            confidence = min(1.0, abs(avg_score) + 0.5)

            return {
                "verdict": verdict,
                "confidence": confidence,
                "themes": result.get("themes", []),
                "article_count": result.get("article_count", len(news)),
            }
        except Exception as e:
            logger.warning(f"SentimentBot: Claude API failed, falling back to TextBlob: {e}")

    # Fallback: Use TextBlob
    result = process_news_sentiment(news)

    # Map verdict
    verdict_map = {
        "Bullish 🐂": "Positive",
        "Bearish 🐻": "Negative",
        "Neutral 😐": "Neutral",
    }
    verdict = verdict_map.get(result.get("verdict", "Neutral"), "Neutral")

    # Calculate confidence from score
    avg_score = result.get("average_score", 0.0)
    confidence = min(1.0, abs(avg_score) + 0.5)

    logger.info(
        f"SentimentBot: Verdict={verdict}, Confidence={confidence:.2f}, "
        f"Articles={result['article_count']}"
    )

    return {
        "verdict": verdict,
        "confidence": confidence,
        "themes": [],  # TextBlob doesn't extract themes
        "article_count": result["article_count"],
    }


# ============================================================================
# Agent 4: ValidatorBot Handler
# ============================================================================


def validator_bot_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    ValidatorBot execution logic: Validate agent results and detect contradictions.

    Args:
        inputs: {"results": dict, "validation_rules": list}
        context: Shared workflow context

    Returns:
        {
            "passed": bool,
            "confidence": float,
            "errors": list,
            "warnings": list,
            "conflicts": list
        }
    """
    results = inputs["results"]
    validation_rules = inputs.get("validation_rules", [])

    logger.info(f"ValidatorBot: Validating {len(results)} agent results")

    # Initialize validators
    SchemaValidator()
    confidence_scorer = ConfidenceScorer()
    contradiction_detector = ContradictionDetector()

    errors = []
    warnings = []
    confidence_scores = []

    # 1. Schema validation (if rules provided)
    for rule in validation_rules:
        rule_id = rule.get("rule_id", "unknown")
        validator_fn = rule.get("validator")
        rule.get("threshold", 0.8)

        if validator_fn and callable(validator_fn):
            try:
                valid = validator_fn(results)
                if not valid:
                    severity = rule.get("severity", "WARNING")
                    if severity == "ERROR":
                        errors.append(f"Rule '{rule_id}' failed")
                    else:
                        warnings.append(f"Rule '{rule_id}' failed")
            except Exception as e:
                warnings.append(f"Rule '{rule_id}' error: {str(e)}")

    # 2. Confidence scoring
    for agent_id, result in results.items():
        if isinstance(result, dict) and "confidence" in result:
            confidence_scores.append(result["confidence"])

    if confidence_scores:
        aggregate_conf = confidence_scorer.aggregate_confidence(confidence_scores)
    else:
        aggregate_conf = 0.5

    # 3. Contradiction detection
    conflicts = contradiction_detector.detect_logical_conflicts(results)

    # Add conflicts to errors/warnings based on severity
    for conflict in conflicts:
        msg = f"{conflict.conflict_type}: {conflict.description}"
        if conflict.severity == "ERROR":
            errors.append(msg)
        elif conflict.severity == "WARNING":
            warnings.append(msg)

    # 4. Final pass/fail determination
    passed = len(errors) == 0

    logger.info(
        f"ValidatorBot: Passed={passed}, Confidence={aggregate_conf:.2f}, "
        f"Errors={len(errors)}, Warnings={len(warnings)}, Conflicts={len(conflicts)}"
    )

    return {
        "passed": passed,
        "confidence": aggregate_conf,
        "errors": errors,
        "warnings": warnings,
        "conflicts": [
            {
                "type": c.conflict_type,
                "agents": c.agents,
                "description": c.description,
                "severity": c.severity,
            }
            for c in conflicts
        ],
    }


# ============================================================================
# Agent 5: ForecastBot Handler
# ============================================================================


def forecast_bot_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    ForecastBot execution logic: Generate ML forecast with confidence intervals.

    Args:
        inputs: {"df": pd.DataFrame}
        context: Shared workflow context

    Returns:
        {
            "forecast": pd.DataFrame,
            "confidence_lower": pd.Series,
            "confidence_upper": pd.Series,
            "metrics": dict,
            "trend": str
        }
    """
    df = inputs["df"]

    if df is None or df.empty or len(df) < 90:
        raise DataProcessingError(
            f"ForecastBot: Insufficient data ({len(df) if df else 0} rows, need 90)"
        )

    logger.info(f"ForecastBot: Generating forecast for {len(df)} rows")

    # Prepare features
    df_copy = df.copy()

    # Ensure we have technical indicators
    if "MA20" not in df_copy.columns:
        from utils.data_loader import calculate_indicators

        df_copy = calculate_indicators(df_copy)

    # Create lag features
    df_copy["lag_1"] = df_copy["Close"].shift(1)
    df_copy["lag_5"] = df_copy["Close"].shift(5)
    df_copy["rolling_std"] = df_copy["Close"].rolling(window=20).std()

    # Drop NaN rows
    df_copy = df_copy.dropna()

    if len(df_copy) < 60:
        raise DataProcessingError(
            f"ForecastBot: After feature engineering, only {len(df_copy)} rows remain"
        )

    # Feature selection
    feature_cols = ["MA20", "RSI", "MACD", "lag_1", "lag_5", "rolling_std", "Volume"]
    available_features = [col for col in feature_cols if col in df_copy.columns]

    X = df_copy[available_features].values
    y = df_copy["Close"].values

    # Train/test split (80/20)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    # Train RandomForest
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)

    # Backtest on test set
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    # Directional accuracy
    direction_actual = np.diff(y_test) > 0
    direction_pred = np.diff(y_pred) > 0
    directional_accuracy = np.mean(direction_actual == direction_pred)

    # Generate 30-day forecast
    forecast_horizon = 30
    forecast_values = []
    last_features = X[-1].copy()

    for _ in range(forecast_horizon):
        pred = model.predict([last_features])[0]
        forecast_values.append(pred)

        # Update features for next prediction (simplified)
        last_features = np.roll(last_features, 1)
        last_features[0] = pred

    # Calculate confidence intervals (±1σ, ±2σ)
    forecast_std = np.std(y_test - y_pred)
    forecast_series = pd.Series(forecast_values)
    confidence_lower = forecast_series - forecast_std
    confidence_upper = forecast_series + forecast_std

    # Determine trend
    avg_change = (forecast_values[-1] - y[-1]) / y[-1]
    if avg_change > 0.02:
        trend = "BULLISH"
    elif avg_change < -0.02:
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"

    logger.info(
        f"ForecastBot: Trend={trend}, R²={r2:.3f}, MAE={mae:.2f}, "
        f"Dir.Acc={directional_accuracy:.2%}"
    )

    # Create forecast DataFrame
    forecast_dates = pd.date_range(
        start=df.index[-1] + pd.Timedelta(days=1), periods=forecast_horizon, freq="D"
    )
    forecast_df = pd.DataFrame({"forecast": forecast_values}, index=forecast_dates)

    return {
        "forecast": forecast_df,
        "confidence_lower": confidence_lower,
        "confidence_upper": confidence_upper,
        "metrics": {
            "MAE": mae,
            "RMSE": rmse,
            "R2": r2,
            "directional_accuracy": directional_accuracy,
        },
        "trend": trend,
    }


# ============================================================================
# Agent 6: SynthesisBot Handler
# ============================================================================


def synthesis_bot_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    SynthesisBot execution logic: Synthesize all agent results into final recommendation.

    Args:
        inputs: {"results": dict}
        context: Shared workflow context

    Returns:
        {
            "recommendation": str,  # BUY, HOLD, SELL, INSUFFICIENT_DATA
            "confidence": float,
            "reasoning": str,
            "risk_factors": list,
            "supporting_evidence": dict
        }
    """
    results = inputs["results"]

    # Check minimum agents
    if len(results) < 3:
        logger.warning(f"SynthesisBot: Insufficient results ({len(results)} < 3)")
        return {
            "recommendation": "INSUFFICIENT_DATA",
            "confidence": 0.0,
            "reasoning": "Not enough agent results to synthesize",
            "risk_factors": ["Incomplete analysis"],
            "supporting_evidence": {},
        }

    logger.info(f"SynthesisBot: Synthesizing {len(results)} agent results")

    # Extract signals and confidence
    signals = []
    confidence_scores = []

    # Technical signal
    if "technical" in results or "tech_bot" in results:
        tech = results.get("technical") or results.get("tech_bot", {})
        tech_signal = tech.get("signal", "NEUTRAL")
        tech_conf = tech.get("confidence", 0.5)
        signals.append((tech_signal, tech_conf, "Technical"))
        confidence_scores.append(tech_conf)

    # Sentiment signal
    if "sentiment" in results or "sentiment_bot" in results:
        sent = results.get("sentiment") or results.get("sentiment_bot", {})
        sent_verdict = sent.get("verdict", "Neutral")
        sent_conf = sent.get("confidence", 0.5)

        # Map sentiment to signal
        if "Positive" in sent_verdict:
            sent_signal = "BULLISH"
        elif "Negative" in sent_verdict:
            sent_signal = "BEARISH"
        else:
            sent_signal = "NEUTRAL"

        signals.append((sent_signal, sent_conf, "Sentiment"))
        confidence_scores.append(sent_conf)

    # Forecast signal
    if "forecast" in results or "forecast_bot" in results:
        forecast = results.get("forecast") or results.get("forecast_bot", {})
        forecast_trend = forecast.get("trend", "NEUTRAL")
        forecast_metrics = forecast.get("metrics", {})
        forecast_conf = forecast_metrics.get("R2", 0.5)
        signals.append((forecast_trend, forecast_conf, "Forecast"))
        confidence_scores.append(forecast_conf)

    # Aggregate signals
    bullish_weight = sum(conf for sig, conf, _ in signals if sig == "BULLISH")
    bearish_weight = sum(conf for sig, conf, _ in signals if sig == "BEARISH")
    neutral_weight = sum(conf for sig, conf, _ in signals if sig == "NEUTRAL")

    total_weight = bullish_weight + bearish_weight + neutral_weight

    # Determine recommendation
    if total_weight == 0:
        recommendation = "INSUFFICIENT_DATA"
        final_confidence = 0.0
    elif bullish_weight > bearish_weight * 1.5 and bullish_weight > neutral_weight:
        recommendation = "BUY"
        final_confidence = bullish_weight / total_weight
    elif bearish_weight > bullish_weight * 1.5 and bearish_weight > neutral_weight:
        recommendation = "SELL"
        final_confidence = bearish_weight / total_weight
    else:
        recommendation = "HOLD"
        final_confidence = max(neutral_weight, bullish_weight, bearish_weight) / total_weight

    # Apply confidence threshold
    if final_confidence < 0.7:
        recommendation = "HOLD"

    # Build reasoning
    reasoning_parts = []
    for signal, conf, source in signals:
        reasoning_parts.append(f"- {source}: {signal} (confidence={conf:.2f})")

    reasoning = (
        f"Recommendation: {recommendation} (confidence={final_confidence:.2f})\n\n"
        + "Signal Summary:\n"
        + "\n".join(reasoning_parts)
    )

    # Identify risk factors
    risk_factors = []
    if final_confidence < 0.7:
        risk_factors.append("Low overall confidence")
    if len(set(sig for sig, _, _ in signals)) > 1:
        risk_factors.append("Conflicting signals across agents")
    if "validator_bot" in results:
        val = results["validator_bot"]
        if not val.get("passed", True):
            risk_factors.append("Validation checks failed")

    logger.info(
        f"SynthesisBot: Recommendation={recommendation}, Confidence={final_confidence:.2f}, "
        f"Risks={len(risk_factors)}"
    )

    return {
        "recommendation": recommendation,
        "confidence": final_confidence,
        "reasoning": reasoning,
        "risk_factors": risk_factors,
        "supporting_evidence": {
            "signals": [{"signal": s, "confidence": c, "source": src} for s, c, src in signals],
            "aggregate_confidence": final_confidence,
        },
    }


# ============================================================================
# Agent 7: AnalystBot Handler
# ============================================================================


def analyst_bot_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    AnalystBot execution logic: Cross-module intelligence analysis.

    Args:
        inputs: {"module_results": dict}
        context: Shared workflow context

    Returns:
        {
            "integrated_insights": list,
            "divergences": list,
            "confidence": float,
            "portfolio_guidance": str
        }
    """
    module_results = inputs["module_results"]

    logger.info(f"AnalystBot: Analyzing {len(module_results)} module results")

    integrated_insights = []
    divergences = []

    # Cross-correlate technical and forecast
    if "technical" in module_results and "forecast" in module_results:
        tech_signal = module_results["technical"].get("signal", "NEUTRAL")
        forecast_trend = module_results["forecast"].get("trend", "NEUTRAL")

        if tech_signal == forecast_trend:
            integrated_insights.append(
                f"Technical analysis and ML forecast align ({tech_signal}) → Strong signal"
            )
        else:
            divergences.append(
                {
                    "modules": ["Technical", "Forecast"],
                    "description": f"Technical {tech_signal} vs Forecast {forecast_trend}",
                    "severity": "WARNING",
                }
            )
            integrated_insights.append(
                "Divergence detected between technical and forecast → Exercise caution"
            )

    # Check data quality vs confidence
    if "data_bot" in module_results and "validator_bot" in module_results:
        data_quality = module_results["data_bot"].get("quality_score", 0.5)
        validator_conf = module_results["validator_bot"].get("confidence", 0.5)

        if data_quality < 0.6 and validator_conf > 0.8:
            divergences.append(
                {
                    "modules": ["DataBot", "ValidatorBot"],
                    "description": (
                        f"Low data quality ({data_quality:.2f}) but high "
                        f"validation confidence ({validator_conf:.2f})"
                    ),
                    "severity": "INFO",
                }
            )

    # Portfolio guidance
    if len(divergences) == 0:
        portfolio_guidance = "Signals are aligned. Consider increasing position sizing."
        confidence = 0.85
    elif len(divergences) == 1:
        portfolio_guidance = "Minor divergence detected. Maintain current allocation."
        confidence = 0.65
    else:
        portfolio_guidance = "Multiple divergences. Reduce position or wait for clarity."
        confidence = 0.45

    if not integrated_insights:
        integrated_insights.append("Insufficient cross-module data for deep analysis")

    logger.info(
        f"AnalystBot: Insights={len(integrated_insights)}, "
        f"Divergences={len(divergences)}, Confidence={confidence:.2f}"
    )

    return {
        "integrated_insights": integrated_insights,
        "divergences": divergences,
        "confidence": confidence,
        "portfolio_guidance": portfolio_guidance,
    }


# ============================================================================
# Handler Registry
# ============================================================================

# Export all handlers for registration
AGENT_HANDLERS = {
    "data_bot": data_bot_handler,
    "tech_bot": tech_bot_handler,
    "sentiment_bot": sentiment_bot_handler,
    "validator_bot": validator_bot_handler,
    "forecast_bot": forecast_bot_handler,
    "synthesis_bot": synthesis_bot_handler,
    "analyst_bot": analyst_bot_handler,
}


def get_handler(agent_id: str) -> Callable:
    """
    Get handler function by agent ID.

    Args:
        agent_id: Agent identifier (e.g., 'data_bot')

    Returns:
        Handler function

    Raises:
        KeyError: If agent_id not found
    """
    if agent_id not in AGENT_HANDLERS:
        available = ", ".join(AGENT_HANDLERS.keys())
        raise KeyError(f"Handler for '{agent_id}' not found. Available: {available}")
    return AGENT_HANDLERS[agent_id]


logger.info(f"Agent handlers initialized: {len(AGENT_HANDLERS)} handlers registered")
