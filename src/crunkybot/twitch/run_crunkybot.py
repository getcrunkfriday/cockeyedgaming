import logging
import sys
import os
import argparse
from crunkybot.twitch.config import ConfigLoader, MUSIC_DB_LOCATION, YOUTUBE_PLAYLIST_CHANNEL

from typing import List, Dict
import threading as thread
from crunkybot.twitch import icescontroller
import crunkybot.twitch.twitch_utils as twitch_utils
import threading


logger = logging.getLogger(__name__)

# Globals for threads.
download_queue = []


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
    parser.add_argument(
        "--sr_enabled",
        action="store_true",
        help="If given, will enable song requests."
    )
    parser.add_argument(
        "--sync_yt",
        action="store_true",
        help="If given, will sync YouTube videos to radio station."
    )
    return parser.parse_args(args)


def check_download_queue() -> None:
    global download_queue
    import sqlite3 as sql
    from src.crunkybot.twitch.musicutils import MusicDB
    from src.crunkybot.twitch.config import ConfigLoader, MUSIC_DB_LOCATION
    from src.crunkybot.twitch.dbutils import Playlist
    import src.crunkybot.twitch.utils as utils

    db_location = ConfigLoader.CONFIG[MUSIC_DB_LOCATION]
    conn = sql.connect(db_location)
    db = MusicDB(db_location)
    while True:
        if download_queue:
            complete_threads = []
            for d in range(len(download_queue)):
                download = download_queue[d]
                if download['request_type'] == 'sr':
                    t = download['thread']
                    if not t.isAlive():
                        logger.info("Download=", download)
                        current_request_user = download['user']
                        current_request_vid = download['vid']
                        current_request_vidid = download['vidid']
                        current_request_title = download['title']
                        logger.info("Adding to download queue...")
                        utils.commit_song_request(
                            conn, current_request_user, current_request_vid, current_request_vidid, current_request_title
                        )
                        complete_threads.append(d)
                if download['request_type'] == 'sync_add_playlist':
                    playlist = Playlist(download['playlist_name'], "cockeyedgaming", youtube_id=download['playlist_id'])
                    res, rid = db.add_playlist(playlist)
                    complete_threads.append(d)
                if download['request_type'] == 'sync_add_tracks':
                    t = download['thread']
                    if not t.isAlive():
                        for t2a in download['tracks']:
                            res, track_rid = db.add_track_to_playlist(t2a)
                        complete_threads.append(d)
                if download['request_type'] == 'sync_remove_tracks':
                    for t2r in download['tracks']:
                        playlist = db.get_playlist_by_id(t2r.playlist_id_)
                        db.remove_track_from_playlist(playlist.rid_, t2r)
                        os.remove(t2r.file_location_)
                    complete_threads.append(d)
            for t in complete_threads:
                try:
                    del download_queue[t]
                except Exception as e:
                    logger.error("Unexpected error checking download queue:", e)
                    continue


def sync_request(username: str = "cockeyedgaming") -> None:
    global download_queue
    import crunkybot.twitch.utils as utils
    from crunkybot.twitch.musicutils import MusicDB, sync_playlists_to_db

    if not utils.is_op(username):
        return

    print("Attempting to sync...")
    db_location = ConfigLoader.CONFIG[MUSIC_DB_LOCATION]
    db = MusicDB(db_location)
    playlists_to_add, tracks_to_add, tracks_to_remove = sync_playlists_to_db(
        db, ConfigLoader.CONFIG[YOUTUBE_PLAYLIST_CHANNEL]
    )
    # Add playlists.
    # for p2a in playlists_to_add:
    #     download_queue.append({
    #         'thread': None,
    #         'request_type': 'sync_add_playlist',
    #         'playlist_id': p2a[0],
    #         'playlist_name': p2a[1]
    #     })
    # Submit downloads for tracks.
    if len(tracks_to_add) > 0:
        download_thread=threading.Thread(
            target=utils.download_song_requests,
            args=[[f"https://www.youtube.com/watch?v={t2a.youtube_id}" for t2a in tracks_to_add]])
        download_thread.start()
        download_queue.append({
            'thread': download_thread,
            'request_type': 'sync_add_tracks',
            'tracks': tracks_to_add
        })

    if len(tracks_to_remove) > 0:
        # Remove tracks from DB
        download_queue.append({
            'thread': None,
            'request_type': 'sync_remove_tracks',
            'tracks': tracks_to_remove
        })


def main(args: argparse.Namespace):
    # Loading the config before any other modules are loaded.
    config: Dict = ConfigLoader(args.config_file).load()
    from crunkybot.twitch.plugins.plugin import PluginLoader, PluginRequest, Plugin

    print(f"Config: {config}")

    playlist_proc = None
    if args.sr_enabled:
        thread.Thread(target=check_download_queue, args=())
        playlistProc = icescontroller.PlaylistProcess()
    if args.sync_yt:
        sync_request()

    plugins: Dict[str, List[Plugin]] = PluginLoader(args.plugin_file).load()
    twitch_sock: twitch_utils.TwitchSocket = twitch_utils.connect(config)
    logger.info(f"Loaded plugins: {plugins}")
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
                    process=playlist_proc
                )
                # Pass command, message to "Plugins"
                if command is not None:
                    for keyword, plugin_list in plugins.items():
                        if command == keyword or keyword == "ANY":
                            for plugin in plugin_list:
                                response = plugin.fn(request)

        except Exception as e:
            exc_type,exc_obj,exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error(f"{e} at {fname}:{exc_tb.tb_lineno}")


if __name__ == "__main__":
    parsed_args = parse_args(sys.argv[1:])
    main(parsed_args)
