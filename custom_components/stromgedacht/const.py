"""Constants for the StromGedacht integration."""

DOMAIN = "stromgedacht"
CONF_ZIP_CODE = "zip_code"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_SHORT_STATUS = "short_status"

# API Configuration
URL_STATES = "https://api.stromgedacht.de/v1/statesRelative"
URL_FORECAST = "https://api.stromgedacht.de/v1/forecast"
REQUEST_TIMEOUT = 20  # Seconds
STATES_HOURS_IN_FUTURE = 48  # Enough for planning; the API allows up to 52

# Defaults
DEFAULT_SCAN_INTERVAL = 15  # Minutes
MIN_SCAN_INTERVAL = 5       # Minutes
DEFAULT_SHORT_STATUS = False

# Grid states as returned by the API, mapped to the sensor state
STATE_SLUG_MAPPING = {
    -1: "super_green",
    1: "green",
    3: "orange",
    4: "red",
}
