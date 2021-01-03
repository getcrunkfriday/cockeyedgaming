import json
from typing import Any

# Common config constants.
TWITCH_HOST = "TWITCH_HOST"
TWITCH_PORT = "TWITCH_PORT"
TWITCH_CHAN = "TWITCH_CHAN"
TWITCH_NICK = "TWITCH_NICK"
TWITCH_PASS = "TWITCH_PASS"
TWITCH_SUB_PASS = "TWITCH_SUB_PASS"
CRUNKYBOT_CLIENT_ID = "CRUNKYBOT_CLIENT_ID"
CRUNKYBOT_CLIENT_SECRET = "CRUNKYBOT_CLIENT_SECRET"

class ConfigLoader:
    def __init__(self, config_file: str, validate_config=True):
        with open(config_file) as f:
            self._config = json.load(f)
        if validate_config:
            self._validate_config()

    def _validate_config(self):
        assert TWITCH_HOST in self._config
        assert TWITCH_PORT in self._config
        assert TWITCH_CHAN in self._config
        assert TWITCH_NICK in self._config
        assert TWITCH_PASS in self._config
        assert TWITCH_SUB_PASS in self._config
        assert CRUNKYBOT_CLIENT_ID in self._config
        assert CRUNKYBOT_CLIENT_SECRET in self._config

    def load(self):
        return self._config

    def __getitem__(self, key: str):
        return self._config[key]

    def __setitem__(self, key: str, val: Any):
        self._config[key] = val
