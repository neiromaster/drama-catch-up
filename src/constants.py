"""Constants used throughout the application."""

# Default user agent for HTTP requests
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
)

# Minimum download speed thresholds (in KB/s)
PIXELDRAIN_MIN_SPEED_NO_API = 1100
PIXELDRAIN_MIN_SPEED_WITH_API = 1000000

# Default configuration values
DEFAULT_CHECK_INTERVAL_MINUTES = 10
DEFAULT_DOWNLOAD_RETRIES = 3
DEFAULT_RETRY_DELAY = 5
DEFAULT_DOWNLOAD_DIRECTORY = "downloads"

# FileCrypt constants
FILECRYPT_BASE_URL = "https://filecrypt.cc"
FILECRYPT_CONTAINER_URL_TEMPLATE = f"{FILECRYPT_BASE_URL}/Container/{{container_id}}.html"
FILECRYPT_LINK_URL_TEMPLATE = f"{FILECRYPT_BASE_URL}/Link/{{link_id}}.html"

# PixelDrain constants
PIXELDRAIN_BASE_URL = "https://pixeldrain.com"
PIXELDRAIN_API_FILE_URL = f"{PIXELDRAIN_BASE_URL}/api/file/{{file_id}}"

# yt-dlp default arguments
YT_DLP_DEFAULT_ARGS = ["--concurrent-fragments", "4"]
