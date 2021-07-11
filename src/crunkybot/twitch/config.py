import json
from typing import Any, Dict

# Common config constants.
TWITCH_HOST = "TWITCH_HOST"
TWITCH_PORT = "TWITCH_PORT"
TWITCH_CHAN = "TWITCH_CHAN"
TWITCH_CHAN_ID = "TWITCH_CHAN_ID"
TWITCH_NICK = "TWITCH_NICK"
TWITCH_PASS = "TWITCH_PASS"
TWITCH_SUB_PASS = "TWITCH_SUB_PASS"
CRUNKYBOT_CLIENT_ID = "CRUNKYBOT_CLIENT_ID"
CRUNKYBOT_CLIENT_SECRET = "CRUNKYBOT_CLIENT_SECRET"
MUSIC_DOWNLOAD_DIR = "MUSIC_DOWNLOAD_DIR"
COMMAND_DB_LOCATION = "COMMAND_DB_LOCATION"
MUSIC_DB_LOCATION = "MUSIC_DB_LOCATION"
MUSIC_PLAYLIST = "MUSIC_PLAYLIST"

# YouTube API constants
YOUTUBE_API_SERVICE_NAME = "YOUTUBE_API_SERVICE_NAME"
YOUTUBE_API_VERSION = "YOUTUBE_API_VERSION"
YOUTUBE_DEVELOPER_KEY = "YOUTUBE_DEVELOPER_KEY"
YOUTUBE_PLAYLIST_CHANNEL = "YOUTUBE_PLAYLIST_CHANNEL"


class ConfigLoader:

    CONFIG: Dict = None

    def __init__(self, config_file: str, validate_config=True):
        with open(config_file) as f:
            ConfigLoader.CONFIG = json.load(f)
        if validate_config:
            self._validate_config()

    @staticmethod
    def _validate_config():
        assert TWITCH_HOST in ConfigLoader.CONFIG
        assert TWITCH_PORT in ConfigLoader.CONFIG
        assert TWITCH_CHAN in ConfigLoader.CONFIG
        assert TWITCH_NICK in ConfigLoader.CONFIG
        assert TWITCH_PASS in ConfigLoader.CONFIG
        assert TWITCH_SUB_PASS in ConfigLoader.CONFIG
        assert CRUNKYBOT_CLIENT_ID in ConfigLoader.CONFIG
        assert CRUNKYBOT_CLIENT_SECRET in ConfigLoader.CONFIG

    @staticmethod
    def load() -> Dict:
        return ConfigLoader.CONFIG

    def __getitem__(self, key: str):
        return ConfigLoader.CONFIG.get(key)

    def __setitem__(self, key: str, val: Any):
        ConfigLoader.CONFIG = val
