from __future__ import unicode_literals
# from sound_downloader.downloader import YoutubeAudioDownloader
import logging
import os
from typing import Tuple, Optional, List

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import youtube_dl
import time
import re

import crunkybot.twitch.config as cfg
from crunkybot.twitch.config import MUSIC_DOWNLOAD_DIR, \
    MUSIC_PLAYLIST, YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, \
    YOUTUBE_DEVELOPER_KEY, TWITCH_CHAN

logger = logging.getLogger(__name__)


# Youtube-dl params
from src.crunkybot.twitch.dbutils import MusicDB, Track, Playlist

CONFIG = cfg.ConfigLoader.CONFIG
youtube_dl_proc = "youtube-dl -x --no-progress --audio-format mp3 --prefer-ffmpeg"
youtube_re_str = "http(s)?://www\.youtube\.com/watch\?v=([-A-Za-z0-9_])+"
youtube_re = re.compile(youtube_re_str)
dl_location = CONFIG.get(MUSIC_DOWNLOAD_DIR, "/tmp")
pl_location = CONFIG.get(MUSIC_PLAYLIST, "/tmp")
# db_location=cfg.MUSIC_DB
db_location = "/tmp/dbs/test_db.db"
playlist_tag = "[CrunkyBot]"

info_options = {'outtmpl': '%(id)s %(title)s', 'ignoreerrors': True}
dl_vid_options = {
    'outtmpl': dl_location + "/%(id)s.%(ext)s",
    'ignoreerrors': True,
    'prefer_ffmpeg': True,
    'format': 'bestaudio/best',
    'noplaylist': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3'
    }]
}
dl_playlist_options = {
    'outtmpl': dl_location + "/%(id)s.%(ext)s",
    'ignoreerrors': True,
    'prefer_ffmpeg': True,
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3'
    }]
}


def get_vid_info(vid: str) -> Optional[Tuple[str, str]]:
    with youtube_dl.YoutubeDL(info_options) as ydl:
        result = ydl.extract_info(vid, download=False)
        if result['duration'] > 420:
            return None
        id_tuple = ydl.prepare_filename(result)
        vidid = id_tuple.split()[0]
        title = " ".join(id_tuple.split()[1:])
        return vidid, title


def get_playlist_info(playlist: str) -> List[Tuple[str, str]]:
    with youtube_dl.YoutubeDL(info_options) as ydl:
        result = ydl.extract_info(playlist, download=False)
        songs = []
        for song in result['entries']:
            if song and song['duration'] <= 420:
                id_tuple = ydl.prepare_filename(song)
                vidid = id_tuple.split()[0]
                title = " ".join(id_tuple.split()[1:])
                songs.append((vidid, title))
        return songs


def download_vid(vid: str) -> bool:
    with youtube_dl.YoutubeDL(dl_vid_options) as ydl:
        ydl.download([vid])
    return True


def download_playlist(pl: str) -> bool:
    with youtube_dl.YoutubeDL(dl_playlist_options) as ydl:
        ydl.download([pl])
    return True


def get_channel_id(channel_name: str) -> str:
    youtube = build(
        CONFIG[YOUTUBE_API_SERVICE_NAME],
        CONFIG[YOUTUBE_API_VERSION],
        developerKey=CONFIG[YOUTUBE_DEVELOPER_KEY]
    )
    channel_response = youtube.channels().list(
        part="id",
        forUsername=channel_name
    ).execute()
    return channel_response['items'][0]['id']


def get_playlists_for_channel_id(channel_id: str) -> List[Tuple[str, str]]:
    youtube = build(
        CONFIG[YOUTUBE_API_SERVICE_NAME],
        CONFIG[YOUTUBE_API_VERSION],
        developerKey=CONFIG[YOUTUBE_DEVELOPER_KEY]
    )
    playlist_response = youtube.playlists()
    req = playlist_response.list(
        part="snippet",
        maxResults=50,
        channelId=channel_id
    )
    playlists = []
    while req:
        res = req.execute()
        for i in res['items']:
            i['snippet'].keys()
            title = i['snippet']['title']
            if playlist_tag in title:
                playlists.append((i['id'], title))
        req = playlist_response.list_next(req, res)
    return playlists


def get_songs_for_playlist(playlist: str) -> List[Tuple[str, str]]:
    youtube = build(
        CONFIG[YOUTUBE_API_SERVICE_NAME],
        CONFIG[YOUTUBE_API_VERSION],
        developerKey=CONFIG[YOUTUBE_DEVELOPER_KEY]
    )
    playlist_item_response = youtube.playlistItems().list(
        part="contentDetails,status,snippet",
        playlistId=playlist,
        maxResults=50
    )
    playlist_videos = []
    while playlist_item_response:
        playlist_response_ex = playlist_item_response.execute()
        for entry in playlist_response_ex.get("items", []):
            playlist_videos.append((entry["contentDetails"]["videoId"], entry['snippet']["title"]))
        playlist_item_response = youtube.playlistItems().list_next(playlist_item_response, playlist_response_ex)
    return playlist_videos


def sync_playlists_to_db(
    db: MusicDB,
    channel_id: str,
    playlists: List[Tuple[str, str]] = []
) -> Tuple[List[Tuple[str, str]], List[Track], List[Track]]:
    if len(playlists) == 0:
        playlists = get_playlists_for_channel_id(channel_id)
    playlists_to_add = []
    tracks_to_add = []
    tracks_to_remove = []
    for playlist in playlists:
        yt_tracks = get_songs_for_playlist(playlist[0])
        db_playlist = db.get_playlist_by_youtube_id(playlist[0])
        if db_playlist:
            playlist_tracks = db.get_tracks(db_playlist.rid)
            playlist_songs = [t.youtube_id for t in playlist_tracks]
            for ytt in yt_tracks:
                if ytt[0] not in playlist_songs:
                    # Check if track exists first, before downloading.
                    # download_vid("https://www.youtube.com/watch?v="+ytt[0])
                    track = Track(db_playlist.rid, ytt[0], ytt[1], os.path.join(dl_location, f"{ytt[0]}.mp3"),
                                  CONFIG[TWITCH_CHAN], time.strftime("%Y-%m-%d"))
                    # res,track_rid=db.add_track_to_playlist(track)
                    tracks_to_add.append(track)
            for playlist_track in playlist_tracks:
                if playlist_track.youtube_id not in [ytt[0] for ytt in yt_tracks]:
                    # db.remove_track_from_playlist(db_playlist.rid_, playlist_track)
                    # os.remove(playlist_track.file_location_)
                    tracks_to_remove.append(playlist_track)
                    logger.info(f"Track {playlist_track.youtube_id} removed from DB (and file system).")

        else:
            logger.info(f"Playlist {playlist[1]} not found. Downloading...")
            playlists_to_add.append(playlist)
            # download_playlist("https://www.youtube.com/watch?v="+yt_tracks[0][0]+"&list="+playlist[0])
            playlist = Playlist(playlist[1], CONFIG[TWITCH_CHAN], youtube_id=playlist[0])
            res, rid = db.add_playlist(playlist)
            if res:
                playlist.set_id(rid)
                for ytt in yt_tracks:
                    track = Track(rid, ytt[0], ytt[1], dl_location + "/" + ytt[0] + ".mp3", "cockeyedgaming",
                                  time.strftime("%Y-%m-%d"))
                    tracks_to_add.append(track)
                    logger.info(f"Track {track.rid}, {track.title} added to DB ({track.file_location})")
    return playlists_to_add, tracks_to_add, tracks_to_remove


def youtube_search(search_str: str) -> Optional[str]:
    def _youtube_search(vid):
        youtube = build(CONFIG[YOUTUBE_API_SERVICE_NAME], CONFIG[YOUTUBE_API_VERSION],
                        developerKey=CONFIG[YOUTUBE_DEVELOPER_KEY])

        # Call the search.list method to retrieve results matching the specified
        # query term.
        search_response = youtube.search().list(
            part="snippet",
            maxResults=5,
            q=vid,
            type="video",
            videoCategoryId="10"
        ).execute()
        return search_response

    try:
        res = _youtube_search(search_str)
        first_return = ""
        if res:
            if res['items']:
                first_return = res['items'][0]['id']['videoId']
        return first_return
    except HttpError as e:
        logger.error(f"Error {e.resp.status} {e.content}")
        return None


if __name__ == "__main__":
    import sys

    db = MusicDB(db_location)
    if len(sys.argv) >= 2:

        if sys.argv[1] == "test":
            playlists = get_playlists_for_channel_id("UCAUBes2LJsXAYRSmq7zwF8g")
            # playlists.append(("PLmPSvm77oH5uXayUShAa2CXy99GiGzSPS", "Test Playlist 1"))
            for playlist in playlists:
                print(playlist[1])
            sync_playlists_to_db(db, "UCAUBes2LJsXAYRSmq7zwF8g", [playlists[0]])
        if sys.argv[1] == "addplaylist":
            # Arg 1: addplaylist
            # Arg 2: [youtube_playlist]
            # Arg 3: playlist name
            playlist_url = sys.argv[2]
            playlist_name = " ".join(sys.argv[3:])
            playlist = Playlist(playlist_name, "cockeyedgaming", "PLmPSvm77oH5sCBI2t1IE9pyBcah1LeHY7")
            res, rid = db.add_playlist(playlist)
            if res:
                playlist.set_id(rid)
                songs = get_playlist_info(str(playlist_url))
                for song in songs:
                    # Creates a DB Track for each song in a playlist.
                    logger.info("Adding to playlist {rid}")
                    track = Track(rid, song[0], song[1], dl_location + "/" + song[0] + ".mp3", "cockeyedgaming",
                                  time.strftime("%Y-%m-%d"))
                    res, track_rid = db.add_track_to_playlist(track)
                    logger.info(f"Track {track_rid}, {track.title}, added to DB ({track.file_location})")
                download_playlist(playlist_url)
        elif sys.argv[1] == "removeplaylist":
            # arg 1: removeplaylist
            # arg2: playlist_id
            db.remove_playlist(int(sys.argv[2]))
        elif sys.argv[1] == "list":
            playlists = db.get_playlists()
            for p in playlists:
                logger.info(f"{p.rid} : {p.playlist_name}")
        elif sys.argv[1] == "listvideos":
            playlist_id = sys.argv[2]
            videos = get_songs_for_playlist(playlist_id)
            for video in videos:
                logger.info(video)
            logger.info(len(videos))
        elif sys.argv[1] == "addcustomsong":
            playlist = Playlist("Metal", "cockeyedgaming")
            res, rid = db.add_playlist(playlist)
            track = Track(rid, "None", "Ash Plissken - I'm a Dwarf", dl_location + "/Ash_Plissken_-_Im_a_Dwarf.mp3",
                          "cockeyedgaming", time.strftime("%Y-%m-%d"))
            _, track_rid = db.add_track_to_playlist(track)
            logger.info(f"Track {track_rid}, {track.title} added to DB({track.file_location})")
        elif sys.argv[1] == "ppr":
            db.purge_playlist_requests()
