import logging
import os
import time
from typing import Dict, Set, Tuple, Optional, List
import re
import requests
import json
import src.crunkybot.twitch.musicutils as musicutils

from crunkybot.twitch.config import ConfigLoader, TWITCH_CHAN, MUSIC_DOWNLOAD_DIR, COMMAND_DB_LOCATION, \
    MUSIC_DB_LOCATION, TWITCH_CHAN_ID
from crunkybot.twitch.dbutils import CommandDB, MusicDB, Command, Shoutout
from crunkybot.twitch.icescontroller import PlaylistProcess
from crunkybot.twitch.musicutils import youtube_re
from crunkybot.twitch.twitch_utils import TwitchSocket, TWITCH_V2_MODERATION_URL, \
    get_twitch_headers, TWITCH_V2_USERS_URL, TWITCH_V2_SUB_URL

logger = logging.getLogger(__name__)


dl_location = ConfigLoader.CONFIG.get(MUSIC_DOWNLOAD_DIR, "")
command_db = CommandDB(ConfigLoader.CONFIG.get(COMMAND_DB_LOCATION, "/tmp/commands.db"))
music_db = MusicDB(ConfigLoader.CONFIG.get(MUSIC_DB_LOCATION, "/tmp/music.db"))

MODERATORS = set([])
FOLLOWERS = set([])
SUBSCRIBERS = set([])


def execute_command(
    sock: TwitchSocket,
    config: Dict,
    username: str,
    message: str,
    command: Dict
) -> Dict:
    action_str = command["action"]
    num_args = int(command["num_args"])
    argument_defs = command["arguments"].split(",")
    # Split message into arguments
    message_split = message.split()
    args = {argument_defs[i]: f"'{message_split[i]}'" for i in range(num_args)}
    for i in range(num_args):
        args[argument_defs[i]] = "'" + message_split[i] + "'"
    if num_args > 0:
        args[argument_defs[num_args-1]] = f"'" + " ".join(message_split[num_args-1:len(message_split)]) + "'"
    args["s"] = "sock"
    args["u"] = "username"
    # Match arguments with action.
    action_regex_str = r"[^%]*%(?P<argname>[-A-Za-z0-9_]+)"
    action_re = re.compile(action_regex_str)
    matches = action_re.findall(action_str)
    for m in matches:
        if m in args:
            action_str = re.sub("%" + m, args[m], action_str, 1)
    ret = {}
    if ((command["permission"] == "MODERATOR" and is_op(username)) or
            (command["permission"] == "OWNER" and username.lower() == config[TWITCH_CHAN]) or
            (command["permission"] == "ALL")):
        logger.info(username.lower() + "," + config[TWITCH_CHAN])
        logger.info("Trying to evaluate command...")
        ret = eval(action_str)
    else:
        logger.info(username.lower() + "," + config[TWITCH_CHAN])
        logger.info(username.lower() == config[TWITCH_CHAN])
        logger.info(username, "does not have permission to execute", command["action"])
    return ret


def remove_chatcomm(
    sock: TwitchSocket,
    command: str
) -> Dict:
    if command[0] == "!":
        command = command[1:]
    command_obj = command_db.get_command(command)
    logger.debug(command_obj)
    if command_obj:
        command_db.remove_command(command_obj)
        chat(sock, "crunkybot", f"{command} successfully removed!")
        return {"command": ("REMOVE", command_obj)}
    return {}


def add_chatcomm(
    sock: TwitchSocket,
    command: str,
    text: str
) -> Dict:
    if command[0] == "!":
        command = command[1:]
    text = text.replace("'", r"\'")
    if not command_db.get_command(command):
        command_obj = Command((command, "CHAT", "ALL", 0, "", f"chat(%s,%u,'{text}')"))
        res = command_db.add_command(command_obj)
        chat(sock, "crunkybot", f"{command} successfully added!")
        return {"command": ("ADD", command_obj)}
    else:
        chat(sock, "crunkybot", f"I already know {command}!")
        return {}


def remove_shoutout(
    sock: TwitchSocket,
    so_user: str
) -> Dict:
    if so_user[0] == "@":
        so_user = so_user[1:]
    shoutout_obj = command_db.get_shoutout(so_user)
    command_obj = command_db.get_command(shoutout_obj["command"])
    if shoutout_obj and command_obj:
        command_db.remove_command(command_obj)
        command_db.remove_shoutout(shoutout_obj)
        chat(sock, "crunkybot", f"Shoutout for {so_user} successfully removed!")
        return {"command": ("REMOVE", command_obj), "shoutout": ("REMOVE", shoutout_obj)}
    return {}


def add_shoutout(
    sock: TwitchSocket,
    command_name: str,
    so_user: str,
    twitch_clip: str,
    chat_text: str
) -> Dict:
    chat_text = chat_text.replace("'",r"\'")
    if command_name[0] == "!":
        command_name=command_name[1:]
    if so_user[0] == "@":
        so_user=so_user[1:]
    if not command_db.get_command(command_name) and not command_db.get_shoutout(so_user):
        shoutout_obj=Shoutout((command_name, so_user, twitch_clip, chat_text))
        shoutout_obj,command_obj=command_db.add_shoutout(shoutout_obj)
        chat(sock, "crunkybot", f"Shoutout for {so_user} successfully added!")
        return {"command": ("ADD", command_obj), "shoutout": ("ADD", shoutout_obj)}
    else:
        chat(sock, "crunkybot", f"I already know {so_user}!... or {command_name}?")
        return {}


def chat(
    sock: TwitchSocket,
    user: str,
    msg: str,
    debug: bool = False
) -> None:
    msg = msg.replace("${username}", user)
    if not debug:
        sock.send("PRIVMSG #{} :{}\r\n".format(ConfigLoader.CONFIG[TWITCH_CHAN], msg.encode('utf-8')))
    else:
        logger.info(msg)


def song_request(twitch_socket, username: str, message: str, download_queue: List):
    import threading

    res = process_song_request(twitch_socket, username, message)
    if res:
        (vidid, title, url) = (res[0], res[1], res[2])
        download_thread=threading.Thread(target=download_song_request, args=[url])
        download_thread.start()
        download_queue.append({
            'thread': download_thread,
            'request_type': 'sr',
            'user': username,
            'vid': url,
            'vidid': vidid,
            'title': title
        })


def process_song_request(
    sock: TwitchSocket,
    user: str,
    message: str
) -> Optional[Tuple[str, str, str]]:
    if not message:
        chat(sock, "crunkybot", "Gotta use a YouTube search or link " + user + ", you n00b!")
        return None
    vid = message.split(" ")[0]
    vid2 = vid
    if "&" in vid:
        vid2 = vid.split("&")[0]
    m = youtube_re.match(vid2)
    if m:
        try:
            res = musicutils.get_vid_info(vid2)
            if res:
                (vidid, title) = (res[0], res[1])
                chat(sock, "crunkybot", f"{title} requested by {user} added to the queue!")
                return vidid, title, vid2
            else:
                chat(sock, "crunkybot", "Video must be < 7 minutes long.")
                return None
        except Exception as e:
            logger.error(f"Exception {e}")
    else:
        res = musicutils.youtube_search(message)
        try:
            res2 = musicutils.get_vid_info(f"https://www.youtube.com/watch?v={res}")
            if res2:
                vidid, title = (res2[0], res2[1])
                chat(sock, "crunkybot", f"{title} requested by {user} added to the queue!")
                return vidid, title, f"https://www.youtube.com/watch?v={res}"
            else:
                chat(sock, "crunkybot", "Video must be < 7 minutes long.")
                return None
        except Exception as e:
            logger.error(f"Exception: {e}")
    return None


def download_song_request(vid: str) -> None:
    try:
        musicutils.download_vid(vid)
    except Exception as e:
        logger.error(f"Soft failure. {e}")


def download_song_requests(vids: List[str]) -> None:
    for vid in vids:
        download_song_request(vid)


def change_playlist(
    sock: TwitchSocket,
    user: str,
    message: str,
) -> None:
    if is_op(user):
        message = message.strip()
        playlist_ids = []
        playlist_name = None
        playlist = None
        try:
            playlist_ids = [int(x) for x in message.split()]
        except:
            playlist_name = message
        if playlist_ids:
            playlists = []
            for playlist_id in playlist_ids:
                # playlists (id INTEGER PRIMARY KEY, playlist_name TEXT, user_added TEXT)
                playlist = music_db.get_playlist_by_id(playlist_id)
                if playlist:
                    playlists.append(playlist)
                else:
                    chat(sock, "crunkybot", f"No playlist with id {playlist_id}")
                    return None
            playlist_mix = ",".join([x.playlist_name for x in playlists])
            chat(sock, "crunkybot", f"Playlist changed to mix of {playlist_mix}")
            music_db.add_playlists_request(playlists)
        else:
            if playlist_name:
                playlist=music_db.get_playlist_by_name(playlist_name)
            music_db.add_playlist_request(playlist)
            chat(sock, "crunkybot", f"Playlist changed to: {playlist.playlist_name}.")


# Download youtube song and add to request list.
def commit_song_request(
    conn,
    user: str,
    vid: str,
    vidid: str,
    title: str
):
    logger.info(f"COMMITTING... {vid} {user}")
    vid = vid.split(" ")[0]
    if "&" in vid:
        vid = vid.split("&")[0]
    m = youtube_re.match(vid)
    if m:
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO requests(youtube_id,title,file_location,user_added,date_added) VALUES(?,?,?,?,?)",
                (vid, title, os.path.join(
                    ConfigLoader.CONFIG[MUSIC_DOWNLOAD_DIR], f"{vidid}.mp3", user, time.strftime("%Y-%m-%d")))
            )
            logger.info('executing')
            conn.commit()
            logger.info('committed')
        except Exception as e:
            logger.error(f"Soft failure. {e}")


def current_song_chat(
    sock: TwitchSocket,
    user: str
):
    cs = current_song()
    if cs is not None:
        chat(sock, "crunkybot", f"Currently playing: {cs}")
    else:
        chat(sock, "crunkybot", "No song is currently playing.")


def current_song() -> Optional[str]:
    if os.path.exists("current_track.txt"):
        with open("current_track.txt") as f:
            s = f.readlines()[0].split(",")
            return f"{s[0]} (requested by: {s[1]})"
    else:
        return None


def skip_song(
    sock: TwitchSocket,
    user: str,
    proc: PlaylistProcess
):
    if is_op(user) or user.lower() == ConfigLoader.CONFIG[TWITCH_CHAN]:
        currsong = current_song()
        if currsong:
            proc.skip()
            chat(sock, user, currsong+" skipped...")


def list_playlists(
    sock: TwitchSocket,
    user: str
) -> None:
    def filter_name(playlist_name):
        return playlist_name.replace('[CrunkyBot]', '')
    if is_op(user) or user.lower() == ConfigLoader.CONFIG[TWITCH_CHAN]:
        playlists = music_db.get_playlists()
        playlists = playlists[:(min(len(playlists), 10))]
        playlist_names = [filter_name(p.playlist_name) for p in playlists]
        playlists_str = ",".join([
            f"{playlists[p].rid}: {playlist_names[p][:(min(len(playlist_names[p]),8))]}" for p in range(len(playlist_names))
        ])
        chat_str = f"Playlists: {playlists_str}"
        chat(sock, user, chat_str)


def fill_user_list(
    socket: TwitchSocket,
    endpoint: str,
    params: Dict,
    result_key: str
) -> Set:
    result = set([])
    with requests.Session() as sess:
        request = sess.get(
            endpoint,
            headers=get_twitch_headers(socket),
            params=params
        )
        response = json.loads(request.text)
        while len(response) > 0 and 'data' in response:
            for user in response["data"]:
                result.add(user[result_key])
            request = sess.get(
                endpoint,
                headers=get_twitch_headers(socket),
                params=params,
                after=response["pagination"]["cursor"]
            )
            response = json.loads(request.text)
    return result


def fill_user_lists(socket: TwitchSocket):
    MODERATORS.update(fill_user_list(
        socket,
        "/".join([TWITCH_V2_MODERATION_URL, "moderators"]),
        {"broadcaster_id": ConfigLoader.CONFIG[TWITCH_CHAN_ID]},
        "user_login"
    ))
    FOLLOWERS.update(fill_user_list(
        socket,
        "/".join([TWITCH_V2_USERS_URL, "follows"]),
        {"to_id": ConfigLoader.CONFIG[TWITCH_CHAN_ID]},
        "from_login"
    ))
    SUBSCRIBERS.update(fill_user_list(
        socket,
        TWITCH_V2_SUB_URL,
        {"broadcaster_id": ConfigLoader.CONFIG[TWITCH_CHAN_ID]},
        "user_login"
    ))


def is_op(user: str) -> bool:
    return user in MODERATORS or user.lower() == ConfigLoader.CONFIG[TWITCH_CHAN]


def is_follower(user: str) -> bool:
    return user.lower() in FOLLOWERS or user.lower() == ConfigLoader.CONFIG[TWITCH_CHAN]


def is_subscriber(user: str) -> bool:
    return user.lower() in SUBSCRIBERS or user.lower() == ConfigLoader.CONFIG[TWITCH_CHAN]