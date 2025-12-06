from textblob import TextBlob
from typing import List, Dict, Any, Optional
from utils.logger import get_logger

# Conditional import for Claude API
try:
    from anthropic import Anthropic, APIError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = get_logger(__name__)

def analyze_sentiment(text: str) -> float:
    """
    Analyze the sentiment polarity of a text.
    
    Args:
        text: The text to analyze.
        
    Returns:
        float: Polarity score between -1.0 (Negative) and 1.0 (Positive).
    """
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return 0.0

def process_news_sentiment(news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process a list of news items and calculate aggregate sentiment.
    
    Args:
        news_items: List of news dictionaries (from yfinance).
        
    Returns:
        Dictionary containing:
        - average_score: float (-1 to 1)
        - verdict: str (Bullish/Bearish/Neutral)
        - article_count: int
        - processed_news: List of news with individual scores
    """
    if not news_items:
        return {
            "average_score": 0.0,
            "verdict": "Neutral",
            "article_count": 0,
            "processed_news": []
        }
        
    total_score = 0.0
    processed_news = []
    
    for item in news_items:
        title = item.get('title', '')
        score = analyze_sentiment(title)
        total_score += score
        
        # Determine label for individual article
        if score > 0.1:
            label = "Positive"
        elif score < -0.1:
            label = "Negative"
        else:
            label = "Neutral"
            
        processed_news.append({
            **item,
            "sentiment_score": score,
            "sentiment_label": label
        })
        
    avg_score = total_score / len(news_items)
    
    # Determine overall verdict
    if avg_score > 0.05:
        verdict = "Bullish 🐂"
    elif avg_score < -0.05:
        verdict = "Bearish 🐻"
    else:
        verdict = "Neutral 😐"
        
    return {
        "average_score": avg_score,
        "verdict": verdict,
        "article_count": len(news_items),
        "processed_news": processed_news
    }


def analyze_sentiment_with_claude(news_items: List[Dict[str, Any]], symbol: str, api_key: str) -> Dict[str, Any]:
    """
    Analyze sentiment using Claude AI for richer contextual analysis.

    Args:
        news_items: List of news dictionaries (from yfinance)
        symbol: Stock ticker symbol
        api_key: Anthropic API key

    Returns:
        Dictionary containing:
        - average_score: float (-1 to 1)
        - verdict: str (Bullish/Bearish/Neutral)
        - article_count: int
        - processed_news: List of news with individual scores
        - reasoning: str (AI reasoning for the overall sentiment)
    """
    if not ANTHROPIC_AVAILABLE:
        logger.warning("Anthropic library not available, falling back to TextBlob")
        return process_news_sentiment(news_items)

    if not news_items:
        return {
            "average_score": 0.0,
            "verdict": "Neutral",
            "article_count": 0,
            "processed_news": [],
            "reasoning": "No news available for analysis"
        }

    try:
        client = Anthropic(api_key=api_key)

        # Build news summary for Claude
        news_titles = [item.get('title', '') for item in news_items[:10]]  # Limit to 10 most recent
        news_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(news_titles)])

        prompt = f"""Analyze the sentiment of the following news headlines for {symbol}:

{news_text}

Provide your analysis in the following JSON format:
{{
    "overall_sentiment": "bullish" | "bearish" | "neutral",
    "confidence": 0-100,
    "reasoning": "Brief explanation of why you arrived at this sentiment",
    "article_sentiments": [
        {{"title": "headline 1", "sentiment": "positive|negative|neutral", "score": -1.0 to 1.0}},
        ...
    ]
}}

Be objective and consider:
- Financial implications of the news
- Market impact
- Company performance indicators
- Industry trends mentioned

Keep reasoning concise (2-3 sentences max)."""

        # Call Claude API
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract and parse response
        response_text = message.content[0].text

        # Try to extract JSON from response
        import json
        import re

        # Look for JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            analysis_data = json.loads(json_match.group())
        else:
            # Fallback to TextBlob if parsing fails
            logger.warning("Could not parse Claude response, falling back to TextBlob")
            return process_news_sentiment(news_items)

        # Convert Claude's analysis to our format
        sentiment_map = {
            "bullish": 0.6,
            "bearish": -0.6,
            "neutral": 0.0
        }

        overall_sentiment = analysis_data.get("overall_sentiment", "neutral").lower()
        confidence = analysis_data.get("confidence", 50) / 100
        avg_score = sentiment_map.get(overall_sentiment, 0.0) * (confidence if confidence > 0 else 0.5)

        # Determine verdict
        if avg_score > 0.05:
            verdict = "Bullish 🐂"
        elif avg_score < -0.05:
            verdict = "Bearish 🐻"
        else:
            verdict = "Neutral 😐"

        # Process individual articles
        processed_news = []
        article_sentiments = analysis_data.get("article_sentiments", [])

        for item in news_items:
            title = item.get('title', '')

            # Try to match with Claude's analysis
            matching_sentiment = next(
                (a for a in article_sentiments if a.get('title', '').lower() in title.lower() or title.lower() in a.get('title', '').lower()),
                None
            )

            if matching_sentiment:
                score = matching_sentiment.get('score', 0.0)
                sentiment_label = matching_sentiment.get('sentiment', 'neutral').capitalize()
            else:
                # Fallback to TextBlob for this article
                score = analyze_sentiment(title)
                if score > 0.1:
                    sentiment_label = "Positive"
                elif score < -0.1:
                    sentiment_label = "Negative"
                else:
                    sentiment_label = "Neutral"

            processed_news.append({
                **item,
                "sentiment_score": score,
                "sentiment_label": sentiment_label
            })

        logger.info(f"Successfully analyzed sentiment with Claude for {symbol}")

        return {
            "average_score": avg_score,
            "verdict": verdict,
            "article_count": len(news_items),
            "processed_news": processed_news,
            "reasoning": analysis_data.get("reasoning", "")
        }

    except APIError as e:
        logger.error(f"Anthropic API error: {e}", exc_info=True)
        # Fallback to TextBlob
        return process_news_sentiment(news_items)
    except Exception as e:
        logger.error(f"Error in Claude sentiment analysis: {e}", exc_info=True)
        # Fallback to TextBlob
        return process_news_sentiment(news_items)
