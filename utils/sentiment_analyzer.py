from textblob import TextBlob
from typing import List, Dict, Any
from utils.logger import get_logger

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
