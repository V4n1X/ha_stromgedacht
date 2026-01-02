"""Constants for the StromGedacht integration."""

DOMAIN = "stromgedacht"
CONF_ZIP_CODE = "zip_code"
CONF_SCAN_INTERVAL = "scan_interval"

# API Configuration
URL_STATES = "https://api.stromgedacht.de/v1/statesRelative"
URL_FORECAST = "https://api.stromgedacht.de/v1/forecast"

# Defaults
DEFAULT_SCAN_INTERVAL = 15  # Minuten
MIN_SCAN_INTERVAL = 5       # Minuten