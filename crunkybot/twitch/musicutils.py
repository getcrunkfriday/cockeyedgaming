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

# Youtube-dl params
youtube_dl_proc="youtube-dl -x --no-progress --audio-format mp3 --prefer-ffmpeg"
youtube_re_str="http(s)?://www\.youtube\.com/watch\?v=([-A-Za-z0-9_])+"
youtube_re=re.compile(youtube_re_str)
dl_location=cfg.MUSIC_DOWNLOAD_DIR
pl_location=cfg.MUSIC_PLAYLIST
db_location=cfg.MUSIC_DB

ydl=youtube_dl.YoutubeDL({'outtmpl': '%(id)s %(title)s'})

def get_vid_info(vid):
    with ydl:
        result=ydl.extract_info(vid,download=False)
        if result['duration'] > 420:
            return False
        id_tuple=ydl.prepare_filename(result)
        vidid=id_tuple.split()[0]
        title=" ".join(id_tuple.split()[1:])
        return (vidid,title)
    return False

def download_vid(vid,dl_location=dl_location):
    pro = subprocess.call(youtube_dl_proc+" --max-filesize 8m --no-playlist -o '"+dl_location+"/%(id)s.%(ext)s' "+vid,shell=True,preexec_fn=os.setsid)
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

def initialize_db(playlist_files=["/home/andrew/music/playlist.txt"],db_loc=db_location,download_files=False):
    conn = sql.connect(db_loc)
    c=conn.cursor()
    c.execute('''DROP TABLE playlist''')
    c.execute('''DROP TABLE requests''')
    c.execute('''CREATE TABLE playlist
                 (id INTEGER PRIMARY KEY, playlist_id INTEGER, youtube_id TEXT, title TEXT, file_location TEXT, user_added TEXT, date_added DATE, num_plays INT)''' )
    c.execute('''CREATE TABLE requests
                 (id INTEGER PRIMARY KEY, youtube_id TEXT, title TEXT, file_location TEXT, user_added TEXT, date_added DATE)''')
    for playlist_file in playlist_files:
        with open(playlist_file) as f:
            for vid in f.readlines():
                (vidid,title)=get_vid_info(vid)
                result=download_vid(vid)
                if result:
                    print "Inserting:",title
                    sql_str="INSERT INTO playlist(youtube_id,title,file_location,user_added,date_added,num_plays) VALUES (?,?,?,?,?,?)"
                    print "Insert string=",sql_str
                    c.execute(sql_str,(vid,title,dl_location+"/"+vidid+".mp3","cockeyedgaming",time.strftime("%Y-%m-%d"),0))
                    conn.commit()
    conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        #grab_url_info("https://www.youtube.com/watch?v=X_AUmIwWbtc")
        #print download_vid("https://www.youtube.com/watch?v=X_AUmIwWbtc","tmp")
        initialize_db(playlist_files=["/home/andrew/music/playlist1.txt"],download_files=True)
        #get_vid_info("https://www.youtube.com/watch?v=SW-BU6keEUw")
    elif len(sys.argv) == 4:
        if sys.argv[1] == "add":
            conn=sql.connect(db_location)
            c=conn.cursor()
            playlist_id=sys.argv[2]
            vid=sys.argv[3]
            (vidid,title)=get_vid_info(vid)
            result=download_vid(vid)
            if result:
                print "Inserting:",title
                sql_str="INSERT INTO playlist(playlist_id,youtube_id,title,file_location,user_added,date_added,num_plays) VALUES (?,?,?,?,?,?,?)"
                print "Insert string=",sql_str
                c.execute(sql_str,(playlist_id,vid,title,dl_location+"/"+vidid+".mp3","cockeyedgaming",time.strftime("%Y-%m-%d"),0))
                conn.commit()
        elif sys.argv[1] == "addfile":
            playlist_id=sys.argv[2]
            with open(sys.argv[3]) as f:
                lines=f.readlines()
                for line in lines:
                    conn=sql.connect(db_location)
                    c=conn.cursor()
                    vid=line
                    (vidid,title)=get_vid_info(vid)
                    result=download_vid(vid)
                    if result:
                        print "Inserting:",title
                        sql_str="INSERT INTO playlist(playlist_id,youtube_id,title,file_location,user_added,date_added,num_plays) VALUES (??,?,?,?,?,?)"
                        print "Insert string=",sql_str
                        c.execute(sql_str,(playlist_id,vid,title,dl_location+"/"+vidid+".mp3","cockeyedgaming",time.strftime("%Y-%m-%d"),0))
                        conn.commit()