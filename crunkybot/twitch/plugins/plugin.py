import json
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass
from crunkybot.twitch.icescontroller import PlaylistProcess
from crunkybot.twitch.twitch_utils import TwitchSocket, uptime

@dataclass
class PluginRequest:
    socket: TwitchSocket
    username: str
    message: str
    config: Dict
    process: Optional[PlaylistProcess] = None
    params: Optional[Dict] = None

@dataclass
class Plugin:
    plugin_name: str
    fn: Callable[[PluginRequest], None]

plugins = {
    "insult": [
        Plugin(
            "CockeyedInsults",
            lambda req: insult(req.socket, req.username, req.message, insults)
        )
    ],
    # Raffle commands
    "raffle": [
        Plugin(
            "Raffle",
            lambda req: raffle(req.socket, req.username)
        )
    ],
    "rafflestop": [
        Plugin(
            "Raffle",
            lambda req: raffle_stop(req.socket, req.username)
        )
    ],
    "raffledraw": [
        Plugin(
            "Raffle",
            lambda req: raffle_draw(req.socket, req.username)
        )
    ],
    "rafflestart": [
        Plugin(
            "Raffle",
            lambda req : raffle_start(req.socket, req.username, req.message)
        )
    ],
    # Queue commands
    #"!queue"    : lambda s,u,**kw : utils.add_to_queue(s,u),
    #"!popqueue" : lambda s,u,m,**kw : utils.pop_queue(s,u,m),
    #"!currqueue": lambda s,**kw   : utils.get_queue(s),
    # Music commands
    "sr": [
        Plugin(
            "SongRequest",
            lambda req: song_request(req.socket, req.username, req.message)
        )
    ],
    "currentsong": [
        Plugin(
            "SongPlugin",
            lambda req: utils.current_song_chat(req.socket, req.username)
        )
    ],
    "skip": [
        Plugin(
            "SongPlugin",
            lambda req: utils.skip_song(req.socket, req.username, req.process)
        )
    ],
    "cp" : [
        Plugin(
            "SongPlugin",
            lambda req: utils.change_playlist(
                req.socket, req.username, req.message, req.process
            )
        )
    ],
    "playlists": [
        Plugin(
            "SongPlugin",
            lambda req: utils.list_playlists(req.socket, req.username)
        )
    ],
    "sync": [
        Plugin(
            "SongPlugin",
            lambda req: utils.sync_request(req.username)
        )
    ],
    # Stream commands
    "uptime" : [
        Plugin(
            "StreamUtils",
            lambda req: uptime(req.socket, req.config)
        )
    ],
    # ANY commands. Run on any message, regardless of command.
    "ANY" : [
    ]
}

class PluginLoader:
    def __init__(self, plugin_file: Optional[str] = None):
        if plugin_file is None:
            self._enabled_plugins = None
        else:
            with open(plugin_file) as f:
                self._enabled_plugins = set(json.load(f))
    def load(self):
        loaded_plugins = {}
        if self._enabled_plugins is None:
            loaded_plugins = plugins
        else:
            for keyword, plugin_list in plugins.items():
                loaded_plugins[keyword] = [
                    p for p in plugin_list if p.plugin_name in self._enabled_plugins
                ]
        return loaded_plugins
