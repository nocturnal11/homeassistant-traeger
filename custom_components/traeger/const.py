from homeassistant.const import UnitOfTemperature

"""Constants for traeger."""
# Base component constants
NAME = "Traeger"
DOMAIN = "traeger"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.1.0"
ATTRIBUTION = ""
ISSUE_URL = "https://github.com/nocturnal11/homeassistant-traeger/issues"

# Icons
ICON = "mdi:format-quote-close"

# Platforms
CLIMATE = "climate"
SENSOR = "sensor"
SWITCH = "switch"
NUMBER = "number"
BINARY_SENSOR = "binary_sensor"
PLATFORMS = [CLIMATE, SENSOR, SWITCH, NUMBER, BINARY_SENSOR]

# Configuration and options
CONF_ENABLED = "enabled"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_PELLET_OUTAGE_TEMP_DROP = "pellet_outage_temp_drop"
CONF_PELLET_OUTAGE_TIME_THRESHOLD = "pellet_outage_time_threshold"

# Defaults
DEFAULT_NAME = DOMAIN

# Grill Modes
GRILL_MODE_OFFLINE = 99  # Offline
GRILL_MODE_SHUTDOWN = 9  # Cooled down, heading to sleep
GRILL_MODE_COOL_DOWN = 8  # Cool down cycle
GRILL_MODE_CUSTOM_COOK = 7  # Custom cook
GRILL_MODE_MANUAL_COOK = 6  # Manual cook
GRILL_MODE_PREHEATING = 5  # Preheating
GRILL_MODE_IGNITING = 4  # Igniting
GRILL_MODE_IDLE = 3  # Idle (Power switch on, screen on)
GRILL_MODE_SLEEPING = 2  # Sleeping (Power switch on, screen off)

# Grill Temps
# these are the min temps the traeger app would set
GRILL_MIN_TEMP_C = 75
GRILL_MIN_TEMP_F = 165

# Pellet Outage Detection
PELLET_OUTAGE_TEMP_DROP_F = 50  # Temperature drop threshold in Fahrenheit
PELLET_OUTAGE_TEMP_DROP_C = 28  # Temperature drop threshold in Celsius
PELLET_OUTAGE_TIME_THRESHOLD = 300  # Time threshold in seconds (5 minutes)
PELLET_OUTAGE_MIN_TARGET_F = 200  # Only monitor when target temp is at least this high
PELLET_OUTAGE_MIN_TARGET_C = 93  # Only monitor when target temp is at least this high

# Device Type ID to Model Name Mapping
DEVICE_TYPE_MAP = {
    "2104": "Pro 575",
    # Add more device types as they are discovered
    # "xxxx": "Pro 780",
    # "xxxx": "Ironwood 650",
    # etc.
}

# Probe Preset Modes
PROBE_PRESET_MODES = {
    "Chicken": {
        UnitOfTemperature.FAHRENHEIT: 165,
        UnitOfTemperature.CELSIUS: 74,
    },
    "Turkey": {
        UnitOfTemperature.FAHRENHEIT: 165,
        UnitOfTemperature.CELSIUS: 74,
    },
    "Beef (Rare)": {
        UnitOfTemperature.FAHRENHEIT: 125,
        UnitOfTemperature.CELSIUS: 52,
    },
    "Beef (Medium Rare)": {
        UnitOfTemperature.FAHRENHEIT: 135,
        UnitOfTemperature.CELSIUS: 57,
    },
    "Beef (Medium)": {
        UnitOfTemperature.FAHRENHEIT: 140,
        UnitOfTemperature.CELSIUS: 60,
    },
    "Beef (Medium Well)": {
        UnitOfTemperature.FAHRENHEIT: 145,
        UnitOfTemperature.CELSIUS: 63,
    },
    "Beef (Well Done)": {
        UnitOfTemperature.FAHRENHEIT: 155,
        UnitOfTemperature.CELSIUS: 68,
    },
    "Beef (Ground)": {
        UnitOfTemperature.FAHRENHEIT: 160,
        UnitOfTemperature.CELSIUS: 71,
    },
    "Lamb (Rare)": {
        UnitOfTemperature.FAHRENHEIT: 125,
        UnitOfTemperature.CELSIUS: 52,
    },
    "Lamb (Medium Rare)": {
        UnitOfTemperature.FAHRENHEIT: 135,
        UnitOfTemperature.CELSIUS: 57,
    },
    "Lamb (Medium)": {
        UnitOfTemperature.FAHRENHEIT: 140,
        UnitOfTemperature.CELSIUS: 60,
    },
    "Lamb (Medium Well)": {
        UnitOfTemperature.FAHRENHEIT: 145,
        UnitOfTemperature.CELSIUS: 63,
    },
    "Lamb (Well Done)": {
        UnitOfTemperature.FAHRENHEIT: 155,
        UnitOfTemperature.CELSIUS: 68,
    },
    "Lamb (Ground)": {
        UnitOfTemperature.FAHRENHEIT: 160,
        UnitOfTemperature.CELSIUS: 71,
    },
    "Pork (Medium Rare)": {
        UnitOfTemperature.FAHRENHEIT: 135,
        UnitOfTemperature.CELSIUS: 57,
    },
    "Pork (Medium)": {
        UnitOfTemperature.FAHRENHEIT: 140,
        UnitOfTemperature.CELSIUS: 60,
    },
    "Pork (Well Done)": {
        UnitOfTemperature.FAHRENHEIT: 155,
        UnitOfTemperature.CELSIUS: 68,
    },
    "Fish": {
        UnitOfTemperature.FAHRENHEIT: 145,
        UnitOfTemperature.CELSIUS: 63,
    },
}

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
