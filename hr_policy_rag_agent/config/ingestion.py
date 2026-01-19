"""
Ingestion configuration module for HR policy scraping.

Contains:
- Base URLs and endpoints
- Default HTTP headers
- Regex patterns for content extraction
- Default ingestion settings
"""

import re

# ---------------------------------------------------------------------------- #
#                                   Constants                                  #
# ---------------------------------------------------------------------------- #
BASE_URL = "https://www.elinfonet.com/hr-policy-samples/"

# Default HTTP headers for requests
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ---------------------------------------------------------------------------- #
#                                Regex Patterns                                #
# ---------------------------------------------------------------------------- #
# Pattern to detect disclaimers/warnings on policy pages
DISCLAIMER_PATTERN = re.compile(
    r"(Warning!|WARNING:)\s*Do\s+NOT\s+simply\s+adopt\s+a\s+policy.*?You[’']ve\s+been\s+warned\.",
    re.IGNORECASE | re.DOTALL,
)

# Pattern to match URLs that point to actual policies
POLICY_PATTERN = r".*(-policy/|flexible-work-schedule/)$"

# ---------------------------------------------------------------------------- #
#                               Default Settings                               #
# ---------------------------------------------------------------------------- #
DEFAULT_INGESTION_SETTINGS = {
    "base_url": BASE_URL,
    "headers": HEADERS,
    "disclaimer_pattern": DISCLAIMER_PATTERN,
    "policy_pattern": POLICY_PATTERN,
}
