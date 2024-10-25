# Make a copy of this file and name it "config.py"
REPEAT_EMOJI = "♻️"
WAITING_EMOJI = "🕒"

# Point this to the caharkness/comfyui-selector instance
SELECTOR_ADDRESS = "http://127.0.0.1:5000"

# Optionally log each request to a MySQL/MariaDB database
MYSQL_CONFIG = {
    "user": "root",
    "password": "password",
    "host": "127.0.0.1",
    "database": "comfyui_discord_ui",
    "raise_on_warnings": False
}
