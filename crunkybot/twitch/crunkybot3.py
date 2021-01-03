import logging
import sys
import os
import argparse
from config3 import ConfigLoader
from typing import List
from crunkybot.twitch.plugins.plugin import PluginLoader, PluginRequest
import crunkybot.twitch.twitch_utils as twitch_utils

logger = logging.getLogger(__name__)

def parse_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--plugin_file",
        required=False,
        default=None,
        help="File that describes the desired bot plugins to run."
    )
    parser.add_argument(
        "--config_file",
        required=True,
        help="Config file for bot settings (channel info, etc.)"
    )
    return parser.parse_args(args)

def main(args: argparse.Namespace):
    config: Dict = ConfigLoader(args.config_file).load()
    plugins: Dict[str, Plugin] = PluginLoader(args.plugin_file).load()
    twitch_sock: TwitchSocket = twitch_utils.connect(config)
    print(f"Loaded plugins: {plugins}")
    while True:
        try:
            response = twitch_sock.receive()
            if response != twitch_utils.PING_MSG and len(response.strip()) > 0:
                print(f"{response}")
                username = twitch_utils.get_username(response)
                command, message = twitch_utils.get_message(response)
                print(f"{username}, {command}, {message}")
                request = PluginRequest(
                    socket=twitch_sock,
                    username=username,
                    message=message,
                    config=config,
                    process=None, # Build later
                )
                # Pass command, message to "Plugins"
                if command is not None:
                    for keyword, plugin_list in plugins.items():
                        if command == keyword or keyword == "ANY":
                            for plugin in plugin_list:
                                plugin.fn(request)

        except Exception as e:
            exc_type,exc_obj,exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error(f"{e} at {fname}:{exc_tb.tb_lineno}")

if __name__ == "__main__":
    parsed_args = parse_args(sys.argv[1:])
    main(parsed_args)
