"""
Custom exceptions for Enterprise Hub.

Provides clear error hierarchies for better error handling
and debugging throughout the application.
"""


class EnterpriseHubError(Exception):
    """Base exception class for all Enterprise Hub errors."""
    pass


class DataFetchError(EnterpriseHubError):
    """Raised when data fetching from external sources fails."""
    pass


class InvalidTickerError(DataFetchError):
    """Raised when an invalid ticker symbol is provided."""
    
    def __init__(self, ticker: str, message: str = ""):
        self.ticker = ticker
        default_message = f"Invalid ticker symbol: '{ticker}'"
        super().__init__(message or default_message)


class DataProcessingError(EnterpriseHubError):
    """Raised when data processing or calculation fails."""
    pass


class ConfigurationError(EnterpriseHubError):
    """Raised when configuration is invalid or missing."""
    pass


class APIError(EnterpriseHubError):
    """Raised when external API calls fail."""
    
    def __init__(self, service: str, message: str = ""):
        self.service = service
        default_message = f"API error from {service}"
        super().__init__(message or default_message)
