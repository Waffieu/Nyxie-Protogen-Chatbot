import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Memory settings
SHORT_MEMORY_SIZE = int(os.getenv("SHORT_MEMORY_SIZE", "25"))
LONG_MEMORY_SIZE = int(os.getenv("LONG_MEMORY_SIZE", "100"))
MEMORY_DIR = os.getenv("MEMORY_DIR", "user_memories")

# Web search settings
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "100"))

# Proxy settings - DISABLED
# Proxy system has been removed due to connection issues with DuckDuckGo
PROXY_ENABLED = False
PROXY_LIST = []
PROXY_FILE = ""

# Maximum number of retries for DuckDuckGo searches
MAX_SEARCH_RETRIES = int(os.getenv("MAX_SEARCH_RETRIES", "10"))

# Time awareness settings
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Europe/Istanbul")
TIME_AWARENESS_ENABLED = os.getenv("TIME_AWARENESS_ENABLED", "true").lower() == "true"
# Only show time information when relevant to the conversation
SHOW_TIME_ONLY_WHEN_RELEVANT = os.getenv("SHOW_TIME_ONLY_WHEN_RELEVANT", "true").lower() == "true"

# Website link settings
# Only show website links when explicitly requested or relevant
SHOW_LINKS_ONLY_WHEN_RELEVANT = os.getenv("SHOW_LINKS_ONLY_WHEN_RELEVANT", "true").lower() == "true"

# Gemini model settings
GEMINI_MODEL = "gemini-2.5-flash-preview-04-17"
GEMINI_TEMPERATURE = 0.8  # Slightly higher temperature for more varied, natural responses
GEMINI_TOP_P = 0.95
GEMINI_TOP_K = 40
GEMINI_MAX_OUTPUT_TOKENS = 2048  # Reduced max tokens to encourage shorter responses

# Specialized Gemini models
# Model for web search, language detection, and media analysis
GEMINI_FLASH_LITE_MODEL = "gemini-2.0-flash-lite"
GEMINI_FLASH_LITE_TEMPERATURE = 0.4
GEMINI_FLASH_LITE_TOP_P = 0.95
GEMINI_FLASH_LITE_TOP_K = 32
GEMINI_FLASH_LITE_MAX_OUTPUT_TOKENS = 8192

# Safety settings - all set to BLOCK_NONE as requested
SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    },
]
