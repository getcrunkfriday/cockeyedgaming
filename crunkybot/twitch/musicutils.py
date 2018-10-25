from __future__ import unicode_literals
from sound_downloader.downloader import YoutubeAudioDownloader

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import youtube_dl
import json
import sqlite3 as sql
import time
import re
import os
import crunkycfg as cfg
import subprocess
from os import listdir
from os.path import isfile, join
from dbutils import *

# Youtube-dl params
youtube_dl_proc="youtube-dl -x --no-progress --audio-format mp3 --prefer-ffmpeg"
youtube_re_str="http(s)?://www\.youtube\.com/watch\?v=([-A-Za-z0-9_])+"
youtube_re=re.compile(youtube_re_str)
dl_location=cfg.MUSIC_DOWNLOAD_DIR
pl_location=cfg.MUSIC_PLAYLIST
db_location=cfg.MUSIC_DB

info_options={'outtmpl': '%(id)s %(title)s', 'ignoreerrors':True}
dl_vid_options  ={
    'outtmpl': dl_location+"/%(id)s.%(ext)s", 
    'ignoreerrors':True, 
    'prefer_ffmpeg':True, 
    'format': 'bestaudio/best',
    'noplaylist': True, 
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3'
    }]
}
dl_playlist_options = {
    'outtmpl': dl_location+"/%(id)s.%(ext)s", 
    'ignoreerrors':True, 
    'prefer_ffmpeg':True, 
    'format': 'bestaudio/best', 
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3'
    }]
}

def get_vid_info(vid):
    with youtube_dl.YoutubeDL(info_options) as ydl:
        result=ydl.extract_info(vid,download=False)
        if result['duration'] > 420:
            return False
        id_tuple=ydl.prepare_filename(result)
        vidid=id_tuple.split()[0]
        title=" ".join(id_tuple.split()[1:])
        return (vidid,title)
    return False

def get_playlist_info(playlist):
    with youtube_dl.YoutubeDL(info_options) as ydl:
        result=ydl.extract_info(playlist,download=False)
        songs=[]
        for song in result['entries']:
            if song and song['duration'] <= 420:
                id_tuple=ydl.prepare_filename(song)
                vidid=id_tuple.split()[0]
                title=" ".join(id_tuple.split()[1:])
                songs.append((vidid,title))
        return songs
                

def download_vid(vid):
    with youtube_dl.YoutubeDL(dl_vid_options) as ydl:
        ydl.download([vid])
    return True

def download_playlist(pl,dl_location=dl_location):
    with youtube_dl.YoutubeDL(dl_playlist_options) as ydl:
        ydl.download([pl])
    return True

def youtube_search(search_str):
    def youtube_search(vid):
        print vid
        youtube = build(cfg.YOUTUBE_API_SERVICE_NAME, cfg.YOUTUBE_API_VERSION,
                    developerKey=cfg.DEVELOPER_KEY)

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
        res=youtube_search(search_str)
        first_return=""
        if res:
            print res['items']
            if res['items']:
                first_return=res['items'][0]['id']['videoId']
        return first_return
    except HttpError as e:
        print "Error",e.resp.status,e.content
        return None

if __name__ == "__main__":
    import sys
    db=MusicDB(db_location)
    if len(sys.argv) >= 2:
        print sys.argv
        if sys.argv[1] == "addplaylist":
            # Arg 1: addplaylist
            # Arg 2: [youtube_playlist]
            # Arg 3: playlist name
            playlist_url=sys.argv[2]
            playlist_name=" ".join(sys.argv[3:])
            playlist=Playlist(playlist_name,"cockeyedgaming")
            res,rid=db.add_playlist(playlist)
            if res:
                playlist.set_id(rid)
                print playlist_url,str(playlist_url)
                songs=get_playlist_info(str(playlist_url))
                for song in songs:
                    # Creates a DB Track for each song in a playlist.
                    print "Adding to playlist...",rid
                    track=Track(rid,song[0],song[1],dl_location+"/"+song[0]+".mp3","cockeyedgaming",time.strftime("%Y-%m-%d"))
                    res,track_rid=db.add_track_to_playlist(track)
                    print "Track",track_rid,track.title_,"added to DB (",track.file_location_,")"
                download_playlist(playlist_url)
        elif sys.argv[1] == "removeplaylist":
            # arg 1: removeplaylist
            # arg2: playlist_id
            db.remove_playlist(int(sys.argv[2]))
        elif sys.argv[1] == "list":
            playlists=db.get_playlists()
            for p in playlists:
                print p.rid_,":",p.playlist_name_
