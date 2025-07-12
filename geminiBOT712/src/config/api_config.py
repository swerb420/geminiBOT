# config/api_config.py
# Manages API keys and endpoints for various data sources.

# In a real system, these values would be securely loaded from an
# encrypted file or secret management service. They are provided here
# as placeholders.

API_KEYS = {
    "unusual_whales": "YOUR_UNUSUAL_WHALES_API_KEY",
    "bigshort": "YOUR_BIGSHORT_API_KEY",
    "stalkchain": "YOUR_STALKCHAIN_API_KEY",
    "twitter": {
        "api_key": "YOUR_TWITTER_API_KEY",
        "api_secret_key": "YOUR_TWITTER_API_SECRET_KEY",
        "access_token": "YOUR_TWITTER_ACCESS_TOKEN",
        "access_token_secret": "YOUR_TWITTER_ACCESS_TOKEN_SECRET",
    },
    "sec": {
        "user_agent": "Your Name Your-Email@example.com",
    },
    "reddit": {
        "client_id": "YOUR_REDDIT_CLIENT_ID",
        "client_secret": "YOUR_REDDIT_CLIENT_SECRET",
        "user_agent": "YOUR_REDDIT_USER_AGENT",
    },
}

API_ENDPOINTS = {
    "unusual_whales": "https://api.unusualwhales.com/v2/",
    "bigshort": "https://api.bigshort.com/v1/",
    "stalkchain": "https://api.stalkchain.io/v1/",
    "sec_edgar": "https://data.sec.gov/submissions/",
    "federal_reserve": "https://api.stlouisfed.org/fred/",
    "google_trends": "https://trends.google.com/trends/api/",
    "yahoo_finance": "https://query1.finance.yahoo.com/",
}
