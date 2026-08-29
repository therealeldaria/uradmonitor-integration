"""Constants for the uradmonitor integration."""

DOMAIN = "uradmonitor"
PLATFORMS = ("sensor",)

CONF_ACCESS_MODE = "access_mode"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_CLOUD_USER_ID = "cloud_user_id"
CONF_CLOUD_USER_KEY = "cloud_user_key"
CONF_DEVICE_ID = "device_id"
CONF_DEVICE_TYPE = "device_type"
CONF_DETECTOR = "detector"
CONF_HARDWARE_VERSION = "hardware_version"
CONF_SOFTWARE_VERSION = "software_version"
CONF_POLL_INTERVAL = "poll_interval"
CONF_SOURCES = "sources"
CONF_LOCAL_POLL_INTERVAL = "local_poll_interval"
CONF_CLOUD_POLL_INTERVAL = "cloud_poll_interval"

DEFAULT_LOCAL_POLL_INTERVAL = 300
DEFAULT_CLOUD_POLL_INTERVAL = 900
POLL_INTERVAL_OPTIONS = (300, 600, 900, 1800, 3600)

ACCESS_MODE_LOCAL = "local"
ACCESS_MODE_CLOUD = "cloud"
