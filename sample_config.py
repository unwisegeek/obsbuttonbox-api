# This is a sample configuration file. Please fill in the below values with the ones for your system.

# Once finished, rename to config.py

# URL where the API will be running.
API_URL = 'localhost' # Example: 127.0.0.1 or localhost
API_PORT = 5000

# MQTT Configuration
MQTT_HOST = 'localhost' # Example: 127.0.0.1 or localhost
MQTT_PORT = 1883 # Do not use '' - Example: 1883
MQTT_AUTH = None
# MQTT_AUTH = {'username':'','password':''} # Authentication for MQTT. Uncomment if required.

# OBS Configuration - Leave all configuration values alone if running on localhost:4444 with no password.
OBS_HOST = 'localhost'
OBS_PORT = 4444
OBS_PASSWORD = None # Leave blank if no password