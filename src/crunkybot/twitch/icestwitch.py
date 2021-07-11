import sqlite3
import sys
import unicodedata
from random import shuffle

# This file controls ices playlists.
# Copy me to /usr/local/etc/modules/

sys.path.append("/home/andrew/Git/cockeyedgaming/crunkybot/twitch")
import dbutils as db
import crunkycfg as cfg

#global playlist,requests,current_track
#global db,con,cur

db_location=cfg.MUSIC_DB
music_db=db.MusicDB(db_location)
tplaylist=[]
trequests=[]
tplaylist_id=[1]
tcurrent_track=""
tuser_added=""

def ices_init():
    global music_db
    tracks=[]
    for pid in tplaylist_id:
        for x in music_db.get_tracks(pid):
            tracks.append(x)
    tplaylist=[(track.title_,track.file_location_) for track in tracks]
    shuffle(tplaylist)
    #for t in tplaylist:
    #    print t
    return 1

def ices_get_metadata():
    global tcurrent_track
    str_curr_track=None
    try:
        str_curr_track=str(tcurrent_track)
    except:
        try:
            str_curr_track=unicodedata.normalize('NFKD', tcurrent_track).encode('ascii','ignore')
        except:
            str_curr_track=None
    with open("current_track.txt","w") as f:
        f.write(str_curr_track)
    return str_curr_track

def ices_shutdown():
    #global db,con,cur
    music_db.purge_requests()
    music_db.close()
    return 1

def ices_get_next():
    global tplaylist
    global tplaylist_id
    global trequests
    global tcurrent_track
    global music_db
    # Check playlist requests.
    new_pl=music_db.pop_playlist_request()
    if new_pl:
        tplaylist=[(track.title_,track.file_location_) for track in new_pl[1]]
        #print tplaylist
        shuffle(tplaylist)
        tplaylist_id=new_pl[0]
    # Check request table.
    requests=music_db.get_track_requests()
    next_track = None
    # If there are any requests:
    if requests:
        for track in requests:
            # Removes the current request from the DB.
            trequests.append((track.title_,track.file_location_,track.user_added_))
    # If I have a request, make that the next track...
    if trequests:
        track=trequests.pop(0)
        tcurrent_track=track[0]+","+track[2]
        next_track = track[1]
    # Otherwise, pick from the playlist.
    elif tplaylist:
        track=tplaylist.pop()
        tcurrent_track=track[0]+",cockeyedgaming"
        next_track = track[1]
    # If the playlist is empty and there are no requests,
    # Shuffle the playlist.
    else:
        print "Reshuffling playlist."
        tracks=[]
        for pid in tplaylist_id:
            for x in music_db.get_tracks(pid):
                tracks.append(x)
        tplaylist=[(track.title_,track.file_location_) for track in tracks]
        shuffle(tplaylist)
        track=tplaylist.pop()
        tcurrent_track=track[0]+",cockeyedgaming"
        next_track = track[1]
    try:
        return str(next_track)
    except:
        track=tplaylist.pop()
        tcurrent_track=track[0]+",cockeyedgaming"
        next_track=track[1]
        return str(next_track)
